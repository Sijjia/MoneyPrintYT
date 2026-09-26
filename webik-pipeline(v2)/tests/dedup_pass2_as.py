"""Второй проход дедупа для упрямых групп (новостной/редкий футаж, distinct-видео нет):
поздние вхождения пере-нарезаем из ТОГО ЖЕ исходника со сдвигом старта (+ зеркало для
совсем коротких) → другой стартовый кадр, визуально не читается как повтор, остаётся
реальным и по теме. Меняем клип на живом таймлайне. Чисто-чёрные/атмосферу пропускаем.
  ../webik-pipeline/.venv/Scripts/python.exe tests/dedup_pass2_as.py
"""
import json, hashlib, subprocess, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.assemble_as as A

PROJECT = A.PROJECT_DIR
IMG = PROJECT / "assets" / "images"
TRIMMED = A.TRIMMED_DIR
tps = 254016000000
OFFSETS = [2.5, 4.5, 6.5, 8.0]


def md5f(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None


def cstart(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def probe_dur(p):
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(p)], capture_output=True, text=True)
        return float(r.stdout.strip())
    except Exception:
        return 0.0


IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def recut(src, dst, slot, offset, flip, occ):
    """Видео → сдвиг старта; картинка → другое кадрирование (кроп + зум + зеркало)."""
    is_img = Path(src).suffix.lower() in IMG_EXT
    try:
        if is_img:
            # увеличиваем и кропаем РАЗНУЮ область → другое кадрирование того же фото
            zx = [1.35, 1.5, 1.65, 1.8][occ % 4]
            px = ["0", "(iw-ow)", "(iw-ow)/2", "0"][occ % 4]      # разный угол
            py = ["0", "(ih-oh)", "0", "(ih-oh)/2"][occ % 4]
            base = f"scale={int(1920*zx)}:{int(1080*zx)}:force_original_aspect_ratio=increase:flags=lanczos"
            vf = f"{base},crop=1920:1080:{px}:{py},setsar=1"
            if flip:
                vf += ",hflip"
            cmd = ["ffmpeg", "-y", "-loop", "1", "-i", str(src), "-t", f"{slot:.3f}",
                   "-r", "30", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                   "-crf", "20", "-pix_fmt", "yuv420p", str(dst)]
        else:
            vf = "scale=1920:1080:flags=lanczos"
            if flip:
                vf += ",hflip"
            cmd = ["ffmpeg", "-y", "-ss", f"{offset:.2f}", "-stream_loop", "-1", "-i", str(src),
                   "-t", f"{slot:.3f}", "-an", "-vf", vf, "-c:v", "libx264", "-preset", "veryfast",
                   "-crf", "20", "-pix_fmt", "yuv420p", str(dst)]
        subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False
    return dst.exists() and dst.stat().st_size > 20000


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((IMG / "manifest.json").read_text(encoding="utf-8"))
    CARD = {"level_card", "topic_card"}
    body = [s["id"] for s in scenes if (s.get("visual") or {}).get("type") not in CARD and s["id"] in man]
    body.sort(key=lambda sid: al.get(sid, {}).get("start", 0))

    g = defaultdict(list)
    for sid in body:
        h = md5f(man[sid].get("path"))
        if h:
            g[h].append(sid)
    groups = [sorted(v, key=lambda s: al.get(s, {}).get("start", 0)) for v in g.values() if len(v) > 1]

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[A.PARALLAX_VIDEO_TRACK_IDX]
    clip_at = {}
    for i in range(v3.clips.numItems):
        clip_at.setdefault(round(cstart(v3.clips[i]), 1), i)

    def find_clip(start):
        for d in (0.0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3):
            idx = clip_at.get(round(start + d, 1))
            if idx is not None:
                return v3.clips[idx]
        return None

    done = fail = skip = 0
    for grp in groups:
        src = man[grp[0]].get("path")
        srcname = (man[grp[0]].get("query") or "").lower()
        # чисто чёрное/статик — сдвиг не поможет, пропускаем (незаметно на глаз)
        if any(w in srcname for w in ("black screen", "static", "glitch")):
            skip += len(grp) - 1; continue
        is_img = Path(src).suffix.lower() in IMG_EXT
        dur = 0.0 if is_img else probe_dur(src)
        for oc, sid in enumerate(grp[1:]):
            slot = max(0.6, al.get(sid, {}).get("end", 0) - al.get(sid, {}).get("start", 0))
            off = OFFSETS[oc % len(OFFSETS)]
            if is_img:
                flip = (oc % 2 == 1)                          # картинка: зеркало через раз + разный кроп
            else:
                flip = dur < (off + 1.5) or oc >= len(OFFSETS)  # видео коротко → зеркало
                if dur < off + 0.5:
                    off = max(0.0, dur * 0.4)
            dst = TRIMMED / f"{sid}_dd2.mp4"
            if not recut(src, dst, slot, off, flip, oc):
                print(f"  ✗ recut {sid}"); fail += 1; continue
            clip = find_clip(al.get(sid, {}).get("start", -99))
            if clip is None:
                print(f"  ✗ клип {sid} @ {al.get(sid,{}).get('start')}"); fail += 1; continue
            try:
                clip.projectItem.changeMediaPath(str(dst.resolve()), True)
                done += 1
                print(f"  ✓ {sid} off={off:.1f}{' flip' if flip else ''}", flush=True)
            except Exception as e:
                print(f"  ✗ swap {sid}: {str(e)[:45]}"); fail += 1

    pymiere.objects.app.project.save()
    print(f"\nпересобрано {done}, пропущено (чёрное/статик) {skip}, ошибок {fail}; сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
