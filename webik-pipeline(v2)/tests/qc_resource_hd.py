"""HD-перекачка плохих/низкобитрейтных стоков на настоящий 1080p (Pexels/Pixabay) по
better_query (vision-QC) или query манифеста. Игро-специфичные запросы (GTA/San Andreas/
NoPixel/Rockstar/easter egg/...) Pexels НЕ ищет корректно → помечаем под bespoke-графику.
Кладёт в assets/_qcfix (живое медиа НЕ трогает). Пишет _qcfix_hd.json + _hd_todo_graphics.json.
  QC_PROJECT=<path> ../.venv/Scripts/python.exe tests/qc_resource_hd.py
Env: HD_MIN_MBIT (порог «низкий битрейт», деф 3.0), HD_LIMIT (тест: N сцен)."""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.stocks.pexels_videos import PexelsVideosClient
from services.stocks.pixabay import PixabayClient

PROJECT = Path(os.environ.get("QC_PROJECT", ROOT / "projects" /
    "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"))
VS = PROJECT / "assets" / "video_stock"
QCFIX = PROJECT / "assets" / "_qcfix"; QCFIX.mkdir(parents=True, exist_ok=True)
MIN_MBIT = float(os.environ.get("HD_MIN_MBIT", "3.0"))
CARD = {"level_card", "topic_card"}

# игро-специфичное — у стоков этого нет, тянуть бессмысленно → графика
GAME = re.compile(r"\b(gta|grand theft|san andreas|vice city|liberty city|los santos|"
                  r"nopixel|no pixel|rockstar|rp server|roleplay server|easter egg|"
                  r"machinima|cutscene|npc|bigfoot|mount chiliad|jetpack|ratman|"
                  r"trevor|franklin|niko bellic|hot coffee|jolene|cranley)\b", re.I)
# «мусорные» слоты, которые правильнее делать графикой/оставить, а не стоком
SKIP_SLATE = re.compile(r"black screen|thanks for watching|subscribe|like button|"
                        r"leave a comment|goodbye|end screen|end card", re.I)


def _probe(p: Path):
    """→ (width, height, mbit)."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                        "-show_entries", "stream=width,height", "-of", "csv=p=0:s=x", str(p)],
                       capture_output=True, text=True)
    w = h = 0
    try:
        w, h = (int(x) for x in r.stdout.strip().split("x")[:2])
    except Exception:
        pass
    rb = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=bit_rate",
                         "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try:
        mb = float(rb.stdout.strip()) / 1e6
    except Exception:
        mb = 0.0
    return w, h, mb


MIN_H = int(os.environ.get("HD_MIN_H", "1000"))   # целим 1080p; 720p — только если 1080 нигде нет


def fetch_hd(query: str, out: Path) -> str | None:
    """Pexels→Pixabay, целясь в ≥1080p (fallback 720p). → источник или None."""
    best = None  # (h, mb, src, bytes) — запасной 720p, если 1080 не нашли
    tmp = out.with_suffix(".cand.mp4")

    def consider(src_name):
        nonlocal best
        w, h, mb = _probe(tmp)
        if h >= MIN_H:
            tmp.replace(out)
            return f"{src_name} {w}x{h} {mb:.1f}M"
        if h >= 700 and (best is None or h > best[0]):
            best = (h, mb, src_name, tmp.read_bytes())
        return None

    for i in range(4):  # ищем среди нескольких кандидатов 1080p
        try:
            if PexelsVideosClient().search_and_download(query, tmp, index=i,
                                                        min_duration=4, max_duration=25):
                r = consider("pexels")
                if r:
                    return r
        except Exception:
            pass
    try:
        pb = PixabayClient()
        for hit in (pb.search_videos(query, video_type="all") or [])[:3]:
            try:
                pb.download_video(hit, tmp, quality="large")
                r = consider("pixabay")
                if r:
                    return r
            except Exception:
                continue
    except Exception:
        pass
    tmp.unlink(missing_ok=True)
    if best:  # 1080 не нашли — берём лучший 720p
        out.write_bytes(best[3])
        return f"{best[2]} {best[0]}p {best[1]:.1f}M (no1080)"
    return None


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    qc = json.loads((PROJECT / "_media_qc.json").read_text(encoding="utf-8"))
    if isinstance(qc, dict):
        qc = qc.get("results") or list(qc.values())
    qmap = {x["id"]: x for x in qc if isinstance(x, dict) and x.get("id")}

    targets = []
    for s in scenes:
        sid = s["id"]
        if (s.get("visual") or {}).get("type") in CARD:
            continue
        e = man.get(sid, {})
        p = Path(e.get("path", ""))
        kind = e.get("kind", "")
        is_video = kind == "video" or p.suffix.lower() in (".mp4", ".mov")
        verdict = qmap.get(sid, {})
        bad = not verdict.get("ok", True)
        low = False
        if is_video and p.exists():
            _, _, mb = _probe(p)
            low = mb < MIN_MBIT
        if not (bad or low):
            continue
        q = (verdict.get("better_query") or e.get("query") or
             (s.get("voiceover") or "")).strip()
        targets.append((sid, q, "bad" if bad else "low", kind))

    lim = int(os.environ.get("HD_LIMIT", "0"))
    if lim:
        targets = targets[:lim]
    print(f"кандидатов на HD-перекачку: {len(targets)}", flush=True)

    done, gfx, failed = {}, [], []
    for n, (sid, q, why, kind) in enumerate(targets, 1):
        if SKIP_SLATE.search(q):
            gfx.append({"id": sid, "query": q, "reason": "slate/outro"})
            print(f"  [{n}/{len(targets)}] {sid} SLATE → графика/пропуск «{q[:40]}»", flush=True)
            continue
        if GAME.search(q):
            gfx.append({"id": sid, "query": q, "reason": "game-specific"})
            print(f"  [{n}/{len(targets)}] {sid} ИГРА → графика «{q[:40]}»", flush=True)
            continue
        out = QCFIX / f"{sid}.mp4"
        src = fetch_hd(q, out)
        if src:
            done[sid] = {"path": str(out.resolve()), "source": src, "query": q, "kind": "video"}
            print(f"  [{n}/{len(targets)}] {sid} ✓ {src}  «{q[:38]}»", flush=True)
        else:
            failed.append({"id": sid, "query": q})
            print(f"  [{n}/{len(targets)}] {sid} ✗ HD не нашёл «{q[:38]}»", flush=True)

    (PROJECT / "_qcfix_hd.json").write_text(json.dumps(done, ensure_ascii=False, indent=1), encoding="utf-8")
    (PROJECT / "_hd_todo_graphics.json").write_text(json.dumps(gfx, ensure_ascii=False, indent=1), encoding="utf-8")
    (PROJECT / "_hd_failed.json").write_text(json.dumps(failed, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nИТОГ: HD-перекачано {len(done)}, под графику {len(gfx)}, не нашлось {len(failed)}", flush=True)
    print("→ _qcfix_hd.json / _hd_todo_graphics.json / _hd_failed.json", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
