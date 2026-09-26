"""Укладывает 11 клипов футажа финала (scene_NNN_out.mp4) поверх графика-монтажа: overwrite на V3
через ExtendScript (без import_media-зависания). Финал 226-237 → разные тематические вставки."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

P = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
VS = P / "assets" / "video_stock"
MAN = P / "assets" / "images" / "manifest.json"

STARTS = [(226, 1454.28), (228, 1469.63), (229, 1472.61), (230, 1477.19), (231, 1482.84),
          (232, 1489.28), (233, 1496.20), (234, 1500.10), (235, 1504.10), (236, 1510.74), (237, 1516.44)]


def main() -> int:
    import json
    man = json.loads(MAN.read_text(encoding="utf-8"))
    for n, st in STARTS:
        p = VS / f"scene_{n:03d}_out.mp4"
        if not p.exists():
            print("MISS", n, flush=True); continue
        path = str(p.resolve()).replace("\\", "/")
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("scene_{n:03d}_out")>=0){{item=root.children[i];break;}}}}'
              'if(!item) return "NOITEM";'
              'var tr=proj.activeSequence.videoTracks[2];'
              f'tr.overwriteClip(item, {st});return "OK";}})()')
        try:
            r = pymiere.core.eval_script(js)
        except Exception as e:
            r = "ERR:" + str(e).splitlines()[-1][:40]
        if r == "OK":
            man[f"scene_{n:03d}"] = {"path": str(p.resolve()), "query": "outro: cinematic footage",
                                     "kind": "video", "source": "pexels-video"}
        print(f"scene_{n:03d}", r, flush=True)
    # cleanup tiny + save
    cj = ('(function(){var t=app.project.activeSequence.videoTracks[2],n=0;'
          'for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15){c.remove(false,false);n++;}}'
          'app.project.save();return "tiny="+n;})()')
    print("CLEAN", pymiere.core.eval_script(cj), flush=True)
    MAN.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print("MANIFEST saved", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
