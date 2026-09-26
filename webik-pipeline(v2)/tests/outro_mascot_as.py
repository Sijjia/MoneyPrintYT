"""Маскот-подпись на аутро Adult Swim (CTA + «С вами был Webik», сцены 275-277):
один маскот-клип с липсинком под голос, заменяет атмосферный футаж. Финальный фейд в чёрное.
  ../webik-pipeline/.venv/Scripts/python.exe tests/outro_mascot_as.py
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.assemble_as as A
import tests.mascot_demo as md

PROJECT = A.PROJECT_DIR
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"
GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
tps = 254016000000
FPS = 30
START_SID, END_SID = "scene_275", "scene_277"


def cstart(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    start = al[START_SID]["start"]
    end = al[END_SID]["end"]
    dur = end - start
    print(f"аутро-маскот: {start:.1f}..{end:.1f} ({dur:.1f}s)", flush=True)

    seg = GFX / "seg_outro.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{start:.2f}", "-t", f"{dur:.2f}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
    mouth = md.mouth_track(seg, dur + 0.2, FPS)
    n = len(mouth)

    props = {"mouth": mouth, "position": "center", "scale": 1.06, "jitter": 0.8,
             "caption": "", "accent": "#1fa48a", "durationInFrames": n}
    pf = REMOTION / "_outro_mascot.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / "outro_mascot_nocap.mp4"   # новое имя → свежий bin-элемент (обход Premiere-кэша)
    r = subprocess.run(f'npx remotion render Mascot "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 20000):
        print("рендер упал:", (r.stderr or r.stdout)[-300:]); return 1

    # кладём на V3 поверх 275-277 (overwrite на длину клипа)
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[A.PARALLAX_VIDEO_TRACK_IDX]
    from services.premiere_template.timeline_ops import import_media, place_clip
    item = import_media(out)
    if item is None:
        print("import упал"); return 1
    place_clip(v3, item, start)  # overwrite=True по умолчанию

    # финальный фейд в чёрное на последнем клипе (этом же)
    js = """
    var seq=app.project.activeSequence, trk=seq.videoTracks[%d], c=null, TOL=0.6;
    for(var i=0;i<trk.clips.numItems;i++){ if(Math.abs(trk.clips[i].start.seconds-%f)<TOL){c=trk.clips[i];break;} }
    if(c){ var opc=null;
      for(var j=0;j<c.components.numItems;j++){ if(c.components[j].displayName.toLowerCase()=='opacity'){opc=c.components[j];break;} }
      if(opc){ var op=null;
        for(var k=0;k<opc.properties.numItems;k++){ if(opc.properties[k].displayName.toLowerCase()=='opacity'){op=opc.properties[k];break;} }
        if(op && op.areKeyframesSupported()){ if(!op.isTimeVarying())op.setTimeVarying(true);
          var ins=c.inPoint.seconds, outs=c.outPoint.seconds;
          op.addKey(ins); op.setValueAtKey(ins,0.0,true); op.addKey(ins+0.6); op.setValueAtKey(ins+0.6,100.0,true);
          op.addKey(outs-0.8); op.setValueAtKey(outs-0.8,100.0,true); op.addKey(outs); op.setValueAtKey(outs,0.0,true);
          'faded'; } } }
    """ % (A.PARALLAX_VIDEO_TRACK_IDX, start)
    print("fade:", pymiere.core.eval_script(js), flush=True)

    man[START_SID] = {"path": str(out), "query": "outro mascot", "kind": "video", "source": "gfx-fix"}
    (PROJECT / "assets" / "images" / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print("готово, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
