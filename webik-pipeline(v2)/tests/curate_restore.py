"""Финальное курирование приколов на V3 (единый проход):
- убрать все приколы, налезающие на ПЛАШКИ ТЕМ (V4) — под названием чисто;
- проредить остальные до ~TARGET, ПРИОРИТЕТ оставить те, что закрывают mid-body
  чёрные дыры (нет файла тела = были на дыре, типа 6:59), потом добрать телесными
  равномерно;
- где убираем прикол НАД ТЕЛОМ (есть файл сцены) — вернуть кадр тела (ffmpeg-трим
  по длине), чтобы НЕ было чёрной дыры; над бывшей дырой — оставить чёрное.
"""
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

P = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
RESTORE = (P / "assets" / "_body_restore").resolve()
TARGET = 12


def body_file(sid):
    num = sid.split("_")[1]
    pz = P / "assets" / "photozoom" / f"scene_{num}_pz.mp4"
    if pz.exists():
        return pz
    for d in ("kenburns", "archive_stock", "photozoom"):
        base = P / "assets" / d
        if base.exists():
            g = sorted(base.glob(f"scene_{num}*"))
            if g:
                return g[0]
    return None


def trim_body(src: Path, dur: float, tag: str):
    RESTORE.mkdir(parents=True, exist_ok=True)
    dst = RESTORE / f"{tag}.mov"
    if dst.exists() and dst.stat().st_size > 5000:
        return dst
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-t", f"{dur:.2f}",
           "-vf", "fps=30,scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,format=yuv422p",
           "-c:v", "dnxhd", "-profile:v", "dnxhr_sq", "-an", str(dst)]
    try:
        subprocess.run(cmd, check=True)
        return dst if dst.exists() and dst.stat().st_size > 5000 else None
    except Exception as e:
        print(f"    trim упал {tag}: {str(e)[:100]}"); return None


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]; v4 = seq.videoTracks[3]
    plaques = [(c.start.seconds, c.end.seconds) for c in v4.clips]

    def on_plaque(a, b):
        return any(a < pb and b > pa for pa, pb in plaques)

    cuts = []  # (start, end, sid, clip, has_body, is_plaque)
    for cl in v3.clips:
        try:
            n = Path(cl.projectItem.getMediaPath()).name
        except Exception:
            n = cl.name
        m = re.match(r"cutaway_(scene_\d+)_", n)
        if m:
            a, b = cl.start.seconds, cl.end.seconds
            cuts.append([a, b, m.group(1), cl, body_file(m.group(1)) is not None, on_plaque(a, b)])
    cuts.sort(key=lambda x: x[0])

    non_plaque = [c for c in cuts if not c[5]]
    over_gap = [c for c in non_plaque if not c[4]]   # закрывают чёрную дыру — приоритет KEEP
    over_body = [c for c in non_plaque if c[4]]

    keep = set(id(c[3]) for c in over_gap)            # все mid-body дыро-фиксы оставляем
    need = max(0, TARGET - len(over_gap))
    if over_body and need:
        keep_i = {round(i * (len(over_body) - 1) / max(1, need - 1)) for i in range(need)} if need > 1 else {0}
        for i, c in enumerate(over_body):
            if i in keep_i:
                keep.add(id(c[3]))
    print(f"приколов {len(cuts)} | на плашках {sum(1 for c in cuts if c[5])} | "
          f"вне плашек {len(non_plaque)} (дыро-фиксы {len(over_gap)}, над телом {len(over_body)})")
    print(f"оставляю ~{len(keep)}")

    # удаляем всё, что НЕ в keep; собираем задания на восстановление тела
    restores = []  # (start, end, sid)
    for a, b, sid, cl, has_body, is_pl in cuts:
        if id(cl) in keep:
            continue
        cl.remove(False, False)
        if has_body:
            restores.append((a, b, sid))
    print(f"удалено {len(cuts) - len(keep)}, восстановить тела: {len(restores)}")

    placed = 0
    for a, b, sid in restores:
        bf = body_file(sid)
        tb = trim_body(bf, b - a, f"{sid}_{int(a)}")
        if tb is None:
            continue
        item = import_media(tb)
        if item is None:
            continue
        v3.overwriteClip(item, time_from_seconds(round(a, 2)))
        placed += 1
    print(f"восстановлено тел: {placed}")

    pymiere.objects.app.project.save()
    clips = sorted([(c.start.seconds, c.end.seconds) for c in v3.clips])
    big = [(clips[i-1][1], clips[i][0]) for i in range(1, len(clips)) if clips[i][0]-clips[i-1][1] > 2.5]
    print(f"\nИТОГ: приколов оставлено ~{len(keep)}, больших дыр в теле: {len(big)}")
    for a, b in big:
        print(f"  дыра {int(a)//60:02d}:{int(a)%60:02d} ({b-a:.1f}с)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
