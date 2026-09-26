"""Укладывает EN-локализованную графику (assets/gfx/{sid}_gfx.mp4) на EN-таймлайн: overwrite на V3
через ExtendScript в клип, содержащий середину сцены. Premiere открыт с EN-проектом."""
import sys, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

EN = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona_EN"
GFX = EN / "assets" / "gfx"
GA = EN / "_gfx_assigns.json"
VALID = {"RedditThread", "HexCipher", "LiminalSpace", "ARGSignal", "EvidenceFrame", "DocuFrame", "NewsAlert"}


def main() -> int:
    assigns = json.loads(GA.read_text(encoding="utf-8"))
    al = json.loads((EN / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    targets = [sid for sid, a in assigns.items() if a.get("component") in VALID and (GFX / f"{sid}_gfx.mp4").exists()]
    print(f"к укладке EN-графики: {len(targets)}", flush=True)
    ok = miss = 0
    for sid in sorted(targets):
        if sid not in al:
            continue
        mid = al[sid]["start"] + 0.3
        f = GFX / f"{sid}_gfx.mp4"
        path = str(f.resolve()).replace("\\", "/")
        cs = pymiere.core.eval_script(
            '(function(){var t=app.project.activeSequence.videoTracks[2];for(var i=0;i<t.clips.numItems;i++){'
            'var c=t.clips[i];if(c.start.seconds-0.05<=%f&&%f<c.end.seconds+0.05)return c.start.seconds.toString();}'
            'return "NA";})()' % (mid, mid))
        if cs == "NA":
            miss += 1; continue
        t0 = float(cs)
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{var nm=root.children[i].name;if(nm.indexOf("{sid}_gfx")>=0){{item=root.children[i];break;}}}}'
              'if(!item)return "NOITEM";'
              f'var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{t0});return "OK";}})()')
        try:
            r = pymiere.core.eval_script(js)
        except Exception as e:
            r = "ERR"
        if r == "OK":
            ok += 1
            if ok % 12 == 0:
                print(f"  ...уложено {ok}", flush=True)
        else:
            miss += 1
    # cleanup tiny + save
    cj = ('(function(){var t=app.project.activeSequence.videoTracks[2],n=0;'
          'for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15){c.remove(false,false);n++;}}'
          'app.project.save();return "tiny="+n;})()')
    print("CLEAN", pymiere.core.eval_script(cj), flush=True)
    print(f"ГОТОВО: уложено {ok}, пропущено {miss}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
