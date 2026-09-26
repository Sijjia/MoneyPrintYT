"""EN-портреты личностей (DocuFrame) для «Iceberg of India». Фото уже в remotion/public/portraits
(язык-независимые), кадрированы по ЛИЦУ. Тут только EN kicker/source, имя = как есть. Рендер под
EN-слот (по EN alignment) + ES-overwrite на живой EN V3.
  ../webik-pipeline/.venv/Scripts/python.exe tests/portraits_india_en.py"""
import sys, json, subprocess, os
from pathlib import Path
ROOT = Path("C:/Users/aidar/OneDrive/Рабочий стол/automotization-youtube/webik-pipeline(v2)")
sys.path.insert(0, str(ROOT))
import pymiere
REM = ROOT / "remotion"
P = ROOT / "projects/2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
GFX = P / "assets/gfx"; GFX.mkdir(parents=True, exist_ok=True)

def es(js): return pymiere.core.eval_script(js)

# sid: (imgSrc, kicker EN, title, source EN)
JOBS = {
 "scene_023": ("portraits/lahauri.jpg", "CHIEF ARCHITECT", "Ustad Ahmad Lahauri", "Indian miniature · Wikimedia"),
 "scene_019": ("portraits/shahjahan.jpg", "MUGHAL EMPEROR", "Shah Jahan", "Wikimedia Commons"),
 "scene_166": ("portraits/asaram.jpg", "GURU ON TRIAL", "Asaram Bapu", "Wikimedia Commons"),
 "scene_169": ("portraits/ramrahim.jpg", "SECT LEADER", "Gurmeet Ram Rahim Singh", "Wikimedia Commons"),
 "scene_184": ("portraits/sleeman.jpg", "BRITISH OFFICER", "William Sleeman", "Portrait · Wikimedia Commons"),
 "scene_239": ("portraits/johnchau.jpg", "MISSIONARY", "John Allen Chau", "Wikimedia Commons"),
}

al = json.loads((P / "assets/alignment.json").read_text(encoding="utf-8"))["scenes"]
scenes = json.loads((P / "scenes.json").read_text(encoding="utf-8"))["scenes"]
order = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
nxt = {order[i][1]: (order[i+1][0] if i+1 < len(order) else order[i][0]+4) for i in range(len(order))}

done = 0
for sid, (img, kicker, title, source) in JOBS.items():
    if sid not in al: print(sid, "нет в alignment"); continue
    st = al[sid]["start"]; slot = max(1.8, nxt[sid] - st)
    frames = int(round(slot * 30)) + 12
    props = {"imgSrc": img, "kicker": kicker, "title": title, "source": source, "durationInFrames": frames}
    pf = REM / f"_pten_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_enportrait.mp4"
    r2 = subprocess.run(f'npx remotion render DocuFrame "{os.path.relpath(out,REM).replace(os.sep,"/")}" --props="{os.path.relpath(pf,REM).replace(os.sep,"/")}" --codec=h264 --muted --log=error', cwd=str(REM), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 20000):
        print(f"{sid}: render fail {(r2.stderr or r2.stdout)[-120:]}"); continue
    norm = GFX / f"{sid}_enportrait_n.mp4"
    subprocess.run(["ffmpeg","-y","-i",str(out),"-t",f"{slot:.3f}","-an","-vf","scale=1920:1080,setsar=1,fps=30","-r","30","-c:v","libx264","-crf","20","-pix_fmt","yuv420p",str(norm)], capture_output=True)
    path = str(norm.resolve()).replace("\\","/")
    js = ('(function(){var proj=app.project;'
          f'proj.importFiles(["{path}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
          f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{sid}_enportrait_n")>=0){{item=root.children[i];break;}}}}'
          f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
    print(f"{sid} {title} @{int(st)//60:02d}:{int(st)%60:02d} =>", es(js))
    done += 1
es('app.project.save();')
print(f"\nГОТОВО: EN-портретов {done}")
