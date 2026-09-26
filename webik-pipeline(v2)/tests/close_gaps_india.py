"""Закрыть МИКРО-гэпы на V3 (чёрные вспышки между сценами): для каждого гэпа продлеваю ПРЕДЫДУЩИЙ
клип, заморозив его последний кадр на длину гэпа (ffmpeg tpad=clone) + мягкий fade — так чёрного
кадра нет, переход плавный. Большие гэпы (слоты плашек V4) не трогаю. Premiere открыт."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
GC = PROJECT / "assets" / "_gapclose"; GC.mkdir(parents=True, exist_ok=True)


def es(js): return pymiere.core.eval_script(js)


def clips_v3():
    raw = es('(function(){var t=app.project.activeSequence.videoTracks[2],o=[];for(var i=0;i<t.clips.numItems;i++){var c=t.clips[i];'
             'var mp="";try{mp=c.projectItem.getMediaPath();}catch(e){}'
             'o.push(c.start.seconds.toFixed(3)+"_"+c.end.seconds.toFixed(3)+"_"+mp);}return o.join(";;");})()')
    out = []
    for l in raw.split(";;"):
        p = l.split("_", 2)
        if len(p) == 3:
            try: out.append((float(p[0]), float(p[1]), p[2]))
            except: pass
    out.sort()
    return out


def freeze_extend(src, dst, base_len, gap):
    """Обрезаю вшитый fade-out (последние ~0.42с), замораживаю последний КОНТЕНТНЫЙ кадр на
    (gap+0.42), потом ОДИН плавный fade-out в самом конце. total = base+gap. Чёрного-мороза нет."""
    content = max(0.3, base_len - 0.42)     # без вшитого хвоста-фейда
    total = base_len + gap
    freeze = total - content                 # сколько морозим (перекрывает бывший фейд + гэп)
    # trim в ФИЛЬТРЕ (не output -t), чтобы tpad продлил ПОСЛЕ обрезки
    vf = (f"trim=0:{content:.3f},setpts=PTS-STARTPTS,"
          f"scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,"
          f"tpad=stop_mode=clone:stop_duration={freeze+0.05:.3f},"
          f"fade=t=in:st=0:d=0.25,fade=t=out:st={max(0.25,total-0.45):.2f}:d=0.45")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-an", "-vf", vf, "-t", f"{total:.3f}",
                        "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 30000


def main() -> int:
    clips = clips_v3()
    print(f"V3 клипов: {len(clips)}", flush=True)
    closed = 0; skipped = 0
    for i in range(len(clips) - 1):
        st, en, mp = clips[i]
        gap = clips[i + 1][0] - en
        if gap <= 0.017 or gap >= 1.0:
            continue  # нет гэпа или большой (плашка V4)
        if not mp or not Path(mp).exists():
            skipped += 1; continue
        base = en - st
        dst = GC / f"gc_{i}_{int(st)}.mp4"
        if not freeze_extend(Path(mp), dst, base, gap):
            skipped += 1; continue
        path = str(dst.resolve()).replace("\\", "/")
        tag = dst.stem
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
              f'for(var k=root.children.numItems-1;k>=0;k--){{if(root.children[k].name.indexOf("{tag}")>=0){{item=root.children[k];break;}}}}'
              f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
        r = es(js)
        if r == "OK":
            closed += 1
            if closed % 10 == 0: print(f"    ...закрыто {closed}", flush=True)
        else:
            skipped += 1
    es('app.project.save();')
    print(f"\nГОТОВО: закрыто гэпов {closed}, пропущено {skipped}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
