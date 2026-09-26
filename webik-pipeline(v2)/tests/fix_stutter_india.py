"""Фикс ЛАГА/повтора кадров: мои footage-замены (_footage/_dd) были залуплены `-stream_loop -1`
из коротких пекселс-клипов → видимый повтор. Пере-нормализую ПЛАВНО (короткий → slow-mo до 2.6×,
совсем короткий → бумеранг-пинпонг) из кэш-оригиналов, БЕЗ жёсткого лупа, и ES-overwrite на V3.
Premiere открыт."""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
FOOT = PROJECT / "assets" / "_footage"
CACHE = PROJECT / "assets" / "_pexels_cache"
FIX = PROJECT / "assets" / "_footage_fix"; FIX.mkdir(parents=True, exist_ok=True)
MAX_SLOW = 2.6


def es(js): return pymiere.core.eval_script(js)


def dur(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0


def orig_source(sid):
    """Найти самый ДЛИННЫЙ кэш-оригинал для сцены (до нашего лупа)."""
    cands = list(CACHE.glob(f"foot_{sid}_*.mp4")) + list(CACHE.glob(f"dd_{sid}_*.mp4")) + \
            list(CACHE.glob(f"{sid}_*.mp4")) + list(CACHE.glob(f"s{sid.split('_')[-1]}_*.mp4"))
    cands = [c for c in cands if c.exists() and c.stat().st_size > 10000]
    if not cands: return None
    return max(cands, key=dur)


def smooth_norm(src, dst, slot):
    """Ровно slot секунд БЕЗ лупа: длиннее→просто режем; короче→slow-mo (setpts); совсем→бумеранг."""
    sd = dur(src)
    base = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,eq=saturation=0.98:contrast=1.03,setsar=1")
    fades = f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,slot-0.4):.2f}:d=0.4"
    if sd >= slot - 0.05:
        vf = f"{base},fps=30,{fades}"
        inp = ["-i", str(src), "-t", f"{slot:.3f}"]
    elif sd * MAX_SLOW >= slot:
        factor = slot / sd
        vf = f"{base},setpts={factor:.4f}*PTS,fps=30,{fades}"
        inp = ["-i", str(src), "-t", f"{slot:.3f}"]
    else:
        # бумеранг: forward+reverse (пинпонг) удлиняет вдвое; при нужде + лёгкий slow-mo, потом режем
        pp = FIX / f"_pp_{dst.stem}.mp4"
        subprocess.run(["ffmpeg", "-y", "-i", str(src), "-filter_complex",
                        "[0]split[a][b];[b]reverse[r];[a][r]concat=n=2:v=1:a=0", "-an", str(pp)], capture_output=True, text=True)
        ppd = dur(pp) or sd * 2
        factor = max(1.0, slot / ppd) if ppd > 0 else 1.0
        vf = f"{base},setpts={min(factor,MAX_SLOW):.4f}*PTS,fps=30,{fades}"
        inp = ["-i", str(pp), "-t", f"{slot:.3f}"]
    r = subprocess.run(["ffmpeg", "-y", *inp, "-an", "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20",
                        "-pix_fmt", "yuv420p", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    # все клипы V3, чьи медиа лежат в _footage (мои замены)
    raw = es('(function(){var t=app.project.activeSequence.videoTracks[2],o=[];for(var i=0;i<t.clips.numItems;i++){var c=t.clips[i];'
             'var mp="";try{mp=c.projectItem.getMediaPath();}catch(e){}'
             'o.push(c.name+"@@"+c.start.seconds.toFixed(3)+"@@"+c.end.seconds.toFixed(3)+"@@"+mp);}return o.join("\\n");})()')
    fixed = 0; checked = 0
    for line in raw.split("\n"):
        parts = line.split("@@")
        if len(parts) < 4: continue
        nm, st, en, mp = parts
        if "_footage" not in mp and "_dd" not in nm and "footage" not in nm.lower():
            continue
        m = re.search(r"scene_\d+", nm) or re.search(r"scene_\d+", mp)
        if not m: continue
        sid = m.group(0)
        slot = float(en) - float(st)
        placed = Path(mp)
        # луплен ли: сравниваем оригинал-кэш с slot
        src = orig_source(sid)
        if not src: continue
        sd = dur(src)
        checked += 1
        if sd >= slot - 0.05:
            # исходник длиннее слота — луп не нужен был; но наш placed мог быть залуплен из ДРУГОГО.
            # всё равно пере-нормализуем ровно (без лупа) для гарантии.
            pass
        elif sd >= slot:  # не бывает, для ясности
            continue
        dst = FIX / f"{sid}_fx.mp4"
        if not smooth_norm(src, dst, slot):
            print(f"  {sid}: norm fail"); continue
        path = str(dst.resolve()).replace("\\", "/")
        tag = f"{sid}_fx"
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{tag}")>=0){{item=root.children[i];break;}}}}'
              'if(!item)return "NOITEM";'
              f'var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{float(st)});return "OK";}})()')
        r = es(js)
        if r == "OK":
            fixed += 1
            if fixed % 6 == 0: print(f"    ...пере-нормализовано {fixed}", flush=True)
        else:
            print(f"  {sid}: {r}")
    es('(function(){var t=app.project.activeSequence.videoTracks[2],n=0;for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15){c.remove(false,false);n++;}}app.project.save();return "tiny="+n;})()')
    print(f"\nГОТОВО: проверено {checked}, пере-нормализовано плавно {fixed}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
