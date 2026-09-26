"""Пересборка медиа двух последних тем (Lake City Quiet Pills 211-217 + Swamps of Dagobah 221):
- РЕАЛЬНЫЕ артефакты (DocuFrame): eulogy-пост, Fark-профиль (откуда имя), Whang!/KYM-разбор;
- убираем повтор EvidenceFrame (214/215/217) → РАЗНЫЙ тематический футаж (Pexels).
Кладём на клип, КОТОРЫЙ СОДЕРЖИТ середину сцены (без off-by-one), overwrite на V3. Premiere открыт."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.stocks.pexels_videos import PexelsVideosClient
from services.premiere_template.timeline_ops import import_media

P = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
REMOTION = ROOT / "remotion"
PUBREAL = REMOTION / "public" / "real"; PUBREAL.mkdir(parents=True, exist_ok=True)
PHOTOS = P / "assets" / "real_photos"
GFX = P / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
VS = P / "assets" / "video_stock"
CACHE = (P / "assets" / "_pexels_cache").resolve(); CACHE.mkdir(parents=True, exist_ok=True)
MANIFEST = P / "assets" / "images" / "manifest.json"
FPS = 30

DOCU = [   # (sid, image, kicker, title, source, kb)
    ("scene_211", "lcqp_post.jpg", "r/UnresolvedMysteries", "«The end of ReligionOfPeace»", "Reddit · архив", "in"),
    ("scene_213", "lcqp_fark.jpg", "СЛЕД", "Профиль AngelTwo-Six — откуда имя", "Fark", "left"),
    ("scene_221", "whang_clean.jpg", "ДОКУМЕНТИРОВАНО", "Разбор на канале Whang! (2020)", "KnowYourMeme · YouTube", "out"),
]
FOOT = [   # (sid, [queries]) — разный тематический футаж вместо повторного EvidenceFrame
    ("scene_214", ["classified redacted documents dark table", "confidential files folder desk dark", "old archive documents dim"]),
    ("scene_215", ["special forces soldiers silhouette night", "military tactical team dark", "surveillance operations dark room monitors"]),
    ("scene_217", ["deleting files computer screen dark", "server room powering down dark", "empty desk case file dim light"]),
]


def containing_clip(v3, mid):
    best = None
    for c in v3.clips:
        if c.start.seconds - 0.05 <= mid < c.end.seconds + 0.05:
            best = c
    return best or min(v3.clips, key=lambda c: abs(c.start.seconds - mid))


def render_docu(sid, kicker, title, source, frames, kb):
    props = {"imgSrc": f"real/{sid}.jpg", "kicker": kicker, "title": title,
             "source": source, "kenburns": kb, "durationInFrames": frames}
    pf = REMOTION / f"_docu_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_gfx.mp4"
    if out.exists(): out.unlink()
    subprocess.run(f'npx remotion render DocuFrame "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out if (out.exists() and out.stat().st_size > 20000) else None


def loopfill(src, dur, tag):
    d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                              "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip() or 0)
    if d >= dur - 0.3: return src
    dst = CACHE / f"{tag}_loop.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "-1", "-i", str(src),
                    "-t", f"{dur:.2f}", "-c", "copy", str(dst)], check=False)
    return dst if dst.exists() else src


def normalize(src, dst, dur):
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1728:972,scale=1920:1080,"
          "eq=saturation=0.92:contrast=1.05,setsar=1,fps=30,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,dur-0.4):.2f}:d=0.4")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.3f}", "-an", "-vf", vf, "-r", "30",
                        "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    al = json.loads((P / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ga = P / "_gfx_assigns.json"
    assigns = json.loads(ga.read_text(encoding="utf-8")) if ga.exists() else {}
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    ok = 0

    for sid, img, kicker, title, source, kb in DOCU:
        src = PHOTOS / img
        if not src.exists():
            print(f"  ✗ {sid}: нет {img}"); continue
        mid = al[sid]["start"] + 0.3
        clip = containing_clip(v3, mid); t0 = clip.start.seconds
        frames = max(45, round((clip.end.seconds - clip.start.seconds) * FPS))
        shutil.copy2(src, PUBREAL / f"{sid}.jpg")
        out = render_docu(sid, kicker, title, source, frames, kb)
        if not out:
            print(f"  ✗ {sid}: render fail"); continue
        item = import_media(out.resolve())
        if item is None:
            print(f"  ✗ {sid}: import fail"); continue
        v3.overwriteClip(item, time_from_seconds(t0))
        man[sid] = {"path": str(out.resolve()), "query": f"web: {title}", "kind": "video", "source": "docuframe"}
        assigns[sid] = {"id": sid, "component": "DocuFrame", "props": {"title": title}}
        ok += 1; print(f"  ✓ DOCU {sid} «{title}» @ {t0:.1f} ({frames}f)", flush=True)

    px = PexelsVideosClient()
    for sid, queries in FOOT:
        mid = al[sid]["start"] + 0.3
        clip = containing_clip(v3, mid); t0 = clip.start.seconds
        dur = clip.end.seconds - clip.start.seconds
        raw = None
        for qi, q in enumerate(queries):
            try:
                p = px.search_and_download(q, CACHE / f"{sid}_{qi}.mp4", index=0, min_duration=5)
                if p and Path(p).exists() and Path(p).stat().st_size > 10000:
                    raw = Path(p); print(f"  {sid}: pexels «{q}»", flush=True); break
            except Exception as e:
                print(f"  {sid} '{q}': {str(e)[:50]}")
        if raw is None:
            print(f"  ✗ {sid}: нет футажа"); continue
        srcv = loopfill(raw, dur, sid)
        dst = VS / f"{sid}_reb.mp4"
        if dst.exists(): dst.unlink()
        if not normalize(srcv, dst, dur):
            print(f"  ✗ {sid}: normalize fail"); continue
        item = import_media(dst.resolve())
        if item is None:
            print(f"  ✗ {sid}: import fail"); continue
        v3.overwriteClip(item, time_from_seconds(t0))
        man[sid] = {"path": str(dst.resolve()), "query": f"pexels: {queries[0]}", "kind": "video", "source": "pexels-video"}
        assigns.pop(sid, None)   # снять EvidenceFrame-назначение
        ok += 1; print(f"  ✓ FOOT {sid} «{queries[0]}» @ {t0:.1f} ({dur:.1f}с)", flush=True)

    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    ga.write_text(json.dumps(assigns, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print(f"\nГОТОВО: обновлено {ok} сцен в 2 темах; сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
