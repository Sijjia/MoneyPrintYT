"""Лечит лаги воспроизведения cutaway-вставок: перекодирует их H.264 (long-GOP,
тяжёлый на декод при композитинге на V7) в МОНТАЖНЫЙ интра-кодек DNxHR HQ (.mov)
— каждый кадр самостоятельный, Premiere играет влёт даже с фейдом/наложением.

Локально (без перекачки с YouTube) + changeMediaPath (фейды/позиция сохраняются).
"""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "cutaways").resolve()
CUT_TRACK = 6  # V7


def to_dnxhr(src: Path, dst: Path) -> bool:
    """H.264 → DNxHR HQ .mov (интра, монтажный). Без звука, CFR 30, 1080p yuv422."""
    if dst.exists() and dst.stat().st_size > 10000:
        return True
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
        "-vf", "fps=30,format=yuv422p",
        "-c:v", "dnxhd", "-profile:v", "dnxhr_hq", "-an", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True)
        return dst.exists() and dst.stat().st_size > 10000
    except Exception as e:
        print(f"    dnxhr упал: {str(e)[:140]}")
        return False


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v7 = seq.videoTracks[CUT_TRACK]
    n = v7.clips.numItems
    print(f"cutaway-клипов на V7: {n}")
    relinked = 0
    for i in range(n):
        clip = v7.clips[i]
        try:
            cur = Path(clip.projectItem.getMediaPath())
        except Exception:
            print(f"  [{i}] нет media path — пропуск"); continue
        if cur.suffix.lower() == ".mov":
            print(f"  [{i}] уже .mov — пропуск"); relinked += 1; continue
        mov = OUT / (cur.stem + ".mov")
        print(f"  [{i}] {cur.name} → {mov.name}")
        if not to_dnxhr(cur, mov):
            continue
        try:
            clip.projectItem.changeMediaPath(str(mov.resolve()), True)
            relinked += 1
        except Exception as e:
            print(f"    relink упал: {str(e)[:120]}")
    pymiere.objects.app.project.save()
    print(f"перекодировано+перелинковано {relinked}/{n} в DNxHR, сохранено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
