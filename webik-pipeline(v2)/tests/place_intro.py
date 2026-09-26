"""Кинематографичное интро: рендер IcebergIntro (Reddit-тема: айсберг+ныряющая камера+4 уровня+
всплывающие имена сабреддитов+дрейф частиц) и overwrite на V3 поверх сцен 001-004. Premiere открыт."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

P = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
REMOTION = ROOT / "remotion"
GFX = P / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
MANIFEST = P / "assets" / "images" / "manifest.json"
FPS = 30
END = 20.30   # конец сцены 004 (конец интро-нарратива), начало с 0.0

TAGS = ["r/nosleep", "Эффект Манделы", "This Man", "Backrooms", "Cicada 3301", "r/A858",
        "11B-X-1371", "Blue Whale", "«Момо»", "9MOTHER9HORSE9EYES9", "Lake City Quiet Pills",
        "Swamps of Dagobah"]


def main() -> int:
    frames = round(END * FPS)
    props = {"title": "АЙСБЕРГ", "sub": "REDDIT", "accent": "#ff4500", "tags": TAGS,
             "durationInFrames": frames}
    pf = REMOTION / "_intro_reddit.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / "intro_reddit.mp4"
    if out.exists():
        out.unlink()
    print(f"рендер IcebergIntro {END:.1f}с ({frames}f)…", flush=True)
    r = subprocess.run(f'npx remotion render IcebergIntro "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 80000):
        print(f"✗ рендер упал: {r.stderr[-500:]}"); return 1

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    item = import_media(out.resolve())
    if item is None:
        print("✗ import"); return 1
    v3.overwriteClip(item, time_from_seconds(0.0))

    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    for n in (1, 2, 3, 4):
        man[f"scene_{n:03d}"] = {"path": str(out.resolve()), "query": "intro: IcebergIntro Reddit",
                                 "kind": "video", "source": "gfx-intro"}
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print(f"✓ интро уложено на V3 0:00–{int(END//60)}:{int(END%60):02d} ({frames}f), сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
