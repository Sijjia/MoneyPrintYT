"""Пересобирает медиа тела V3 для хвоста (сцены 177-190: альбиносы Танзании +
Орден Солнечного Храма) реальным архивом по теме. LLM по закадру → архивный
запрос (тактично: хроника/новости/документалка, БЕЗ жести), fetch_robust →
normalize по длине сцены. БЕЗ Premiere. Расстановку делает tail_media_place.py.
Файлы: assets/tail_media/{scene}_{start}.mov
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.llm.claude import ClaudeService
from tests.cutaway_source_place import fetch_robust, normalize, PROJECT

OUT = (PROJECT / "assets" / "tail_media").resolve()
LO, HI = 177, 190  # диапазон сцен (по номеру)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    sm = json.loads((PROJECT / "scene_map.json").read_text(encoding="utf-8"))
    targets = []
    for s in sm:
        m = re.match(r"scene_(\d+)", s["scene_id"])
        if m and LO <= int(m.group(1)) <= HI and (s.get("vo") or "").strip():
            targets.append(s)
    targets.sort(key=lambda s: s["start"])
    print(f"сцен к пересбору: {len(targets)}")

    svc = ClaudeService()
    lines = [f"[{i}] {s['scene_id']}: {s['vo'][:180]}" for i, s in enumerate(targets)]
    prompt = (
        "Для док-ролика нужно заполнить сцены РЕАЛЬНЫМ архивом по теме (хроника, новости, "
        "документалка, реальные места/люди/события). Темы: охота на альбиносов в Танзании/"
        "Восточной Африке и Орден Солнечного Храма (Швейцария, 1994).\n\n"
        "Для КАЖДОЙ сцены дай поисковый запрос на YouTube, который найдёт РЕАЛЬНУЮ уместную "
        "хронику. ТАКТИЧНО: новости/документалка/awareness, БЕЗ графичной жести (не трупы/"
        "кровь). Русский или английский — как лучше найдётся.\n"
        "Примеры: 'Tanzania albinos attacks BBC documentary', 'albino children Tanzania safe "
        "center news', 'Order of the Solar Temple 1994 Switzerland news archive', "
        "'Ordre du Temple Solaire documentaire'.\n\n"
        + "\n".join(lines) +
        f"\n\nОтветь СТРОГО JSON-массивом из {len(targets)} строк-запросов по порядку индексов."
    )
    try:
        qs = svc.call_json(prompt, max_tokens=2000, temperature=0.4)
        if not (isinstance(qs, list) and len(qs) == len(targets)):
            raise ValueError("bad")
    except Exception as e:
        print(f"LLM-запросы упали ({str(e)[:80]}) — фолбэк по первым словам")
        qs = [s["vo"][:50] for s in targets]

    ok = 0
    for s, q in zip(targets, qs):
        sid = s["scene_id"]; dur = float(s["dur"]); start = int(float(s["start"]))
        tag = f"{sid}_{start}"
        dst = OUT / f"{tag}.mov"
        print(f"\n{sid} @ {start//60}:{start%60:02d} ({dur:.1f}с) '{q}'", flush=True)
        if dst.exists() and dst.stat().st_size > 5000:
            print("    кэш"); ok += 1; continue
        raw = fetch_robust(str(q), dur, f"tail_{tag}", fact=s["vo"][:160],
                           idea="реальная хроника/новости по теме (не киносцена, без жести)")
        if raw is None or not Path(raw).exists():
            print("    не скачалось"); continue
        if normalize(Path(raw), dst, dur):
            ok += 1; print(f"    ✓ {dst.name}")
    print(f"\nготово {ok}/{len(targets)} .mov")
    return 0


if __name__ == "__main__":
    sys.exit(main())
