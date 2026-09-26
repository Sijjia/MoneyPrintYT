"""Убирает ВИЗУАЛЬНЫЕ повторы на V3: группирует клипы тела по md5 исходника, в каждой
группе оставляет первый, поздние перекачивает на РАЗНЫЙ футаж того же шоу (вариация
запроса + md5-дедуп против ВСЕХ исходников), пере-нарезает под слот и подменяет клип
на живом таймлайне (changeMediaPath). Требует POT-сервер (4416) + открытый Premiere.
  ../webik-pipeline/.venv/Scripts/python.exe tests/dedup_media_as.py
"""
import json, hashlib, sys, tempfile
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.assemble_as as A
from tests.source_media_dw import fetch_movie
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = A.PROJECT_DIR
VID = PROJECT / "assets" / "video_stock"
IMG = PROJECT / "assets" / "images"
TRIMMED = A.TRIMMED_DIR
tps = 254016000000
TOL = 0.4
TOKENS = ["scene", "clip", "moment", "full episode", "best scene", "compilation",
          "highlights", "different scene", "another clip", "hd part"]


def md5f(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None


def cstart(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((IMG / "manifest.json").read_text(encoding="utf-8"))
    plan_ext = json.loads((PROJECT / "media_plan_dw.json").read_text(encoding="utf-8"))
    CARD = {"level_card", "topic_card"}
    body = [s["id"] for s in scenes if (s.get("visual") or {}).get("type") not in CARD and s["id"] in man]
    body.sort(key=lambda sid: al.get(sid, {}).get("start", 0))

    # группы точных дублей + все занятые хеши
    g = defaultdict(list)
    seen = set()
    for sid in body:
        h = md5f(man[sid].get("path"))
        if h:
            g[h].append(sid); seen.add(h)
    groups = [sorted(v, key=lambda s: al.get(s, {}).get("start", 0)) for v in g.values() if len(v) > 1]
    # ARG-графику не трогаем (source=arg-graphic — уникальна by design)
    to_fix = []
    for grp in groups:
        for sid in grp[1:]:
            if man[sid].get("source") != "arg-graphic":
                to_fix.append(sid)
    print(f"групп дублей: {len(groups)} | клипов к замене: {len(to_fix)}", flush=True)

    # индекс клипов V3 по времени
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

    tmp = Path(tempfile.mkdtemp())
    px = PexelsVideosClient()
    done = fail = 0
    for k, sid in enumerate(to_fix):
        info = plan_ext.get(sid, {})
        base = (info.get("query") or man[sid].get("query") or "Adult Swim").strip()
        fb = (info.get("fallback") or "").strip()
        bucket = info.get("bucket", "movie")
        slot = max(0.6, al.get(sid, {}).get("end", 0) - al.get(sid, {}).get("start", 0))
        newsrc = None
        # пробуем разные вариации запроса, берём первый НОВЫЙ по md5
        variants = [f"{base} {TOKENS[(k + i) % len(TOKENS)]}" for i in range(4)] + ([fb] if fb else [])
        for vi, q in enumerate(variants):
            out = VID / f"{sid}_dd.mp4"
            if bucket == "stock":
                try:
                    if px.search_and_download(q, out, index=(vi % 4)) and out.stat().st_size > 20000:
                        h = md5f(out)
                        if h and h not in seen: seen.add(h); newsrc = out; break
                except Exception: pass
            else:
                for idx in (k + vi * 4, k + vi * 4 + 17):
                    if fetch_movie(q, out, idx, tmp):
                        h = md5f(out)
                        if h and h not in seen: seen.add(h); newsrc = out; break
                if newsrc: break
        if not newsrc:
            print(f"  ✗ {sid}: не нашёл уник. футаж «{base[:35]}»", flush=True); fail += 1; continue
        # пере-нарезка под слот + подмена клипа
        trimmed = TRIMMED / f"{sid}_dd.mp4"
        if not A.pretrim_fill(newsrc, trimmed, slot):
            print(f"  ✗ {sid}: pretrim"); fail += 1; continue
        clip = find_clip(al.get(sid, {}).get("start", -99))
        if clip is None:
            print(f"  ✗ {sid}: клип на V3 не найден @ {al.get(sid,{}).get('start')}"); fail += 1; continue
        try:
            clip.projectItem.changeMediaPath(str(trimmed.resolve()), True)
            man[sid] = {"path": str(newsrc), "query": base, "kind": "video", "source": man[sid].get("source", "youtube-as")}
            done += 1; print(f"  ✓ {sid} ← новый футаж", flush=True)
        except Exception as e:
            print(f"  ✗ {sid}: swap {str(e)[:50]}"); fail += 1

    (IMG / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print(f"\nзаменено {done}, не удалось {fail}; проект сохранён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
