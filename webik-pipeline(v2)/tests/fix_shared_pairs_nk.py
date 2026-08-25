"""Добить 7 пар, где два клипа делят ОДИН projectItem (changeMediaPath менял оба).
Для ВТОРОГО клипа пары: качаем ДРУГОЕ уникальное фото сцены → рендерим PhotoZoom
РОВНО в длину слота → import_media (новый bin-элемент) → overwriteClip (свой источник).
Так первый клип остаётся с картинкой A, второй получает картинку B."""
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
from services.premiere_template import timeline_ops as T

PROJECT = ROOT / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
PHOTOS = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
REMOTION = ROOT / "remotion"
tps = 254016000000

# запас разнообразных тематических запросов, если по сцене мало разных фото
EXTRA = ["North Korea propaganda poster", "Pyongyang street scene", "North Korea military parade",
         "North Korea countryside village", "DMZ Korea border", "North Korea rural poverty",
         "Kim Il Sung monument", "North Korea soldiers", "Pyongyang architecture",
         "North Korea vintage photo"]


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
    m = re.match(r"(scene_\d+)(?:_[a-z0-9]+)?_pz\.mp4$", b)
    if m:
        for cand in (m.group(1) + "_p2.*", m.group(1) + "_d.*", m.group(1) + ".*"):
            for f in PHOTOS.glob(cand):
                return str(f)
    return path


def cstart(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def cend(c):
    return c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / tps


def find_unique_still(wm, queries, used, tmp):
    for q in queries:
        if not q:
            continue
        try:
            hits = wm.search_images(q, limit=15, min_width=1000)
        except Exception:
            hits = []
        for j, hit in enumerate(hits):
            o = tmp / f"c_{md5(q.encode())}_{j}.jpg"
            try:
                wm.download(hit, o)
                h = md5f(o)
            except Exception:
                continue
            if h and h not in used:
                return o, h
    return None, None


def render_pz_exact(sid, img, frames, direction):
    suffix = Path(img).suffix or ".jpg"
    pub = PHOTOS / f"{sid}_p2{suffix}"
    shutil.copy(img, pub)
    props = REMOTION / f"_pz_{sid}_p2.json"
    props.write_text(json.dumps({"img": f"photos/{sid}_p2{suffix}", "dir": direction,
                                 "durationInFrames": int(frames)}), encoding="utf-8")
    outp = OUT / f"{sid}_p2_pz.mp4"
    r = subprocess.run(f'npx remotion render PhotoZoom "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    props.unlink(missing_ok=True)
    if r.returncode != 0:
        print("    ✗ render:", (r.stderr or "")[-160:]); return None
    return outp


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    by_id = {s["id"]: s for s in scenes}
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
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]

    clips = []
    for i in range(v3.clips.numItems):
        c = v3.clips[i]
        try:
            path = c.projectItem.getMediaPath()
        except Exception:
            continue
        clips.append({"idx": i, "start": cstart(c), "end": cend(c), "hash": md5f(source_for(path))})
    groups = defaultdict(list)
    for cl in clips:
        if cl["hash"]:
            groups[cl["hash"]].append(cl)
    used = set(groups.keys())
    targets = []
    for h, items in groups.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda x: x["start"])
        targets += items[1:]
    targets.sort(key=lambda x: x["start"])
    print(f"пар-повторов: {len([1 for v in groups.values() if len(v)>1])} | вторых клипов к замене: {len(targets)}\n")

    tmp = Path(tempfile.mkdtemp())
    ok = fail = 0
    for k, cl in enumerate(targets):
        idx = cl["idx"]; st = cl["start"]; dur = max(1.5, cl["end"] - cl["start"])
        frames = max(45, round(dur * 30))
        sid = scene_at(st)
        s = by_id.get(sid, {})
        vis = s.get("visual", {}) if isinstance(s, dict) else {}
        queries = [vis.get("search_query"), vis.get("fallback_query")] + EXTRA
        label = f"[{k+1}/{len(targets)}] {mmss(st)} idx={idx} {sid} ({dur:.1f}с)"
        img, h = find_unique_still(wm, queries, used, tmp)
        if not img:
            fail += 1; print(f"  ✗ {label} — нет уникального фото"); continue
        outp = render_pz_exact(sid, img, frames, "in" if k % 2 else "out")
        if not outp:
            fail += 1; continue
        item = T.import_media(outp)
        if item is None:
            fail += 1; print(f"  ✗ {label} — import не удался"); continue
        try:
            T.place_clip(v3, item, st, overwrite=True)
            used.add(h); ok += 1
            print(f"  ✓ {label}  q='{(queries[0] or queries[1] or '')[:36]}'")
        except Exception as e:
            fail += 1; print(f"  ✗ place idx={idx}: {str(e)[:80]}")

    pymiere.objects.app.project.save()
    print(f"\nготово: заменено={ok} провал={fail}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
