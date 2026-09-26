"""Замена ПОВТОРЯЮЩЕГОСЯ футажа на РАЗНОЕ: по _dupes.json (кроме gfx-пар) фетчим разнообразный
индийский футаж (для переходных — ротация атмосферного пула, чтобы соседи не совпадали) и
ES-overwrite на живой V3 (БЕЗ пересборки — иначе сотрутся маскот/графика/музыка). Premiere открыт."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
FOOT = PROJECT / "assets" / "_footage"; FOOT.mkdir(parents=True, exist_ok=True)
CACHE = PROJECT / "assets" / "_pexels_cache"; CACHE.mkdir(parents=True, exist_ok=True)
px = PexelsVideosClient()

# пул разнообразного атмосферного индийского футажа (для переходных/fog сцен) — ротация
POOL = [
    "ancient indian temple dark atmosphere", "himalayan mountains mist clouds", "varanasi ghats river dusk",
    "indian street crowd evening", "hindu temple carved architecture", "ganges river flowing sacred",
    "indian jungle forest fog", "old manuscript candlelight", "rajasthan fort desert golden",
    "indian ritual fire smoke night", "monsoon rain india", "indian village dusk smoke",
    "himalayan monastery prayer flags", "indian market spices colorful", "diya oil lamps floating river",
    "stone temple deity carving", "misty forest path mountains", "night desert stars milky way",
    "temple bells incense smoke", "sadhu holy man india", "peacock indian nature", "banyan tree ancient india",
    "indian classical dancer silhouette", "elephant temple procession india", "lotus pond temple reflection",
]


def es(js): return pymiere.core.eval_script(js)


def bounds(sid):
    r = es('(function(){var t=app.project.activeSequence.videoTracks[2];for(var i=0;i<t.clips.numItems;i++){var c=t.clips[i];'
           f'if(c.name.indexOf("{sid}")>=0&&c.name.indexOf("mascot")<0&&c.name.indexOf("_new")<0)return c.start.seconds.toFixed(3)+"|"+c.end.seconds.toFixed(3);}}return "NA";}})()')
    if "|" not in r: return None
    a, b = r.split("|"); return float(a), float(b)


def norm(src, dst, d):
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,"
          "eq=saturation=0.98:contrast=1.03,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,d-0.4):.2f}:d=0.4")
    r = subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{d:.3f}", "-an",
                        "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    dupes = json.loads((PROJECT / "_dupes.json").read_text(encoding="utf-8"))
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    targets = [x for x in dupes if x.get("source") != "gfx-india"]
    print(f"к замене: {len(targets)}", flush=True)

    placed = 0
    pool_i = 0
    for k, x in enumerate(targets):
        sid = x["sid"]
        bd = bounds(sid)
        if not bd:
            print(f"  {sid}: нет клипа на V3 — пропуск"); continue
        st, en = bd; dur = en - st
        vo = (scenes.get(sid, {}).get("voiceover") or "").strip()
        # запрос: если внятный vo — по нему; иначе из ротирующегося пула (разнообразие)
        if len(vo) > 30:
            q = vo[:55] + " india"
        else:
            q = POOL[pool_i % len(POOL)]; pool_i += 1
        got = None
        for idx in (k % 3, 0, 1, 2):
            try:
                p = px.search_and_download(q, CACHE / f"dd_{sid}_{idx}.mp4", index=idx, min_duration=4)
                if p and Path(p).exists() and Path(p).stat().st_size > 10000:
                    dst = FOOT / f"{sid}_dd.mp4"
                    if norm(Path(p), dst, dur):
                        got = dst; break
            except Exception as e:
                print(f"    {sid} err {str(e)[:30]}")
        if not got:
            print(f"  {sid}: не нашёл футаж"); continue
        path = str(got.resolve()).replace("\\", "/")
        tag = f"{sid}_dd"
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{tag}")>=0){{item=root.children[i];break;}}}}'
              'if(!item)return "NOITEM";'
              f'var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
        r = es(js)
        if r == "OK":
            placed += 1
            if placed % 6 == 0: print(f"    ...заменено {placed}", flush=True)
        else:
            print(f"  {sid}: {r}")
    es('(function(){var t=app.project.activeSequence.videoTracks[2],n=0;for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15){c.remove(false,false);n++;}}app.project.save();return "tiny="+n;})()')
    print(f"\nГОТОВО: заменено повторов {placed}/{len(targets)}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
