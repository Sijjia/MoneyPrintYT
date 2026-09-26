"""Из VTT-транскриптов референс-айсбергов Adult Swim вытаскивает ПУЛ ТЕМ (что заезжено),
с пометкой факт/слух/конспирология. Пишет adultswim_topic_pool.json в scratchpad."""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

S = Path(r"C:\Users\aidar\AppData\Local\Temp\claude\C--Users-aidar-OneDrive--------------automotization-youtube\0a3edf5b-8f55-4b33-a918-972784adb4ef\scratchpad")
VTTS = {"ZeroOmens (108 мин, полный)": S / "ref_2lfR9y_JCnw.en.vtt",
        "BionicPIG (32 мин)": S / "ref_8oRu4mqEstk.en.vtt"}


def clean_vtt(p: Path) -> str:
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    out, seen = [], ""
    for ln in lines:
        if "-->" in ln or ln.strip().isdigit() or ln.startswith("WEBVTT") or ln.startswith("Kind:") \
           or ln.startswith("Language:") or not ln.strip():
            continue
        t = re.sub(r"<[^>]+>", "", ln).strip()          # убрать теги <c>
        if t and t != seen:
            out.append(t); seen = t
    # склейка + грубая дедупликация подряд-повторов слов auto-caption
    txt = " ".join(out)
    return re.sub(r"\s+", " ", txt)


def main() -> int:
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    all_topics = []
    for label, p in VTTS.items():
        if not p.exists():
            print(f"нет {p.name}"); continue
        txt = clean_vtt(p)
        words = txt.split()
        print(f"{label}: ~{len(words)} слов", flush=True)
        CH = 5000
        for i in range(0, len(words), CH):
            chunk = " ".join(words[i:i + CH])
            ask = ("Это часть транскрипта видео-айсберга про Adult Swim (ночной блок Cartoon Network). "
                   "Выпиши ВСЕ отдельные ТЕМЫ/факты/легенды, которые тут упоминаются (шоу, случаи, "
                   "лост-медиа, скандалы, бампы, закулисье, отменённое). Для каждой верни "
                   "{\"topic\": короткое название, \"brief\": 1 фраза сути, "
                   "\"kind\": \"факт|слух|конспирология\"}. Только JSON-массив.\n\nТРАНСКРИПТ:\n" + chunk)
            try:
                res = llm.call_json(ask, max_tokens=4000, temperature=0.2)
                if isinstance(res, list):
                    for r in res:
                        if r.get("topic"): all_topics.append(r)
                print(f"  чанк {i//CH+1}: +{len(res) if isinstance(res,list) else 0}", flush=True)
            except Exception as e:
                print(f"  ✗ {str(e)[:70]}", flush=True)

    # финальная консолидация: дедуп + сортировка
    ask2 = ("Ниже сырой список тем айсберга Adult Svim (с повторами). Сведи в ЧИСТЫЙ пул БЕЗ дублей, "
            "сгруппируй по типу. Для каждой: {\"topic\",\"brief\",\"kind\":\"факт|слух|конспирология\", "
            "\"strength\": 1-5 (насколько интересно+подтверждено для ролика)}. Отсортируй по strength. "
            "Только JSON-массив.\n\n" + json.dumps(all_topics, ensure_ascii=False)[:60000])
    pool = llm.call_json(ask2, max_tokens=14000, temperature=0.3)
    if not isinstance(pool, list): pool = all_topics
    (S / "adultswim_topic_pool.json").write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    facts = [t for t in pool if t.get("kind") == "факт"]
    print(f"\n=== ПУЛ: {len(pool)} тем (сырых {len(all_topics)}) | фактов {len(facts)} ===")
    for t in sorted(pool, key=lambda x: -x.get("strength", 0))[:30]:
        print(f"  [{t.get('strength')}] [{t.get('kind')}] {t.get('topic')}: {(t.get('brief') or '')[:60]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
