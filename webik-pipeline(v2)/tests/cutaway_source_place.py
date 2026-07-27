"""Качает cutaway-клипы (кино/мульт/мем/гифка) с YouTube по запросам режиссёра,
нормализует в 1920x1080 (размытый фон-заливка, без обрезки лиц, БЕЗ звука),
ставит full-frame на V7 в выбранное время. Голос A1 продолжает играть.

Надёжная качалка: search → select → ПОЛНОЕ скачивание (download_full_video) →
trim. Секционную качалку (download_ranges) НЕ используем — она на части видео
отдаёт битый огрызок и ffmpeg trim падает.

Демо: читает <project>/cutaways.json (от cutaway_director.py).
Идемпотентно по assets/cutaways/<scene_id>.mp4 (кэш).
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.stocks.youtube_search import search_candidates
from services.stocks.youtube_clipper import download_full_video, trim_clip
from services.premiere_template.timeline_ops import import_media
from services.llm.claude import ClaudeService
from tests.assemble_iceberg_test import apply_dip_to_black_fade

# титулы-стоп-слова: зелёный экран/шаблоны/туториалы/нарезки — НЕ сама сценка
BAD_TITLE = ("green screen", "greenscreen", "green-screen", "chroma", "template",
             "tutorial", "how to make", "download", "no copyright", "copyright free",
             "free to use", "overlay", "footage pack", "10 hour", "1 hour")
_svc = None

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
OUT = (PROJECT / "assets" / "cutaways").resolve()
CACHE = (PROJECT / "assets" / "_cutaway_cache").resolve()
CUT_TRACK = 6  # V7 (свободна, над телом; режиссёр обходил графику V8)
FADE = 0.45    # сек fade-in/out — плавный кроссфейд с нижним слоем (не резкий щелчок)
FFMPEG = "ffmpeg"


def llm_choose(fact: str, idea: str, query: str, cands: list):
    """LLM выбирает клип, который РЕАЛЬНО является этой сценкой/мемом (не гринскрин/
    не обзор/не нарезка). Возвращает index или 0 при сбое."""
    global _svc
    if _svc is None:
        _svc = ClaudeService()
    lines = []
    for i, c in enumerate(cands):
        d = c.get("duration")
        lines.append(f"[{i}] {c.get('title','')} | канал {c.get('channel','')} | "
                     f"{int(d) if d else '?'}с | {c.get('view_count') or '?'} просм.")
    prompt = (
        f"Выбираешь КОРОТКИЙ клип-вставку (мем / сценка из фильма / кадр из мультика) "
        f"для ироничного cutaway в ролике.\n\n"
        f"Момент закадра: {fact}\nИдея вставки: {idea}\nЗапрос: {query}\n\n"
        f"КАНДИДАТЫ:\n" + "\n".join(lines) + "\n\n"
        f"Выбери ОДИН, который РЕАЛЬНО является этой сценкой/мемом и хорош как вставка:\n"
        f"- это сама сценка/мем (НЕ обзор, НЕ реакция на реакцию, НЕ нарезка «10 мемов», НЕ туториал);\n"
        f"- НЕ зелёный экран и НЕ шаблон для монтажа;\n- короткий, по делу.\n"
        f'Ответь СТРОГО JSON: {{"index": <0..{len(cands)-1}>, "reason": "<кратко>"}}'
    )
    try:
        data = _svc.call_json(prompt, max_tokens=300, temperature=0.0)
        idx = int(data.get("index", 0))
        if 0 <= idx < len(cands):
            print(f"    LLM: [{idx}] {data.get('reason','')[:60]}")
            return idx
    except Exception as e:
        print(f"    LLM-пик сбой ({str(e)[:80]}) — беру самый короткий")
    return 0


def window_for(dur_total: float, want: float):
    """Окно внутри клипа: короткий клип = вся сценка почти с начала."""
    if dur_total and dur_total <= want + 6:
        cs = min(0.4, max(0.0, dur_total - want) / 2)
        ce = min(dur_total - 0.05, cs + want)
        if ce - cs < 2.0:
            cs, ce = 0.0, min(dur_total, want)
        return cs, ce
    return 1.0, 1.0 + want


def fetch_robust(query: str, dur: float, tag: str, fact: str = "", idea: str = ""):
    """search → фильтр junk → LLM-выбор по смыслу → полное скачивание → trim."""
    cands = [c for c in search_candidates(query, n=8) if c.get("url")]
    if not cands:
        print("    ytsearch пусто"); return None
    good = [c for c in cands if not any(b in (c.get("title", "").lower()) for b in BAD_TITLE)]
    pool = good or cands
    # приоритет коротким релевантным (дедиц. клип сценки, а не часовой ролик)
    pool.sort(key=lambda c: (abs((c.get("duration") or 999) - (dur + 3))))
    pool = pool[:6]
    idx = llm_choose(fact, idea, query, pool)
    c = pool[idx]
    cs, ce = window_for(c.get("duration") or 0, dur)
    print(f"    выбран: {c['title'][:52]} [{cs:.1f}-{ce:.1f}]")
    full = download_full_video(c["url"], CACHE)
    if full is None:
        print("    полное скачивание не вышло"); return None
    raw = CACHE / f"{tag}_trim.mp4"
    if raw.exists():
        raw.unlink()
    return trim_clip(full, cs, ce, raw)


def normalize(src: Path, dst: Path, dur: float) -> bool:
    """Full-frame 1920x1080: размытый фон + вписанный фронт по центру, без звука.
    Выход СРАЗУ в DNxHR SQ .mov (монтажный интра-кодек) — Premiere играет плавно
    даже с наложением/фейдом (H.264 long-GOP дёргался). fps=30 → CFR."""
    if dst.exists() and dst.stat().st_size > 5000:
        return True
    vf = (
        "[0:v]fps=30,split=2[bg][fg];"
        "[bg]scale=1920:1080:force_original_aspect_ratio=increase,"
        "crop=1920:1080,boxblur=24:2,eq=brightness=-0.06[bgb];"
        "[fg]scale=1920:1080:force_original_aspect_ratio=decrease[fgs];"
        "[bgb][fgs]overlay=(W-w)/2:(H-h)/2,format=yuv422p[v]"
    )
    cmd = [
        FFMPEG, "-y", "-loglevel", "error", "-t", f"{dur:.2f}", "-i", str(src),
        "-filter_complex", vf, "-map", "[v]", "-an",
        "-r", "30", "-vsync", "cfr", "-c:v", "dnxhd", "-profile:v", "dnxhr_sq",
        "-t", f"{dur:.2f}", str(dst),
    ]
    try:
        subprocess.run(cmd, check=True)
        return dst.exists() and dst.stat().st_size > 5000
    except Exception as e:
        print(f"    ffmpeg normalize упал: {str(e)[:140]}")
        return False


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)
    cuts = json.loads((PROJECT / "cutaways.json").read_text(encoding="utf-8"))["cutaways"]
    print(f"вставок к обработке: {len(cuts)}")

    seq = pymiere.objects.app.project.activeSequence
    v7 = seq.videoTracks[CUT_TRACK]
    v8 = seq.videoTracks[7]
    gfx = [(c.start.seconds, c.end.seconds) for c in v8.clips]

    # чистим старую V7 (вставки прошлого прогона) + старые нормализации
    for cl in reversed(list(v7.clips)):
        cl.remove(False, False)
    for f in list(OUT.glob("cutaway_*.mp4")) + list(OUT.glob("cutaway_*.mov")):
        f.unlink()
    print("старые V7-вставки и нормализации очищены")

    ready = []
    for i, c in enumerate(cuts, 1):
        sid = c["scene_id"]; q = c.get("yt_query", ""); dur = float(c.get("duration_sec", 7.0))
        dst = OUT / f"cutaway_{sid}.mov"
        print(f"\n[{i}/{len(cuts)}] {sid} @ {c['abs_start']}s · {c['type']} · '{q}'")
        if not dst.exists():
            raw = fetch_robust(q, dur, f"cutaway_{sid}",
                               fact=c.get("narration_snippet", ""), idea=c.get("idea", ""))
            if raw is None or not Path(raw).exists():
                print("    не скачалось — пропуск"); continue
            if not normalize(Path(raw), dst, dur):
                continue
        else:
            print("    кэш есть")
        c["clip_path"] = str(dst)
        ready.append(c)

    print(f"\n=== расстановка {len(ready)} на V7 ===")
    placed = 0
    for c in ready:
        at = float(c["abs_start"])
        if any(gs < at + c["duration_sec"] and ge > at for gs, ge in gfx):
            print(f"    ! {c['scene_id']} @ {at}s пересекает графику V8 (ставлю под ней)")
        item = import_media(Path(c["clip_path"]))
        if item is None:
            print(f"    import упал: {c['clip_path']}"); continue
        try:
            v7.overwriteClip(item, time_from_seconds(round(at, 2)))
            placed += 1
            print(f"    ✓ {c['scene_id']} @ {at}s")
        except Exception as e:
            print(f"    overwrite упал: {str(e)[:120]}")

    # плавный fade-in/out на КАЖДОЙ вставке V7 (кроссфейд с нижним слоем — не щелчок)
    faded = 0
    for cl in v7.clips:
        if apply_dip_to_black_fade(cl, FADE, FADE):
            faded += 1
    print(f"фейды применены: {faded}/{v7.clips.numItems}")

    pymiere.objects.app.project.save()
    print(f"\nПОСТАВЛЕНО {placed}/{len(cuts)} cutaway на V7 (+fade {FADE}s), проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
