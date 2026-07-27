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
N_MIN, N_MAX = 5, 7


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
        "Ты — режиссёр монтажа современного русского YouTube-канала в док-стиле про "
        "тёмные темы. Твоя фишка — точечно оживлять ролик короткими вставками-приколами "
        "(cutaway 1.5-2.5с): реакция из фильма, кадр из мультика, мем или реакшн-гифка, "
        "которая иронично комментирует закадр. Это резко поднимает удержание и динамику."
    )
    prompt = f"""Ролик: «Айсберг религиозного террора» — про секты, культы, религиозных мошенников и фанатиков. Тема ТЯЖЁЛАЯ.

Ниже закадр с таймкодами [мм:сс], id сцены, уровнем айсберга (L) и текстом. Пометка [ГРАФИКА] = там идёт инфографика.

ЗАДАЧА: выбери РОВНО {N_MIN}-{N_MAX} ЛУЧШИХ мест для вставки-прикола.

ЖЁСТКИЕ ПРАВИЛА УМЕСТНОСТИ (нарушение = провал):
1. Вставки ТОЛЬКО на ЛЁГКИЕ / АБСУРДНЫЕ / ИРОНИЧНЫЕ / МЕТА / ПЕРЕХОДНЫЕ моменты:
   абсурд мошенников (воскрешения за деньги, «бог» из соседнего подъезда, нелепые обещания),
   ирония разоблачения, риторические «вы серьёзно?!», хук/вступление, смена темы.
2. КАТЕГОРИЧЕСКИ НЕЛЬЗЯ поверх: убийств, пыток, насилия, самоубийств, смертей (ОСОБЕННО детей),
   реальных жертв, любой настоящей трагедии. Шутка над жертвой = недопустимо. Если сомневаешься — пропусти.
3. НЕ выбирай сцены с пометкой [ГРАФИКА].
4. Распредели по ролику (не кучей в одном месте).

Для каждой вставки верни объект:
- scene_id: id сцены из списка
- at_offset_sec: сколько секунд ОТ НАЧАЛА этой сцены поставить (0 = в начале; обычно 0.3-1.5)
- narration_snippet: точная фраза закадра, которую комментируем
- type: "movie" | "cartoon" | "meme" | "gif"
- idea: по-русски что показать (конкретно: какой фильм/мультик/мем и реакция)
- yt_query: КОНКРЕТНЫЙ англ. запрос для поиска на YouTube (назови источник, напр.
  "Michael Scott no please no reaction", "Spongebob imagination rainbow", "Vince McMahon money reaction",
  "Fry shut up and take my money", "Anakin younglings meme", "This is fine dog fire")
- duration_sec: 1.5-2.5
- why: 1 фраза почему уместно и смешно

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
        c["duration_sec"] = max(1.2, min(2.6, float(c.get("duration_sec", 2.0))))
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
