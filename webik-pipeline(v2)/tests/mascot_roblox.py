"""Маскот точечно для «Айсберг Roblox»: 2 врезки (scam-warning, item-value) + аутро-подпись.
Липсинк по голосу сцены, кладёт на V3 (overwrite). Аутро — центр, без подписи, фейд в чёрное.
Premiere с проектом открыт.  ../webik-pipeline/.venv/Scripts/python.exe tests/mascot_roblox.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.assemble_roblox as A
import tests.mascot_demo as md
from services.premiere_template.timeline_ops import import_media, place_clip

PROJECT = A.PROJECT_DIR
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
V3 = A.PARALLAX_VIDEO_TRACK_IDX
FPS = 30

INSERTS = [
    {"sid": "scene_034", "caption": "Никаких «бесплатных Robux» не существует — это ловушка для кражи аккаунта.", "eco": "scene_036"},
    {"sid": "scene_045", "caption": "Одна виртуальная вещь — тысячи реальных долларов.", "eco": "scene_047"},
]


def clip_starts():
    csv = pymiere.core.eval_script(
        "(function(){var t=app.project.activeSequence.videoTracks[%d],a=[];"
        "for(var i=0;i<t.clips.numItems;i++)a.push(t.clips[i].start.seconds);return a.join(',');})()" % V3)
    return [float(x) for x in csv.split(",") if x.strip()]


def render(props, out, frames):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_msc_{out.stem}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render Mascot "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out.exists() and out.stat().st_size > 20000


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    trimmed = PROJECT / "assets" / "video_stock" / "_trimmed"
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[V3]
    starts = clip_starts()

    def find(t):
        best, bi = 1e9, None
        for i, s in enumerate(starts):
            if abs(s - t) < best:
                best, bi = abs(s - t), i
        return v3.clips[bi] if bi is not None and best < 1.2 else None

    # длительности слотов
    srt = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
    dur = {}
    for i, (st, sid) in enumerate(srt):
        dur[sid] = (srt[i + 1][0] if i + 1 < len(srt) else st + 4) - st

    done = 0
    # --- врезки ---
    for job in INSERTS:
        sid = job["sid"]
        if sid not in al:
            print(f"  ✗ {sid} нет в alignment"); continue
        d = dur.get(sid, 4.0)
        seg = GFX / f"seg_{sid}.wav"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{al[sid]['start']:.2f}", "-t", f"{d:.2f}", "-i", str(VOICE),
                        "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
        mouth = md.mouth_track(seg, d + 0.2, FPS)
        comp = []
        eco = trimmed / f"{job['eco']}.mp4"
        cf = REMOTION / "public" / "mascot" / f"rb_{sid}.jpg"
        if eco.exists() and md.grab_frame(eco, cf):
            comp = [{"src": f"mascot/rb_{sid}.jpg", "x": 0.72, "y": 0.36, "w": 640, "from": 12, "to": len(mouth) - 6}]
        out = GFX / f"mascot_{sid}.mp4"
        if render({"mouth": mouth, "position": "left", "scale": 0.95, "jitter": 0.8,
                   "companions": comp, "caption": job["caption"], "accent": "#00a2ff"}, out, len(mouth)):
            c = find(al[sid]["start"])
            item = import_media(out)
            if item is not None:
                place_clip(v3, item, al[sid]["start"])
                done += 1; print(f"  ✓ врезка {sid}", flush=True)
        else:
            print(f"  ✗ render {sid}")

    # --- аутро ---
    outro_scenes = [s for s in scenes if (s.get("section") or "") in ("outro", "cta", "conclusion") and s["id"] in al]
    if outro_scenes:
        st = min(al[s["id"]]["start"] for s in outro_scenes)
        en = max(al[s["id"]]["end"] for s in outro_scenes)
        d = en - st
        seg = GFX / "seg_outro.wav"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{st:.2f}", "-t", f"{d:.2f}", "-i", str(VOICE),
                        "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
        mouth = md.mouth_track(seg, d + 0.2, FPS)
        out = GFX / "mascot_outro.mp4"
        if render({"mouth": mouth, "position": "center", "scale": 1.06, "jitter": 0.8,
                   "caption": "", "accent": "#00a2ff"}, out, len(mouth)):
            item = import_media(out)
            if item is not None:
                place_clip(v3, item, st)
                # фейд в чёрное на аутро
                js = """
                var seq=app.project.activeSequence, trk=seq.videoTracks[%d], c=null, TOL=0.8;
                for(var i=0;i<trk.clips.numItems;i++){ if(Math.abs(trk.clips[i].start.seconds-%f)<TOL){c=trk.clips[i];break;} }
                if(c){ var opc=null;
                  for(var j=0;j<c.components.numItems;j++){ if(c.components[j].displayName.toLowerCase()=='opacity'){opc=c.components[j];break;} }
                  if(opc){ var op=null;
                    for(var k=0;k<opc.properties.numItems;k++){ if(opc.properties[k].displayName.toLowerCase()=='opacity'){op=opc.properties[k];break;} }
                    if(op && op.areKeyframesSupported()){ if(!op.isTimeVarying())op.setTimeVarying(true);
                      var ins=c.inPoint.seconds, outs=c.outPoint.seconds;
                      op.addKey(ins); op.setValueAtKey(ins,0.0,true); op.addKey(ins+0.6); op.setValueAtKey(ins+0.6,100.0,true);
                      op.addKey(outs-0.8); op.setValueAtKey(outs-0.8,100.0,true); op.addKey(outs); op.setValueAtKey(outs,0.0,true); } } }
                """ % (V3, st)
                pymiere.core.eval_script(js)
                done += 1; print("  ✓ аутро-маскот + фейд", flush=True)

    pymiere.objects.app.project.save()
    print(f"\nмаскот-врезок/аутро: {done}; сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
