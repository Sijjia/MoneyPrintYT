"""EN-вставки: переиспользуем готовые cut_scene_XXX.mp4 из RU/_uniq, кладём на V8 по EN-таймингам.
Уникальные имена cuten_ (обход кэша bin)."""
import json, shutil, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
RU = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
EN = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu_EN"
UNIQ = EN / "assets" / "_uniq"; UNIQ.mkdir(parents=True, exist_ok=True)


def main() -> int:
    al = json.loads((EN / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    cuts = sorted((RU / "assets" / "_uniq").glob("cut_scene_*.mp4"))
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    v8 = pymiere.objects.app.project.activeSequence.videoTracks[7]
    placed = 0
    for f in cuts:
        sid = f.stem.replace("cut_", "")
        if sid not in al: continue
        u = UNIQ / f"cuten_{sid}.mp4"
        if not (u.exists() and u.stat().st_size == f.stat().st_size): shutil.copy(f, u)
        it = import_media(u)
        if it is None: continue
        v8.overwriteClip(it, time_from_seconds(round(al[sid]["start"], 2))); placed += 1
        print(f"  ✓ {sid} @{al[sid]['start']:.1f}", flush=True)
    before = (EN / "project_template.prproj").stat().st_mtime
    pymiere.objects.app.project.save(); time.sleep(1.5)
    print(f"\nвставок→V8: {placed}/{len(cuts)} | save {'OK' if (EN/'project_template.prproj').stat().st_mtime>before else 'NO'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
