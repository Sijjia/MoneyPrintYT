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
        "Ты — режиссёр монтажа YouTube-канала в док-стиле. Твоя задача — подбирать "
        "ИЛЛЮСТРАТИВНЫЕ вставки из фильмов и мультиков: короткий отрывок (5-10с), который "
        "ВИЗУАЛЬНО ПОКАЗЫВАЕТ то, о чём говорит закадр — конкретный объект, действие или образ. "
        "Это НЕ реакшн-мем и НЕ ирония, а остроумная ВИДЕО-ИЛЛЮСТРАЦИЯ по картинке: "
        "слышим про штрихкоды — показываем сцену со штрихкодом (тату Агента 47 в «Хитмане»); "
        "слышим «несли ему деньги» — показываем, как в кино/мультике тащат мешок денег."
    )
    prompt = f"""Ролик: «Айсберг религиозного террора» — про секты, культы, религиозных мошенников и фанатиков. Тема ТЯЖЁЛАЯ.

Ниже закадр с таймкодами [мм:сс], id сцены, уровнем айсберга (L) и текстом. Пометка [ГРАФИКА] = там идёт инфографика.

ЗАДАЧА: выбери РОВНО {N_MIN}-{N_MAX} мест, где в закадре есть КОНКРЕТНЫЙ ВИЗУАЛЬНЫЙ образ
(объект, действие, сцена), который можно ЭФФЕКТНО ПРОИЛЛЮСТРИРОВАТЬ отрывком из фильма/мультика.

ГЛАВНЫЙ ПРИНЦИП: клип ПОКАЗЫВАЕТ то, о чём речь (буквально или узнаваемым киношным образом), а НЕ шутит.
Примеры совпадения «слово → картинка»:
- «штрихкоды / печать дьявола на товарах» → сцена со штрихкодом (Hitman — тату Агента 47; сканер на кассе)
- «люди несли ему деньги» → тащат мешок/чемодан денег (фильм/мультик)
- «объявил себя богом» → явление божества / «бог» из кино
- «увёл людей в лес / в подземелье» → толпа идёт за лидером; вход в бункер
- «обещал конец света» → апокалиптический кадр из кино
- «воскрешение мёртвых» → человек восстаёт/оживает в кино
Бери ЯРКИЙ, УЗНАВАЕМЫЙ момент, который визуально бьёт точно в образ.

ПРАВИЛА:
1. Ставь ТОЛЬКО туда, где есть чёткий визуальный образ (объект/действие), который классно показать картинкой.
   Нет яркого образа — пропусти сцену.
2. СТРОГО НЕЛЬЗЯ иллюстрировать убийство / трупы / массовое захоронение / пытки / увечья / суицид / гибель
   (особенно детей); саму вставку с кровью/резнёй НЕ бери. На трагедию/жертв — пропусти, найди соседний образ.
3. НЕ выбирай сцены с пометкой [ГРАФИКА].
4. Распредели по ролику (не кучей).

Для каждой вставки верни объект:
- scene_id: id сцены из списка
- at_offset_sec: сколько секунд ОТ НАЧАЛА этой сцены поставить (обычно 0.3-1.5)
- narration_snippet: точная фраза закадра
- visual_element: какой ОБРАЗ иллюстрируем (по-русски коротко: «штрихкод», «мешок денег», «толпа за лидером»)
- type: "movie" | "cartoon"
- idea: по-русски какой фильм/мультик и какая сцена показывает этот образ
- yt_query: КОНКРЕТНЫЙ англ. запрос на ИМЕННО ЭТУ сцену (источник + что показано + "scene"/"clip").
  НЕЛЬЗЯ "template", "green screen", "greenscreen", "chroma".
  Примеры: "Hitman Agent 47 barcode tattoo scene", "cartoon carrying huge sack of money scene",
  "movie cult followers walking into forest scene", "apocalypse end of the world movie scene"
- duration_sec: 5-10
- why: 1 фраза — как визуально попадает в образ

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
