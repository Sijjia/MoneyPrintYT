"""Рендер bespoke кино-сцен «Айсберг эволюции» (cine_scenes.json) в assets/cine/*.mov
(ProRes 4444, полноэкранные). Длина = props.durationInFrames (dur*30)."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.overlays.render_bridge import render_overlays

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
OUT = PROJECT / "assets" / "cine"


def main() -> int:
    scenes = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))["scenes"]
    ovs = []
    for s in scenes:
        props = dict(s.get("props", {}))
        props["durationInFrames"] = int(round(s["dur"] * 30))
        ovs.append({"id": s["id"], "composition": s["composition"],
                    "type": s.get("type", "cine"), "props": props})
    print(f"рендерю {len(ovs)} кино-сцен → {OUT}")
    done = render_overlays(ovs, OUT, overwrite=False)
    print(f"готово: {len(done)}/{len(ovs)}")
    for d in done:
        print("  ", d["id"], "→", Path(d["file"]).name)
    return 0 if len(done) == len(ovs) else 1


if __name__ == "__main__":
    sys.exit(main())
