"""Автономный QC живого таймлайна: кадр из КАЖДОГО клипа V3 (getMediaPath) → vision-чек vs закадр →
мимо-темы добиваю реальным футажом (min_duration>=slot, без джаддера) ES-overwrite. Графику/маскот/
enum/оверлеи не трогаю. Premiere открыт. Env: QC_ONLY_FLAG=1 (только пометить, не чинить)."""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.media_vision_qc as vqc
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
FIX = PROJECT / "assets" / "_footage_fix"; FIX.mkdir(parents=True, exist_ok=True)
CACHE = PROJECT / "assets" / "_pexels_cache"
TMP = Path(tempfile.mkdtemp())
px = PexelsVideosClient()
scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}


def es(js): return pymiere.core.eval_script(js)


def busy():
    b = set()
    ga = PROJECT / "_gfx_assigns.json"
    if ga.exists(): b |= set(json.loads(ga.read_text(encoding="utf-8")).keys())
    for p in (PROJECT / "assets" / "gfx").glob("*.mp4"):
        m = re.match(r"(scene_\d+)", p.name.replace("mascot_", ""))
        if m: b.add(m.group(1))
    return b


def frame_of_file(mp, sid):
    out = TMP / f"{sid}.jpg"
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(mp)], capture_output=True, text=True)
    try: d = float(r.stdout.strip())
    except: d = 2.0
    subprocess.run(["ffmpeg", "-y", "-ss", f"{max(0.3,d*0.5):.2f}", "-i", str(mp), "-frames:v", "1", "-vf", "scale=512:-1", str(out)], capture_output=True)
    return out if out.exists() and out.stat().st_size > 2000 else None


def norm(src, dst, d):
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=saturation=0.99:contrast=1.03,setsar=1,fps=30,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,d-0.4):.2f}:d=0.4")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{d:.3f}", "-an", "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    bs = busy()
    raw = es('(function(){var t=app.project.activeSequence.videoTracks[2],o=[];for(var i=0;i<t.clips.numItems;i++){var c=t.clips[i];'
             'var mp="";try{mp=c.projectItem.getMediaPath();}catch(e){}o.push(c.name+"|@|"+c.start.seconds.toFixed(3)+"|@|"+c.end.seconds.toFixed(3)+"|@|"+mp);}return o.join(";;;");})()')
    items = []
    for line in raw.split(";;;"):
        p = line.split("|@|")
        if len(p) < 4: continue
        nm, st, en, mp = p
        m = re.search(r"scene_\d+", nm)
        if not m: continue
        sid = m.group(0)
        if sid in bs: continue                                  # графика/маскот
        vis = (scenes.get(sid, {}).get("visual") or {}).get("type")
        if vis in ("level_card", "topic_card"): continue
        if not mp or not Path(mp).exists(): continue
        items.append((sid, float(st), float(en), mp))
    print(f"клипов к проверке: {len(items)}", flush=True)

    # vision-QC батчами
    bad = {}
    B = vqc.BATCH
    for i in range(0, len(items), B):
        chunk = items[i:i + B]
        batch = []
        for sid, st, en, mp in chunk:
            img = frame_of_file(mp, sid)
            if img: batch.append({"id": sid, "vo": (scenes[sid].get("voiceover") or "")[:200], "img": img})
        try:
            for v in vqc.vision_call(batch):
                if v.get("id") and not v.get("ok"):
                    bad[v["id"]] = v.get("better_query") or ""
        except Exception as e:
            print(f"  QC батч err: {str(e)[:70]}", flush=True)
        print(f"  {min(i+B,len(items))}/{len(items)} (брак пока {len(bad)})", flush=True)

    print(f"\nмимо-темы: {len(bad)}", flush=True)
    if os.environ.get("QC_ONLY_FLAG") == "1":
        (PROJECT / "_live_qc_bad.json").write_text(json.dumps(bad, ensure_ascii=False, indent=1), encoding="utf-8")
        for sid, q in list(bad.items())[:40]: print(f"  {sid}: «{q[:45]}»")
        return 0

    pos = {sid: (st, en) for sid, st, en, mp in items}
    fixed = 0
    for sid, bq in bad.items():
        st, en = pos[sid]; slot = en - st
        vo = (scenes[sid].get("voiceover") or "")
        q = bq or (vo[:55] + " india")
        got = None
        for idx in (0, 1, 2):
            try:
                pth = px.search_and_download(q, CACHE / f"lq_{sid}_{idx}.mp4", index=idx, min_duration=max(5, int(slot) + 1))
                if pth and Path(pth).exists() and Path(pth).stat().st_size > 10000:
                    d = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(pth)], capture_output=True, text=True)
                    try: srcd = float(d.stdout.strip())
                    except: srcd = 0
                    if srcd >= slot - 0.3:
                        dst = FIX / f"{sid}_lq.mp4"
                        if norm(Path(pth), dst, slot): got = dst; break
            except Exception as e:
                print(f"    {sid} err {str(e)[:25]}")
        if not got:
            print(f"  {sid}: не нашёл длинный"); continue
        path = str(got.resolve()).replace("\\", "/"); tag = f"{sid}_lq"
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{tag}")>=0){{item=root.children[i];break;}}}}'
              f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
        if es(js) == "OK":
            fixed += 1
            if fixed % 6 == 0: print(f"    ...исправлено {fixed}", flush=True)
    es('(function(){var t=app.project.activeSequence.videoTracks[2];for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15)c.remove(false,false);}app.project.save();return 1;})()')
    print(f"\nГОТОВО: проверено {len(items)}, мимо-темы {len(bad)}, исправлено {fixed}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
