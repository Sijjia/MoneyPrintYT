"""Режиссёр cutaway-вставок («приколы»): LLM (sonnet) читает закадр с РЕАЛЬНЫМИ
таймкодами из живого Premiere и выбирает 5-7 УМЕСТНЫХ мест для короткой вставки
(реакция из фильма / кадр из мультика / мем / реакшн-гифка).

ЖЁСТКО: только лёгкие/абсурдные/мета/переходные моменты; НИКОГДА над убийствами/
пытками/насилием/смертями/жертвами; обходить сцены с графикой (V8).

Время — из живого Premiere (V3 = тело), чтобы не попасть на ~19.7с расхождение
статичного alignment с ручными подрезками Айдара.

Вывод: <project>/cutaways.json — [{scene_id, at_offset_sec, narration_snippet,
type, idea, yt_query, duration_sec, why}]
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.llm.claude import ClaudeService

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
N_MIN, N_MAX = 16, 24


def mmss(s: float) -> str:
    return f"{int(s)//60:02d}:{int(s)%60:02d}"


def sid_from_name(name: str):
    m = re.search(r"scene_(\d+)", name)
    return f"scene_{m.group(1)}" if m else None


def main() -> int:
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]  # тело
    v8 = seq.videoTracks[7]  # графика
    gfx = [(c.start.seconds, c.end.seconds) for c in v8.clips]

    def has_gfx(a, b):
        return any(gs < b and ge > a for gs, ge in gfx)

    # scene_id -> текст/mood/level
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    items = sc if isinstance(sc, list) else sc["scenes"]
    meta = {s["id"]: s for s in items}

    lines, placed = [], []
    for c in v3.clips:
        sid = sid_from_name(c.name)
        if not sid or sid not in meta:
            continue
        m = meta[sid]
        vo = (m.get("voiceover") or "").strip().replace("\n", " ")
        if not vo:
            continue
        a, b = c.start.seconds, c.end.seconds
        flag = " [ГРАФИКА]" if has_gfx(a, b) else ""
        lvl = m.get("level", "")
        lines.append(f"[{mmss(a)}] {sid} (L{lvl}){flag}: {vo}")
        placed.append((sid, a, b))

    transcript = "\n".join(lines)

    system = (
        "Ты — режиссёр монтажа ДЕРЗКОГО молодёжного русского YouTube-канала в док-стиле про "
        "тёмные темы. Твоя фишка — оживлять ролик хайповыми вставками-приколами (cutaway 5-10с): "
        "сценка из фильма, кусок из мультика, вирусный мем или мем-сценка, которая ЖЁСТКО и "
        "иронично комментирует закадр. Не бойся ЧЁРНОГО ЮМОРА и вирусных/брейнрот-мемов — "
        "аудитория молодая, ценит дерзость и панч. Это резко поднимает удержание и хайп."
    )
    prompt = f"""Ролик: «Айсберг религиозного террора» — про секты, культы, религиозных мошенников и фанатиков. Тема ТЯЖЁЛАЯ.

Ниже закадр с таймкодами [мм:сс], id сцены, уровнем айсберга (L) и текстом. Пометка [ГРАФИКА] = там идёт инфографика.

ЗАДАЧА: выбери РОВНО {N_MIN}-{N_MAX} ЛУЧШИХ мест для ХАЙПОВОЙ вставки-прикола.

ПРАВИЛА:
1. Вставки на АБСУРДНЫЕ / ИРОНИЧНЫЕ / ДЕРЗКИЕ / МЕТА / ПЕРЕХОДНЫЕ моменты:
   абсурд мошенников (воскрешения за деньги, «бог» из соседнего подъезда, нелепые обещания),
   ирония разоблачения, дикость ситуации, риторические «вы серьёзно?!», хук, смена темы.
