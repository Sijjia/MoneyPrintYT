"""Живой таймлайн: (1) кросс-сценовые ДУБЛИ контента (одно медиа в разных темах), (2) короткие
клипы, ЗАЦИКЛЕННЫЕ внутри своей сцены (источник<слот). Хэширую все клипы V3 (getMediaPath) →
дубли+лупы → перекачиваю УНИКАЛЬНЫЙ ДЛИННЫЙ футаж (min_duration>=slot; после фетча ПРОВЕРЯЮ хэш,
чтоб не создать новый дубль). ES-overwrite. Графику/маскот/enum скипаю. Premiere открыт."""
import json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.pexels_videos import PexelsVideosClient
from PIL import Image

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
FIX = PROJECT / "assets" / "_footage_fix"; FIX.mkdir(parents=True, exist_ok=True)
CACHE = PROJECT / "assets" / "_pexels_cache"
TMP = Path(tempfile.mkdtemp())
px = PexelsVideosClient()
scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}


def es(js): return pymiere.core.eval_script(js)
def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0


def _hash1(mp, at, hs=8):
    fr = TMP / (Path(mp).stem + f"_{at:.1f}.jpg")
    subprocess.run(["ffmpeg", "-y", "-ss", f"{at:.2f}", "-i", str(mp), "-frames:v", "1", "-vf", "scale=64:64", str(fr)], capture_output=True)
    if not fr.exists(): return None
    try:
        im = Image.open(fr).convert("L").resize((hs + 1, hs))
        px_ = list(im.getdata()); bits = 0
        for r in range(hs):
            for c in range(hs):
                bits = (bits << 1) | (1 if px_[r * (hs + 1) + c] < px_[r * (hs + 1) + c + 1] else 0)
        return bits
    except: return None


def dhash(mp):
    """3 кадра (25/50/75%) → список хэшей (ловит «тот же ролик другим сегментом»)."""
    d = dur(mp) or 3.0
    hs = [_hash1(mp, max(0.3, d * f)) for f in (0.25, 0.5, 0.75)]
    return [h for h in hs if h is not None] or None


def ham(a, b): return bin(a ^ b).count("1")
THRESH = 10
def is_dup(hlist, used_lists):
    """дубль, если хоть один кадр близок к хоть одному кадру ранее использованного клипа."""
    for oh in used_lists:
        for a in hlist:
            for b in oh:
                if ham(a, b) <= THRESH:
                    return True
    return False
def busy():
    b = set()
    ga = PROJECT / "_gfx_assigns.json"
    if ga.exists(): b |= set(json.loads(ga.read_text(encoding="utf-8")).keys())
    for p in (PROJECT / "assets" / "gfx").glob("*.mp4"):
        m = re.match(r"(scene_\d+)", p.name.replace("mascot_", ""))
        if m: b.add(m.group(1))
    return b


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
        if not m or m.group(0) in bs: continue
        vis = (scenes.get(m.group(0), {}).get("visual") or {}).get("type")
        if vis in ("level_card", "topic_card"): continue
        if not mp or not Path(mp).exists(): continue
        items.append([m.group(0), float(st), float(en), mp])
    items.sort(key=lambda x: x[1])
    print(f"клипов: {len(items)}", flush=True)

    # хэши + детект дублей и лупов
    used_hashes = []   # список hlist
    todo = []          # sid к перекачке
    for sid, st, en, mp in items:
        slot = en - st
        h = dhash(mp)
        srcd = dur(mp)
        loop = srcd > 0 and srcd < slot - 0.35
        dup = False
        if h is not None:
            dup = is_dup(h, used_hashes)
            if not dup: used_hashes.append(h)
        if dup or loop:
            todo.append((sid, st, en, "dup" if dup else "loop"))
    print(f"дублей+лупов к фиксу: {len(todo)}", flush=True)

    used_set = list(used_hashes)
    fixed = 0
    for k, (sid, st, en, why) in enumerate(todo):
        slot = en - st
        vo = (scenes[sid].get("voiceover") or "")
        base_q = vo[:55] if len(vo) > 25 else "india temple culture ritual"
        got = None
        for attempt, q in enumerate([base_q + " india", base_q + " india footage", "ancient india " + base_q[:30]]):
            for idx in (k % 4, 0, 1, 2, 3):
                try:
                    pth = px.search_and_download(q, CACHE / f"dl_{sid}_{attempt}_{idx}.mp4", index=idx, min_duration=max(5, int(slot) + 1))
                    if pth and Path(pth).exists() and Path(pth).stat().st_size > 10000 and dur(pth) >= slot - 0.3:
                        nh = dhash(pth)
                        if nh is not None and is_dup(nh, used_set):
                            continue  # новый дубль — берём другой
                        dst = FIX / f"{sid}_dl.mp4"
                        if norm(Path(pth), dst, slot):
                            got = dst
                            if nh is not None: used_set.append(nh)
                            break
                except Exception as e:
                    print(f"    {sid} err {str(e)[:22]}")
            if got: break
        if not got:
            print(f"  {sid} [{why}]: не нашёл уникальный длинный"); continue
        path = str(got.resolve()).replace("\\", "/"); tag = f"{sid}_dl"
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{tag}")>=0){{item=root.children[i];break;}}}}'
              f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
        if es(js) == "OK":
            fixed += 1; print(f"  {sid} [{why}] slot={slot:.1f} => OK", flush=True)
    es('(function(){var t=app.project.activeSequence.videoTracks[2];for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15)c.remove(false,false);}app.project.save();return 1;})()')
    print(f"\nГОТОВО: дублей+лупов {len(todo)}, исправлено {fixed}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
