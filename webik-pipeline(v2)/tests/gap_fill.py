"""Заполняет ЧЁРНЫЕ ДЫРЫ тела V3 (пре-существующие провалы сборки) реальным
архивным видео по теме сцены. LLM по закадру каждой дыры даёт архивный
поисковый запрос (реальный человек/событие/место), качаем через архивную
качалку (youtube_search + clip_llm_pick, заточены на хронику, не обзоры),
нормализуем в DNxHR ровно на длину дыры.

БЕЗ Premiere (качаем независимо). Расстановку делает gap_fill_place.py.
Файлы: assets/cutaways/gapfill_{scene}_{int(start)}.mov
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.llm.claude import ClaudeService
from tests.cutaway_source_place import normalize, fetch_robust, OUT, PROJECT


def gen_queries(gaps):
    """Один LLM-вызов: по закадру каждой дыры → архивный поисковый запрос."""
    svc = ClaudeService()
    lines = []
    for i, g in enumerate(gaps):
        lines.append(f"[{i}] {g['voiceover'][:200]}")
    prompt = (
        "Для документального ролика про секты/культы нужно заполнить пустые места "
        "РЕАЛЬНЫМ архивным видео (хроника, новости, съёмка реального человека/события/места).\n\n"
        "Ниже закадр для каждого места. Для КАЖДОГО дай поисковый запрос на YouTube, "
        "который найдёт РЕАЛЬНУЮ хронику по теме (имя человека, событие, место — как в тексте). "
        "Русский или английский, как лучше найдётся реальное. НЕ киносцена, НЕ мем — реальные кадры.\n"
        "Примеры: 'Пётр Кузнецов пензенские затворники секта хроника', 'Grigory Grabovoi court trial', "
        "'Kanungu Uganda cult fire 2000 news'.\n\n"
        + "\n".join(lines) +
        f'\n\nОтветь СТРОГО JSON-массивом из {len(gaps)} строк-запросов по порядку индексов, без пояснений.'
    )
    try:
        qs = svc.call_json(prompt, max_tokens=2000, temperature=0.4)
        if isinstance(qs, list) and len(qs) == len(gaps):
            return [str(x) for x in qs]
    except Exception as e:
        print(f"LLM-запросы упали: {str(e)[:120]}")
    # фолбэк: первые слова закадра
    return [g['voiceover'][:50] for g in gaps]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    gaps = json.loads((PROJECT / "gaps.json").read_text(encoding="utf-8"))
    print(f"дыр к заполнению: {len(gaps)}")
    queries = gen_queries(gaps)
    ok = 0
    for i, (g, q) in enumerate(zip(gaps, queries), 1):
        sid = g["scene_id"]; dur = float(g["dur"])
        tag = f"gapfill_{sid}_{int(float(g['start']))}"
        dst = OUT / f"{tag}.mov"
        print(f"\n[{i}/{len(gaps)}] {sid} ({dur:.1f}с) '{q}'", flush=True)
        if dst.exists() and dst.stat().st_size > 5000:
            print("    готов (кэш)"); ok += 1; continue
        # быстрый путь: fetch_robust (search+download, БЕЗ per-candidate деталей,
        # с socket_timeout) — не виснет как auto_archive_clip
        raw = fetch_robust(q, dur, tag, fact=g["voiceover"][:160],
                           idea="реальная хроника/съёмка по теме (не киносцена)")
        if raw is None or not Path(raw).exists():
            print("    не нашлось — пропуск"); continue
        if normalize(Path(raw), dst, dur):
            ok += 1; print(f"    ✓ {dst.name}")
    print(f"\nготово {ok}/{len(gaps)} gapfill .mov")
    return 0


if __name__ == "__main__":
    sys.exit(main())
