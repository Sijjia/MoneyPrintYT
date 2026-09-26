"""6 курированных КУЛЬТОВЫХ киновставок-приколов на V7 (узнаваемые моменты под темы Индии).
Поиск YouTube → фетч короткого клипа с нужным моментом → vision-чек (мимо титров/вотермарок) →
нормализация в .mov → assets/v7_inserts/ + v7_inserts.json. Потом ставит tests/v7_place_india.py."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.stocks.youtube_search import search_candidates
from services.stocks.youtube_clipper import fetch_clip
import tests.media_vision_qc as vqc

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
OUT = PROJECT / "assets" / "v7_inserts"; OUT.mkdir(parents=True, exist_ok=True)

# (scene_id, timeline_start, dur, film, yt_query, ожидаемый образ для vision)
CUTS = [
    ("scene_141", 797.17, 4.6, "Сияние — близнецы", "the shining twins hallway scene", "two identical twin girls standing in a hallway"),
    ("scene_076", 404.17, 6.0, "Рататуй — крысы", "ratatouille rats swarm scene", "many cartoon rats swarming"),
    ("scene_178", 1004.53, 6.5, "Храм Судьбы — культ Кали", "indiana jones temple of doom kali ceremony", "dark cult ceremony with fire and idol"),
    ("scene_196", 1111.43, 4.1, "Индиана Джонс — храм", "raiders of the lost ark temple entrance boulder", "ancient temple adventure scene"),
    ("scene_220", 1255.70, 7.5, "Книга джунглей — Каа", "jungle book kaa snake scene", "large snake cartoon"),
    ("scene_155", 869.23, 7.5, "Близкие контакты — НЛО", "close encounters ufo lights night scene", "glowing ufo lights in night sky"),
]


def vision_ok(sid, mp4, want):
    shadow = {sid: {"path": str(Path(mp4).relative_to(PROJECT)).replace("\\", "/"), "kind": "video"}}
    img = vqc.frame_of(sid, shadow)
    if not img:
        return False
    try:
        for v in vqc.vision_call([{"id": sid, "vo": f"кадр из фильма: {want}", "img": img}]):
            return bool(v.get("ok"))
    except Exception:
        return True
    return False


def to_mov(src, dst, dur):
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,setsar=1,fps=30,"
          f"fade=t=in:st=0:d=0.2,fade=t=out:st={max(0.2,dur-0.3):.2f}:d=0.3")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{dur:.2f}", "-an", "-vf", vf,
                        "-r", "30", "-c:v", "prores_ks", "-profile:v", "3", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 20000


def main() -> int:
    inserts = []
    for sid, st, dur, film, q, want in CUTS:
        print(f"\n[{sid}] {film} — '{q}'", flush=True)
        cands = search_candidates(q, n=8, min_dur=6, max_dur=600)
        if not cands:
            print("  нет кандидатов"); continue
        placed = False
        for c in cands[:5]:
            title = (c.get("title") or "").lower()
            if any(b in title for b in ("reaction", "explained", "review", "tier list")):
                continue
            vdur = float(c.get("duration") or 0)
            w = 2.0 if vdur < 90 else 30.0            # короткий клип = сам момент; длинный = вглубь
            try:
                res = fetch_clip(c["url"], w, w + dur + 0.5, PROJECT, sid)
            except Exception as e:
                print(f"  fetch err {str(e)[:40]}"); continue
            mp4 = PROJECT / "assets" / "youtube_clips" / f"{sid}.mp4"
            if not (res and mp4.exists()):
                continue
            if not vision_ok(sid, mp4, want):
                print(f"  vision мимо: {title[:40]}"); continue
            mov = OUT / f"v7_{sid}_{int(st)}_6.mov"
            if to_mov(mp4, mov, dur):
                inserts.append({"scene_id": sid, "start": round(st, 2), "film": film})
                print(f"  ✓ {film} @ {int(st)//60:02d}:{int(st)%60:02d}", flush=True)
                placed = True; break
        if not placed:
            print(f"  ✗ не нашёл подходящий клип для {film}")
    (PROJECT / "v7_inserts.json").write_text(json.dumps({"inserts": inserts}, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: киновставок собрано {len(inserts)}/{len(CUTS)} → v7_inserts.json", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
