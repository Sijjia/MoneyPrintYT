"""EN спец-графика: KarniCurse (scene_077) + EnumShowcase (scene_048) с англ-текстом,
ES-overwrite на живой EN V3 по EN alignment.
  ../webik-pipeline/.venv/Scripts/python.exe tests/specials_india_en.py"""
import sys, json, subprocess, os
from pathlib import Path
ROOT = Path("C:/Users/aidar/OneDrive/Рабочий стол/automotization-youtube/webik-pipeline(v2)")
sys.path.insert(0, str(ROOT))
import pymiere
REM = ROOT / "remotion"
P = ROOT / "projects/2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
GFX = P / "assets/gfx"; GFX.mkdir(parents=True, exist_ok=True)

def es(js): return pymiere.core.eval_script(js)

al = json.loads((P / "assets/alignment.json").read_text(encoding="utf-8"))["scenes"]
scenes = json.loads((P / "scenes.json").read_text(encoding="utf-8"))["scenes"]
order = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
nxt = {order[i][1]: (order[i+1][0] if i+1 < len(order) else order[i][0]+4) for i in range(len(order))}

# sid: (component, props, fade?)
JOBS = {
 "scene_077": ("KarniCurse", {
    "kicker": "THE LEGEND OF KARNI MATA", "title": "THE CURSE ON THE GOD OF DEATH",
    "refuseLabel": "REFUSED", "bypassLabel": "bypassing Yama's power",
    "caption": "Karni's clan is reborn as rats — bypassing Yama — then born human again."}),
 "scene_048": ("EnumShowcase", {
    "kicker": "AYURVEDA", "title": "MILLENNIA OF PLANT KNOWLEDGE",
    "items": [{"img": "enum/turmeric.jpg", "label": "TURMERIC", "sub": "anti-inflammatory"},
              {"img": "enum/neem.jpg", "label": "NEEM", "sub": "antiseptic"},
              {"img": "enum/ashwagandha.jpg", "label": "ASHWAGANDHA", "sub": "adaptogen"}],
    "caption": ""}),
}

done = 0
for sid, (comp, props) in JOBS.items():
    if sid not in al: print(sid, "нет в alignment"); continue
    st = al[sid]["start"]; slot = max(1.8, nxt[sid] - st)
    frames = int(round(slot * 30)) + (4 if comp == "KarniCurse" else 12)
    pr = dict(props); pr["durationInFrames"] = frames
    pf = REM / f"_sp_{sid}.json"; pf.write_text(json.dumps(pr, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_enspecial.mp4"
    r2 = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out,REM).replace(os.sep,"/")}" --props="{os.path.relpath(pf,REM).replace(os.sep,"/")}" --codec=h264 --muted --log=error', cwd=str(REM), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 20000):
        print(f"{sid}: render fail {(r2.stderr or r2.stdout)[-140:]}"); continue
    norm = GFX / f"{sid}_enspecial_n.mp4"
    vf = f"scale=1920:1080,setsar=1,fps=30,fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,slot-0.4):.2f}:d=0.4"
    subprocess.run(["ffmpeg","-y","-i",str(out),"-t",f"{slot:.3f}","-an","-vf",vf,"-r","30","-c:v","libx264","-crf","19","-pix_fmt","yuv420p",str(norm)], capture_output=True)
    path = str(norm.resolve()).replace("\\","/")
    js = ('(function(){var proj=app.project;'
          f'proj.importFiles(["{path}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
          f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{sid}_enspecial_n")>=0){{item=root.children[i];break;}}}}'
          f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
    print(f"{sid} {comp} @{int(st)//60:02d}:{int(st)%60:02d} =>", es(js)); done += 1
es('app.project.save();')
print(f"\nГОТОВО: EN спец-графики {done}")