2. ЧЁРНЫЙ ЮМОР РАЗРЕШЁН и приветствуется — но это ирония над АБСУРДОМ и над МОШЕННИКАМИ/ЗЛОДЕЯМИ,
   над лицемерием и дикостью происходящего. СТРОГО НЕЛЬЗЯ ставить прикол на момент, где ОПИСЫВАЮТ
   убийство / трупы / массовое захоронение / пытки / увечья / самоубийство / гибель (особенно детей) —
   ДАЖЕ «для разрядки иронией». Это издёвка над жертвами = бан YouTube. И саму вставку с кровью/резнёй
   (напр. бойня, расчленёнка) НЕ бери. Юмор — над схемой развода и лицемерием жулика, НЕ над моментом,
   когда гибнут/находят людей. Если момент = трагедия/жертвы — пропусти, найди соседний абсурдный.
3. НЕ выбирай сцены с пометкой [ГРАФИКА].
4. Распредели по ролику (не кучей).

Для каждой вставки верни объект:
- scene_id: id сцены из списка
- at_offset_sec: сколько секунд ОТ НАЧАЛА этой сцены поставить (обычно 0.3-1.5)
- narration_snippet: точная фраза закадра, которую комментируем
- type: "movie" | "cartoon" | "meme"
- idea: по-русски что показать (конкретно: какой фильм/мультик/мем и панч)
- yt_query: КОНКРЕТНЫЙ англ. запрос для YouTube — назови ИСТОЧНИК (фильм/сериал/мультик) и добавь
  "scene"/"clip"/"original". Бери РЕАЛЬНУЮ законченную сценку 5-10с.
  НЕЛЬЗЯ слова "template", "green screen", "greenscreen", "chroma" — они дают зелёный шаблон, не сценку!
  Примеры: "Michael Scott no god no please scene the office", "Futurama Fry take my money scene",
  "Despicable Me Gru plan presentation scene", "Monty Python black knight tis but a scratch scene"
- duration_sec: 5-10 (можно до 12). Бери клипы, которые РЕАЛЬНО тянут этот хронометраж
  (сценки из фильмов/мультов, законченные мем-сценки), НЕ 2-секундные гифки-блипы.
- why: 1 фраза почему уместно и хайпово

Верни ТОЛЬКО JSON-массив, без пояснений.

ЗАКАДР:
{transcript}"""

    print(f"сцен в закадре: {len(placed)} | графика-диапазонов: {len(gfx)}")
    print("зову sonnet-режиссёра...")
    llm = ClaudeService()  # LLM_MODEL = sonnet 4.5
    cuts = llm.call_json(prompt, max_tokens=6000, temperature=0.9, system=system)
    if isinstance(cuts, dict):
        cuts = cuts.get("cutaways") or cuts.get("items") or []

    # привяжем реальное абсолютное время
    tstart = {sid: a for sid, a, b in placed}
    tend = {sid: b for sid, a, b in placed}
    clean = []
    for c in cuts:
        sid = c.get("scene_id")
        if sid not in tstart:
            continue
        off = max(0.0, float(c.get("at_offset_sec", 0.5)))
        at = tstart[sid] + off
        at = min(at, max(tstart[sid], tend[sid] - 0.5))  # не вылезти за сцену
        c["abs_start"] = round(at, 2)
        c["duration_sec"] = max(5.0, min(12.0, float(c.get("duration_sec", 7.0))))
        clean.append(c)

    out = PROJECT / "cutaways.json"
    out.write_text(json.dumps({"cutaways": clean}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n=== РЕЖИССЁР ВЫБРАЛ {len(clean)} ВСТАВОК ===")
    for c in clean:
        print(f"\n[{mmss(c['abs_start'])}] {c['scene_id']} · {c['type']} · {c['duration_sec']}с")
        print(f"  закадр: «{c.get('narration_snippet','')[:80]}»")
        print(f"  идея:   {c.get('idea','')}")
        print(f"  запрос: {c.get('yt_query','')}")
        print(f"  почему: {c.get('why','')}")
    print(f"\nсохранено → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
