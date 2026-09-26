"""Сорсинг медиа «Айсберг DreamWorks» по media_plan_dw.json.
movie  → yt-dlp (android+POT) кадр из мультфильма + апскейл 360p→1080p → video_stock/scene_XXX.mp4
archive→ реальное фото (Wikimedia/Wikipedia) → images/scene_XXX.jpg
stock  → Pexels видео → video_stock/scene_XXX.mp4
Пишет assets/images/manifest.json {sid:{path,query,kind,source}}. Резюмируемо (готовое пропускает).
ТРЕБУЕТ запущенный POT-сервер (tools/bgutil.../server, node build/main.js:4416)."""
import hashlib, json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.stocks.wikimedia import WikimediaClient
from services.stocks.wikipedia_photo import WikipediaPhotoClient
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
VID = PROJECT / "assets" / "video_stock"
IMG = PROJECT / "assets" / "images"
YTDLP = [str(ROOT.parent / "webik-pipeline" / ".venv" / "Scripts" / "python.exe"), "-m", "yt_dlp"]
YT_ARGS = ["--no-warnings", "--extractor-args", "youtube:player_client=android"]
for d in (VID, IMG):
    d.mkdir(parents=True, exist_ok=True)


def md5f(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None


def fetch_movie(query, out_mp4, idx, tmp):
    """yt-dlp секцию (варьируем старт против повторов) + апскейл до 1080p."""
    start = 6 + (idx % 6) * 8
    raw = tmp / f"raw_{out_mp4.stem}.mp4"
    # качаем ДЛИННЕЕ (24с) — чтобы клип покрывал даже длинные слоты без зацикливания
    cmd = YTDLP + YT_ARGS + ["--download-sections", f"*{start}-{start+24}",
          "--force-keyframes-at-cuts", "-o", str(raw), f"ytsearch1:{query}"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
    if not raw.exists() or raw.stat().st_size < 20000:
        # запасной старт
        raw2 = tmp / f"raw2_{out_mp4.stem}.mp4"
        cmd = YTDLP + YT_ARGS + ["--download-sections", "*3-27", "--force-keyframes-at-cuts",
              "-o", str(raw2), f"ytsearch1:{query}"]
        subprocess.run(cmd, capture_output=True, text=True, timeout=150)
        raw = raw2 if raw2.exists() and raw2.stat().st_size > 20000 else None
    if not raw:
        return False
    # апскейл 360p → 1080p (lanczos + лёгкий шарп). СПИСОК, не shell — кириллица в пути ломает cmd.exe.
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(raw),
         "-vf", "scale=1920:1080:flags=lanczos,unsharp=5:5:0.5:5:5:0.0",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "20", "-an", str(out_mp4)],
        capture_output=True, text=True)
    return out_mp4.exists() and out_mp4.stat().st_size > 20000


def main() -> int:
    plan = json.loads((PROJECT / "media_plan_dw.json").read_text(encoding="utf-8"))
    scenes = [s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]]
    order = {s["id"]: i for i, s in enumerate(scenes)}
    wm = WikimediaClient(); wp = WikipediaPhotoClient(); px = PexelsVideosClient()
    tmp = Path(tempfile.mkdtemp())
    man = json.loads((IMG / "manifest.json").read_text(encoding="utf-8")) if (IMG / "manifest.json").exists() else {}
    stats = {"movie": 0, "archive": 0, "stock": 0, "fail": 0}

    items = sorted(plan.items(), key=lambda kv: order.get(kv[0], 9999))
    for k, (sid, p) in enumerate(items):
        if sid in man:  # уже готово
            continue
        bucket = p.get("bucket"); q = p.get("query", ""); fb = p.get("fallback", "")
        try:
            if bucket in ("game", "movie"):
                out = VID / f"{sid}.mp4"
                ok = fetch_movie(q, out, k, tmp) or (fb and fetch_movie(fb, out, k + 3, tmp))
                if ok:
                    man[sid] = {"path": str(out), "query": q, "kind": "video", "source": "youtube-dw"}
                    stats["movie"] += 1; print(f"  ✓M {sid} «{q[:40]}»")
                else:
                    stats["fail"] += 1; print(f"  ✗ {sid} movie: не скачалось «{q[:40]}»")
            elif bucket == "archive":
                out = IMG / f"{sid}.jpg"
                got = False
                for query in (q, fb):
                    if not query: continue
                    try:
                        if wm.search_and_download(query, out) and out.stat().st_size > 6000:
                            got = True; break
                    except Exception: pass
                if not got and q:
                    try:
                        if wp.download_photo(q.split(" 19")[0].split(" 20")[0].strip(), out) and out.stat().st_size > 6000:
                            got = True
                    except Exception: pass
                if got:
                    man[sid] = {"path": str(out), "query": q, "kind": "image", "source": "wikimedia"}
                    stats["archive"] += 1; print(f"  ✓A {sid} «{q[:40]}»")
                else:
                    stats["fail"] += 1; print(f"  ✗ {sid} archive: «{q[:40]}»")
            else:  # stock
                out = VID / f"{sid}.mp4"
                got = False
                for query in (q, fb, "old film reel dark"):
                    if not query: continue
                    try:
                        if px.search_and_download(query, out, index=(k % 3)) and out.stat().st_size > 20000:
                            got = True; break
                    except Exception: pass
                if got:
                    man[sid] = {"path": str(out), "query": q, "kind": "video", "source": "pexels-video"}
                    stats["stock"] += 1; print(f"  ✓S {sid} «{q[:40]}»")
                else:
                    stats["fail"] += 1; print(f"  ✗ {sid} stock: «{q[:40]}»")
        except Exception as e:
            stats["fail"] += 1; print(f"  ✗ {sid} [{bucket}]: {str(e)[:60]}")
        if (k + 1) % 15 == 0:
            (IMG / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
            print(f"  ...чекпойнт {k+1}/{len(items)} | {stats}")

    (IMG / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nИТОГ: {stats} | манифест {len(man)} записей")
    return 0


if __name__ == "__main__":
    sys.exit(main())
