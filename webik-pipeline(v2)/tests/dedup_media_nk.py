"""Устранить ВИЗУАЛЬНЫЕ повторы на V3 (одна картинка под разными именами).
Для каждой группы одинаковых картинок оставляем ПЕРВОЕ вхождение, остальные меняем
на УНИКАЛЬНОЕ тематическое медиа по запросу ИМЕННО той сцены:
  1) Wikimedia-фото (дедуп по контент-хешу, чтобы не вернуть то же самое) → PhotoZoom
  2) если разных фото нет — тематическое Pexels-видео (движение тоже ломает повтор)
Глобально держим set использованных хешей → ничего не повторяется.
"""
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.stocks.wikimedia import WikimediaClient
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
PHOTOS = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
VID = PROJECT / "assets" / "video_stock"
REMOTION = ROOT / "remotion"
tps = 254016000000


def mmss(t):
    return f"{int(t)//60:02d}:{int(t)%60:02d}"


def md5(b):
    return hashlib.md5(b).hexdigest()[:12]


def md5f(p):
    try:
        return md5(Path(p).read_bytes())
    except Exception:
        return None


def source_for(path):
    b = os.path.basename(path)
    m = re.match(r"(scene_\d+)(?:_[a-z0-9]+)?_pz\.mp4$", b) or re.match(r"(scene_\d+)_pz\.mp4$", b)
    if m:
        for f in PHOTOS.glob(m.group(1) + ".*"):
            return str(f)
    return path


def clip_start(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def render_photozoom(sid, img_path, dur, direction):
    """Копирует картинку в public/photos/{sid}_d{suffix}, рендерит PhotoZoom, отдаёт mp4."""
    suffix = Path(img_path).suffix or ".jpg"
    pub = PHOTOS / f"{sid}_d{suffix}"
    shutil.copy(img_path, pub)
    props = REMOTION / f"_pz_{sid}_d.json"
    props.write_text(json.dumps({"img": f"photos/{sid}_d{suffix}", "dir": direction,
                                 "durationInFrames": int((dur + 0.5) * 30)}), encoding="utf-8")
    outp = OUT / f"{sid}_d_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("    ✗ render:", (r.stderr or "")[-160:]); return None
    return outp


def find_unique_still(wm, queries, used_hashes, tmp):
    """Ищет по Wikimedia фото, чьего хеша ещё нет в used_hashes. Отдаёт (path, hash)."""
    for q in queries:
        if not q:
            continue
        try:
            hits = wm.search_images(q, limit=12, min_width=1000)
        except Exception:
            hits = []
        for j, hit in enumerate(hits):
            o = tmp / f"cand_{md5(q.encode())}_{j}.jpg"
            try:
                wm.download(hit, o)
                hsh = md5f(o)
            except Exception:
                continue
            if hsh and hsh not in used_hashes:
                return o, hsh
    return None, None


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    by_id = {s["id"]: s for s in scenes}
    # интервалы сцен по времени
    ivals = sorted(((al[sid]["start"], al[sid]["end"], sid) for sid in al if sid in by_id), key=lambda x: x[0])

    def scene_at(t):
        best = None
        for st, en, sid in ivals:
            if st - 0.05 <= t < en + 0.05:
                return sid
            if st <= t:
                best = sid
        return best

    wm = WikimediaClient()
    px = PexelsVideosClient()
    OUT.mkdir(parents=True, exist_ok=True); VID.mkdir(parents=True, exist_ok=True)
    PHOTOS.mkdir(parents=True, exist_ok=True)

    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]

    # собрать клипы: idx, start, source-hash
    clips = []
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        try:
            path = c.projectItem.getMediaPath()
        except Exception:
            continue
        src = source_for(path)
        clips.append({"idx": i, "start": clip_start(c), "hash": md5f(src), "src": src})

    groups = defaultdict(list)
    for cl in clips:
        if cl["hash"]:
            groups[cl["hash"]].append(cl)

    used = set(groups.keys())  # все текущие хеши заняты
    # цели: 2-е и далее вхождения (по времени), первое оставляем
    targets = []
    for hsh, items in groups.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda x: x["start"])
        for cl in items[1:]:
            targets.append(cl)
    targets.sort(key=lambda x: x["start"])
    print(f"клипов V3: {len(clips)} | групп-повторов: {sum(1 for v in groups.values() if len(v)>1)} | "
          f"к замене: {len(targets)}\n")

    tmp = Path(tempfile.mkdtemp())
    done_still = done_vid = fail = 0
    for k, cl in enumerate(targets):
        idx, t = cl["idx"], cl["start"]
        sid = scene_at(t)
        s = by_id.get(sid, {})
        vis = s.get("visual", {}) if isinstance(s, dict) else {}
        queries = [vis.get("search_query"), vis.get("fallback_query")]
        dur = 3.2
        a = al.get(sid)
        if a:
            dur = max(2.5, round(a["end"] - a["start"], 1))
        label = f"[{k+1}/{len(targets)}] {mmss(t)} idx={idx} {sid}"
        # 1) уникальное фото
        img, hsh = find_unique_still(wm, queries, used, tmp)
        newmedia = None
        if img:
            outp = render_photozoom(sid, img, dur, "in" if k % 2 else "out")
            if outp:
                newmedia = outp; used.add(hsh); done_still += 1
                print(f"  ✓ФОТО {label}  q='{(queries[0] or queries[1] or '')[:40]}'")
        # 2) fallback: тематическое видео
        if newmedia is None:
            for qi, q in enumerate([queries[0], queries[1], s.get("voiceover", "")[:60]]):
                if not q:
                    continue
                try:
                    o = VID / f"{sid}_d.mp4"
                    if px.search_and_download(q, o, index=(k % 3)) and o.stat().st_size > 20000:
                        hsh = md5f(o)
                        if hsh and hsh not in used:
                            newmedia = o; used.add(hsh); done_vid += 1
                            print(f"  ✓ВИДЕО {label}  q='{q[:40]}'")
                            break
                except Exception:
                    continue
        if newmedia is None:
            fail += 1
            print(f"  ✗ {label}  — не нашёл уникального медиа")
            continue
        try:
            v3.clips[idx].projectItem.changeMediaPath(str(Path(newmedia).resolve()), True)
        except Exception as e:
            fail += 1; print(f"  ✗ swap idx={idx}: {str(e)[:80]}")

    pymiere.objects.app.project.save()
    print(f"\nготово: фото={done_still} видео={done_vid} провал={fail}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
