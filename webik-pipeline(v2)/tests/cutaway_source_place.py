"""Качает cutaway-клипы (кино/мульт/мем/гифка) с YouTube по запросам режиссёра,
нормализует в 1920x1080 (размытый фон-заливка, без обрезки лиц, БЕЗ звука),
ставит full-frame на V7 в выбранное время. Голос A1 продолжает играть.

Надёжная качалка: search → select → ПОЛНОЕ скачивание (download_full_video) →
trim. Секционную качалку (download_ranges) НЕ используем — она на части видео
отдаёт битый огрызок и ffmpeg trim падает.

Демо: читает <project>/cutaways.json (от cutaway_director.py).
Идемпотентно по assets/cutaways/<scene_id>.mp4 (кэш).
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.stocks.youtube_search import search_candidates, select_clip
from services.stocks.youtube_clipper import download_full_video, trim_clip
from services.premiere_template.timeline_ops import import_media

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "cutaways").resolve()
CACHE = (PROJECT / "assets" / "_cutaway_cache").resolve()
CUT_TRACK = 6  # V7 (свободна, над телом; режиссёр обходил графику V8)
FFMPEG = "ffmpeg"


def fetch_robust(query: str, dur: float, tag: str):
    """search → select → полное скачивание → trim. Возвращает Path сырого клипа."""
    cands = search_candidates(query, n=6)
    if not cands:
        print("    ytsearch пусто"); return None
    sel = select_clip(query, cands, want_sec=dur + 1.0, fetch_details=False)
    if not sel:
        print("    select пусто"); return None
    print(f"    выбран: {sel['title'][:50]} [{sel['clip_start']:.1f}-{sel['clip_end']:.1f}]")
    full = download_full_video(sel["url"], CACHE)
    if full is None:
        print("    полное скачивание не вышло"); return None
    raw = CACHE / f"{tag}_trim.mp4"
    if raw.exists():
        raw.unlink()
    return trim_clip(full, sel["clip_start"], sel["clip_end"], raw)


def normalize(src: Path, dst: Path, dur: float) -> bool:
    """Full-frame 1920x1080: размытый фон + вписанный фронт по центру, без звука."""
    if dst.exists() and dst.stat().st_size > 5000:
        return True
    vf = (
        "[0:v]split=2[bg][fg];"
        "[bg]scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,boxblur=24:2,eq=brightness=-0.06[bgb];"
        "[fg]scale=1920:1080:force_original_aspect_ratio=decrease[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv420p[v]"
    )
    cmd = [
        FFMPEG, "-y", "-loglevel", "error", "-t", f"{dur:.2f}", "-i", str(src),
        "-filter_complex", vf, "-map", "[v]", "-an",
        "-r", "30", "-c:v", "libx264", "-crf", "20", "-preset", "fast",
        "-t", f"{dur:.2f}", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True)
        return dst.exists() and dst.stat().st_size > 5000
    except Exception as e:
        print(f"    ffmpeg normalize упал: {str(e)[:140]}")
        return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    cuts = json.loads((PROJECT / "cutaways.json").read_text(encoding="utf-8"))["cutaways"]
    print(f"вставок к обработке: {len(cuts)}")

    seq = pymiere.objects.app.project.activeSequence
    v7 = seq.videoTracks[CUT_TRACK]
    v8 = seq.videoTracks[7]
    gfx = [(c.start.seconds, c.end.seconds) for c in v8.clips]

    ready = []
    for i, c in enumerate(cuts, 1):
        sid = c["scene_id"]; q = c.get("yt_query", ""); dur = float(c.get("duration_sec", 2.0))
        dst = OUT / f"cutaway_{sid}.mp4"
        print(f"\n[{i}/{len(cuts)}] {sid} @ {c['abs_start']}s · {c['type']} · '{q}'")
        if not dst.exists():
            raw = fetch_robust(q, dur, f"cutaway_{sid}")
            if raw is None or not Path(raw).exists():
                print("    не скачалось — пропуск"); continue
            if not normalize(Path(raw), dst, dur):
                continue
        else:
            print("    кэш есть")
        c["clip_path"] = str(dst)
        ready.append(c)

    print(f"\n=== расстановка {len(ready)} на V7 ===")
    placed = 0
    for c in ready:
        at = float(c["abs_start"])
        if any(gs < at + c["duration_sec"] and ge > at for gs, ge in gfx):
            print(f"    ! {c['scene_id']} @ {at}s пересекает графику V8 (ставлю под ней)")
        item = import_media(Path(c["clip_path"]))
        if item is None:
            print(f"    import упал: {c['clip_path']}"); continue
        try:
            v7.overwriteClip(item, time_from_seconds(round(at, 2)))
            placed += 1
            print(f"    ✓ {c['scene_id']} @ {at}s")
        except Exception as e:
            print(f"    overwrite упал: {str(e)[:120]}")
    pymiere.objects.app.project.save()
    print(f"\nПОСТАВЛЕНО {placed}/{len(cuts)} cutaway на V7, проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
