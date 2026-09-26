"""Ре-рендер EN bespoke-графики из сохранённого _gfx_assigns.json (без LLM) — чтобы подхватить
англ-дефолты компонентов. ES-overwrite на живой EN V3 по EN alignment.
  ../webik-pipeline/.venv/Scripts/python.exe tests/rerender_en_gfx.py"""
import json, os, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
REM = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"
FPS = 30

def es(js): return pymiere.core.eval_script(js)

al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
order = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
nxt = {order[i][1]: (order[i+1][0] if i+1 < len(order) else order[i][0]+4) for i in range(len(order))}
keep = json.loads((PROJECT / "_gfx_assigns.json").read_text(encoding="utf-8"))

placed = fail = 0
for sid, a in sorted(keep.items(), key=lambda kv: al.get(kv[0], {}).get("start", 0)):
    if sid not in al: continue
    st = al[sid]["start"]; slot = max(1.5, nxt[sid] - st)
    frames = int(round(slot * FPS)) + 15
    props = dict(a.get("props", {})); props["durationInFrames"] = max(80, frames)
    pf = REM / f"_re_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_engfx.mp4"
    r = subprocess.run(f'npx remotion render {a["component"]} "{os.path.relpath(out,REM).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf,REM).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REM), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 20000):
        fail += 1; print(f"  ✗ {sid} render {(r.stderr or r.stdout)[-120:]}"); continue
    norm = GFX / f"{sid}_engfx_n.mp4"
    vf = f"scale=1920:1080,setsar=1,fps=30,fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,slot-0.4):.2f}:d=0.4"
    subprocess.run(["ffmpeg","-y","-i",str(out),"-t",f"{slot:.3f}","-an","-vf",vf,"-r","30","-c:v","libx264","-crf","19","-pix_fmt","yuv420p",str(norm)], capture_output=True)
    p = str(norm.resolve()).replace("\\","/")
    js = ('(function(){var proj=app.project;'
          f'proj.importFiles(["{p}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
          f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{sid}_engfx_n")>=0){{item=root.children[i];break;}}}}'
          f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
    r2 = es(js)
    if r2 == "OK": placed += 1; print(f"  ✓ {sid} {a['component']} @{int(st)//60:02d}:{int(st)%60:02d} ({placed})", flush=True)
    else: fail += 1; print(f"  ✗ {sid} place={r2}")
es('app.project.save();')
print(f"\nГОТОВО: ре-рендер EN-графики {placed}, ошибок {fail}")
