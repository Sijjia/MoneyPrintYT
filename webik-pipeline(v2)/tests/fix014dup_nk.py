"""Убрать единственный повтор тела: scene_014_wm.jpg стоит и на scene_014 (01:19),
и на scene_016 (01:23, «Первый уровень. Верхушка айсберга»). Меняем ВТОРОЕ вхождение
(idx=16) на отдельное тематическое фото (панорама Пхеньяна = видимая верхушка КНДР)."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.wikimedia import WikimediaClient

PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
POR = PROJECT / "assets" / "portraits"
PUB = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
REMOTION = ROOT / "remotion"
QUERIES = ["Pyongyang skyline", "Pyongyang cityscape", "Pyongyang panorama"]
TARGET_IDX = 16
SID = "scene_016"


def main() -> int:
    wm = WikimediaClient()
    img = None
    for i, q in enumerate(QUERIES):
        o = POR / f"pyongyang_{i}.jpg"
        try:
            if wm.search_and_download(q, o) and o.stat().st_size > 8000:
                img = o; print(f"  ✓ '{q}' → {o.name}"); break
        except Exception as e:
            print(f"  ✗ '{q}': {str(e)[:50]}")
    if not img:
        print("нет фото — прерываю"); return 1

    pub = PUB / f"{SID}{img.suffix}"; shutil.copy(img, pub)
    props = REMOTION / f"_pz_{SID}.json"
    props.write_text(json.dumps({"img": f"photos/{SID}{img.suffix}", "dir": "in",
                                 "durationInFrames": int(3.6 * 30)}), encoding="utf-8")
    outp = OUT / f"{SID}_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("рендер упал:", r.stderr[-300:]); return 1
    print(f"  ✓ рендер {outp.name}")

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    c = v3.clips[TARGET_IDX]
    print(f"  цель idx={TARGET_IDX} было: {os.path.basename(c.projectItem.getMediaPath())}")
    c.projectItem.changeMediaPath(str(outp.resolve()), True)
    pymiere.objects.app.project.save()
    print(f"  ✓ swap idx={TARGET_IDX} → {outp.name}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
