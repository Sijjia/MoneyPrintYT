"""
Stage 3: Сцены
script.md + outline.json → scenes.json (разбивка для монтажа)

ВАЖНО: раскадровка идёт ПОСЕКЦИОННО — отдельный LLM-вызов на каждую секцию
сценария (intro-хук / каждый уровень айсберга / заключение), затем сцены
сшиваются в один scenes.json. Причина: один общий вызов НЕ вмещает раскадровку
20+ минут в max_tokens и молча обрывает покрытие на середине (теряя хвост тем и
заключение). Посекционно каждый кусок мал и покрывается полностью.
"""
import json
import re
from pathlib import Path
from typing import Optional

from core.config import get_settings
from core.logger import setup_logger
from core.state import Stage, StateManager
from services.llm.claude import ClaudeService

log = setup_logger("stage3")


def run(project_dir: Path, feedback: Optional[str] = None) -> dict:
    """
    Запустить Stage 3.

    Args:
        project_dir: путь к папке проекта
        feedback: фидбек на переделку (если есть)

    Returns:
        scenes dict
    """
    log.info(f"[bold cyan]Stage 3: Сцены[/]")

    state_manager = StateManager(project_dir)
    state = state_manager.load()
    state.mark_running(Stage.SCENES)
    state_manager.save(state)

    try:
        # Загружаем входные данные
        outline_path = project_dir / "outline.json"
        script_path = project_dir / "script.md"

        if not outline_path.exists() or not script_path.exists():
            raise FileNotFoundError("Сначала выполни Stage 1 и Stage 2")

        outline = json.loads(outline_path.read_text(encoding="utf-8"))
        script_text = script_path.read_text(encoding="utf-8")

        # Парсим preset
        preset_full = outline.get("preset", "MYSTIC")
        if "+" in preset_full:
            primary_preset, *modifiers = preset_full.split("+")
            primary_preset = primary_preset.strip()
            modifiers = [m.strip() for m in modifiers]
        else:
            primary_preset = preset_full.strip()
            modifiers = []

        # Подключаем LLM. Раскадровка — механика (порезать сценарий на сцены +
        # типы медиа), топ-модель не нужна → берём дешёвую (LLM_MODEL_CHEAP), это
        # ~90% стоимости ролика. Пусто → обычная llm_model.
        claude = ClaudeService(model=get_settings().llm_model_cheap or None)
        log.info(f"LLM (раскадровка): {claude.model}")
        template = claude.load_prompt("scenes")

        # Режем сценарий на секции и раскадровываем КАЖДУЮ отдельным вызовом,
        # чтобы гарантированно покрыть весь текст (без обрыва по max_tokens).
        sections = _split_script_sections(script_text)
        log.info(
            f"Сценарий разбит на {len(sections)} секций "
            f"(intro/уровни/заключение) — раскадровываю посекционно"
        )

        feedback_section = f"\n\nФИДБЕК НА ПЕРЕДЕЛКУ:\n{feedback}\n" if feedback else ""

        # Названия уровней для озвучиваемых анонсов (level_announce)
        level_names = {
            lo.get("level"): _level_announce_text(lo.get("title", ""))
            for lo in outline.get("levels", [])
        }

        all_scenes = []
        seen_levels = set()
        for sec in sections:
            prompt = claude.render(template, {
                "SCRIPT_MD": _chunk_instruction(sec) + sec["text"] + feedback_section,
                "OUTLINE_JSON": outline,
                "PRIMARY_PRESET": primary_preset,
                "MODIFIERS": modifiers,
                "PROJECT_ID": state.project_id,
            })

            log.info(f"  → секция «{sec['label']}» (level {sec['level']})...")
            # Секция мала (≈5 мин), 24k токенов с большим запасом — обрыва не будет.
            obj = claude.call_json(prompt, max_tokens=24000, temperature=0.7)
            chunk_scenes = obj.get("scenes", []) if isinstance(obj, dict) else []
            if not chunk_scenes:
                raise ValueError(f"Секция «{sec['label']}» вернула 0 сцен")

            # Принудительно проставляем level/section — модели не доверяем.
            for s in chunk_scenes:
                s["level"] = sec["level"]
                s.setdefault("section", sec["section"])

            # Анонс-сцены: диктор проговаривает название уровня/темы + карточка на
            # экране (level_card / topic_card печатной машинкой). Вставляем ПЕРЕД
            # контентом темы. Для intro/outro анонсов нет.
            lvl = sec["level"]
            if sec["section"] not in ("intro", "outro"):
                if lvl >= 1 and lvl not in seen_levels:
                    seen_levels.add(lvl)
                    if level_names.get(lvl):
                        all_scenes.append(_make_announce_scene(
                            level_names[lvl], "level_card", lvl, "level_announce", primary_preset))
                # topic_announce — только для настоящих тем (### ), НЕ для мостика-абзаца
                # под заголовком уровня (иначе анонс продублирует название уровня).
                if sec.get("is_theme"):
                    all_scenes.append(_make_announce_scene(
                        _theme_announce_text(sec["label"]), "topic_card", lvl, "topic_announce", primary_preset))

            all_scenes.extend(chunk_scenes)
            log.info(f"     {len(chunk_scenes)} сцен")

        # Сквозная перенумерация ID
        for i, s in enumerate(all_scenes, start=1):
            s["id"] = f"scene_{i:03d}"

        # Нормализуем длительности: при посекционной генерации каждый вызов
        # оценивает duration_sec независимо и щедро — сумма раздувается (напр. 33
        # мин при 20 мин речи). Масштабируем под реальную длину озвучки, сохраняя
        # относительный ритм. WhisperX в Stage 4 уточнит тайминг по mp3, но
        # total_duration_sec для планирования музыки/таймлайна должен быть честным.
        _normalize_durations(all_scenes)

        total_dur = round(sum(float(s.get("duration_sec", 0)) for s in all_scenes), 1)

        # Короткие CAPS-заголовки уровней (нужны для level-карточек) — дешёвый вызов
        level_titles = _generate_level_titles(claude, outline, primary_preset)

        scenes = {
            "project_id": state.project_id,
            "primary_preset": primary_preset,
            "modifiers": modifiers,
            "total_duration_sec": total_dur,
            "total_scenes": len(all_scenes),
            "scenes": all_scenes,
            "topics_index": _build_topics_index(all_scenes, outline),
            "level_transitions": _build_level_transitions(all_scenes),
            "level_titles": level_titles,
            "music_plan": {
                "main_mood": "ominous, tense, archive documentary",
                "shadow_mood": "horror, sub bass, breakdown",
                "estimated_main_duration_sec": total_dur,
            },
        }

        # Валидация структуры
        _validate_scenes(scenes)

        # Сохраняем
        scenes_path = project_dir / "scenes.json"
        scenes_path.write_text(
            json.dumps(scenes, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Обновляем state
        state.total_cost_usd += claude.estimate_cost()
        state.mark_awaiting(Stage.SCENES)
        state_manager.save(state)

        log.info(f"[green]✓[/] Сцены сохранены: {scenes_path}")
        log.info(f"  Сцен сгенерировано: {len(scenes['scenes'])}")
        log.info(f"  Длительность: {total_dur/60:.1f} мин")
        log.info(f"  Преимущественный пресет: {scenes['primary_preset']}")
        log.info(f"  Cost: ${claude.estimate_cost():.4f}")

        # Статистика по типам визуала
        visual_types = {}
        for scene in scenes["scenes"]:
            vtype = scene["visual"]["type"]
            visual_types[vtype] = visual_types.get(vtype, 0) + 1
        log.info("  Распределение визуала:")
        for vtype, count in sorted(visual_types.items(), key=lambda x: -x[1]):
            pct = count * 100 / len(scenes['scenes'])
            log.info(f"    {vtype}: {count} ({pct:.1f}%)")

        return scenes

    except Exception as e:
        state.mark_failed(Stage.SCENES, str(e))
        state_manager.save(state)
        raise


def _level_announce_text(title: str) -> str:
    """«ПЕРВЫЙ УРОВЕНЬ. ВЕРХУШКА АЙСБЕРГА» → «Первый уровень. Верхушка айсберга.»"""
    parts = [p.strip().capitalize() for p in title.split(".") if p.strip()]
    return ". ".join(parts) + "." if parts else title


def _theme_announce_text(title: str) -> str:
    """Название темы для озвучки: как есть, с завершающей точкой."""
    t = title.strip()
    return t if t and t[-1] in ".!?…" else t + "."


def _make_announce_scene(voiceover: str, ctype: str, level: int,
                         section: str, preset: str) -> dict:
    """Сцена-анонс: диктор проговаривает название + карточка на экране.
    Тип level_card/topic_card → медиа не качается, рисуется плашка (topic — печатной
    машинкой). fallback_query даёт тёмный фон под карточку, если он нужен сборке."""
    words = len(voiceover.split())
    return {
        "id": "tmp", "section": section, "level": level, "topic_id": None,
        "voiceover": voiceover,
        "duration_sec": max(2.0, round(words / 2.5, 1)),
        "visual": {"type": ctype, "search_query": "", "fallback_query": "dark ominous fog background"},
        "camera": {"movement": "static", "speed": "slow"},
        "transition_out": {"type": "default", "duration_ms": 600},
        "audio": {"music_layer": "main", "music_intensity": 0.35, "sfx": []},
        "preset": preset, "modifiers": [], "mood": "mysterious", "text_overlay": None,
    }


def _normalize_durations(scenes: list, wpm: int = 150) -> None:
    """Масштабирует duration_sec всех сцен так, чтобы сумма ≈ реальной длине
    озвучки (по числу слов voiceover при `wpm`). Сохраняет относительный ритм
    (драматичные короче, описательные длиннее), но убирает раздутость оценок."""
    words = sum(len(s.get("voiceover", "").split()) for s in scenes)
    cur = sum(float(s.get("duration_sec", 0)) for s in scenes)
    if words == 0 or cur <= 0:
        return
    target = words / (wpm / 60.0)  # секунд речи при wpm (150 → 2.5 слова/сек)
    factor = target / cur
    for s in scenes:
        d = float(s.get("duration_sec", 0)) * factor
        s["duration_sec"] = round(max(1.2, d), 1)


def _has_body(lines: list) -> bool:
    """True, если среди строк есть непустой текст-абзац (не заголовок/разделитель)."""
    for l in lines:
        s = l.strip()
        if s and not s.startswith("#") and not s.startswith("---"):
            return True
    return False


def _split_script_sections(script_text: str) -> list:
    """Режет script.md на МЕЛКИЕ единицы для посекционной раскадровки.

    Единица = intro-хук / отдельная ТЕМА (`### `) / заключение. Тема — самая
    крупная единица, которая гарантированно влезает в один LLM-вызов без обрыва
    по max_tokens (уровень целиком уже НЕ влезает: 60-70 микро-сцен).

    Возвращает список dict{level, section, label, text}:
      - всё до первого `## ` → intro (level 0);
      - каждая `### <ТЕМА>` → нужный level по родительскому `## <УРОВЕНЬ>`;
      - `## ЗАКЛЮЧЕНИЕ` → outro (level = номер последнего уровня, для SHADOW).
    Заголовки-уровни `## ` сами по себе тела не имеют и юнитами не становятся.
    """
    lines = script_text.splitlines()
    units = []
    cur = {"level": 0, "section": "intro", "label": "intro", "lines": []}
    level_counter = 0
    cur_level = 0

    def _flush(unit):
        # оставляем только единицы с реальным текстом озвучки (не голый заголовок)
        if _has_body(unit["lines"]):
            units.append(unit)

    for ln in lines:
        if ln.startswith("## "):
            _flush(cur)
            header = ln[3:].strip()
            if "ЗАКЛЮЧ" in header.upper():
                cur = {"level": max(level_counter, 1), "section": "outro",
                       "label": "заключение", "lines": [ln]}
            else:
                level_counter += 1
                cur_level = level_counter
                # заголовок уровня — тела нет, следующий `###` начнёт реальную тему
                cur = {"level": cur_level, "section": f"level_{cur_level}",
                       "label": header, "lines": [ln]}
        elif ln.startswith("### "):
            _flush(cur)
            cur = {"level": cur_level, "section": f"level_{cur_level}",
                   "label": ln[4:].strip(), "lines": [ln], "is_theme": True}
        else:
            cur["lines"].append(ln)
    _flush(cur)

    for u in units:
        u["text"] = "\n".join(u["lines"]).strip()
        del u["lines"]
    return units


def _chunk_instruction(sec: dict) -> str:
    """Инструкция-обёртка над фрагментом сценария для посекционного вызова."""
    if sec["section"] == "intro":
        what = "ВСТУПЛЕНИЕ-ХУК (секция intro, level 0)"
    elif sec["section"] == "outro":
        what = "ЗАКЛЮЧЕНИЕ и финальный CTA (секция outro)"
    else:
        what = f"ОДНА тема уровня {sec['level']} айсберга («{sec['label']}»)"

    return (
        "# ВНИМАНИЕ: ПОСЕКЦИОННАЯ РАСКАДРОВКА\n"
        f"Ниже дан ТОЛЬКО фрагмент сценария — {what}. Разбей на микро-сцены "
        "КАЖДОЕ предложение этого фрагмента, по порядку, дословно, НИЧЕГО не "
        "пропуская и не сокращая. Строки-заголовки (`# ...`, `## ...`, `### ...`) "
        "и разделители (`---`) — это НЕ voiceover, в сцены их не включай; но текст "
        "ВСЕХ абзацев переноси в voiceover целиком.\n"
        "Верни ТОЛЬКО валидный JSON вида {\"scenes\": [ ... ]} — массив сцен для "
        "ЭТОГО фрагмента по обычной схеме сцены. Глобальные поля "
        "(total_duration_sec, total_scenes, level_titles, topics_index, "
        "level_transitions, music_plan) НЕ добавляй — их соберёт пайплайн. "
        "Нумерацию scene_XXX можешь вести с начала — она будет перезаписана.\n\n"
        "=== ФРАГМЕНТ СЦЕНАРИЯ ===\n"
    )


def _generate_level_titles(claude: ClaudeService, outline: dict, preset: str) -> dict:
    """Короткие CAPS-заголовки уровней (1-3 слова) для cinematic level-карточек.

    Кормим LLM РЕАЛЬНЫЕ темы каждого уровня, чтобы ярлык бился с содержанием
    (иначе выходит мимо — напр. «МАССОВЫЕ САМОУБИЙСТВА» на уровне без таковых)."""
    levels = outline.get("levels", [])
    n = len(levels) or 4

    # Сводка тем по уровням — контекст для точного заголовка
    level_briefs = []
    for i, lvl in enumerate(levels, start=1):
        themes = [t.get("title", "") for t in (lvl.get("topics") or lvl.get("themes") or [])]
        level_briefs.append(f"Уровень {i}: " + "; ".join(themes))
    briefs_block = "\n".join(level_briefs)

    prompt = (
        "Придумай короткие заголовки уровней для видео-айсберга на тему "
        f"«{outline.get('title', '')}». Уровней: {n}. Заголовок каждого уровня "
        "должен ОТРАЖАТЬ РЕАЛЬНЫЕ темы этого уровня (список ниже), а не общую тему "
        "ролика. Каждый — 1-3 слова, ЗАГЛАВНЫМИ буквами, по нарастанию жути "
        "(поверхность → бездна).\n\n"
        f"ТЕМЫ ПО УРОВНЯМ:\n{briefs_block}\n\n"
        'Верни ТОЛЬКО JSON-объект вида {"1":"...","2":"...","3":"...","4":"..."} '
        "без каких-либо пояснений."
    )
    try:
        obj = claude.call_json(prompt, max_tokens=500, temperature=0.7)
        titles = {str(k): str(v).upper() for k, v in obj.items()}
        if titles:
            return titles
    except Exception as e:
        log.warning(f"level_titles через LLM не удались ({e}) — беру дефолт")

    default = ["ОФИЦИАЛЬНО", "СЛУХИ И ДОГАДКИ", "СКРЫТЫЕ ФАКТЫ", "ЗАПРЕЩЁННОЕ"]
    return {str(i + 1): (default[i] if i < len(default) else f"УРОВЕНЬ {i + 1}")
            for i in range(n)}


def _build_topics_index(scenes: list, outline: dict) -> list:
    """Собирает topics_index (id, title, scene_start, scene_end) из сцен."""
    titles = {}
    for lvl in outline.get("levels", []):
        for t in (lvl.get("topics") or lvl.get("themes") or []):
            titles[t.get("id")] = t.get("title", "")

    index = {}
    order = []
    for s in scenes:
        tid = s.get("topic_id")
        if tid is None:
            continue
        if tid not in index:
            index[tid] = {"id": tid, "title": titles.get(tid, ""),
                          "scene_start": s["id"], "scene_end": s["id"]}
            order.append(tid)
        index[tid]["scene_end"] = s["id"]
    return [index[tid] for tid in order]


def _build_level_transitions(scenes: list) -> list:
    """Механически строит переходы между соседними уровнями (>=1)."""
    trans = []
    prev_level = None
    for i, s in enumerate(scenes):
        lvl = s.get("level", 0)
        if (prev_level is not None and lvl != prev_level
                and lvl >= 1 and prev_level >= 1):
            trans.append({
                "after_scene": scenes[i - 1]["id"],
                "from_level": prev_level,
                "to_level": lvl,
                "mogrt": f"level_card_{lvl}.mogrt",
            })
        prev_level = lvl
    return trans


def _validate_scenes(scenes: dict):
    """Проверка обязательных полей и структуры."""
    if "scenes" not in scenes:
        raise ValueError("Отсутствует ключ 'scenes'")

    if not isinstance(scenes["scenes"], list) or len(scenes["scenes"]) < 10:
        raise ValueError(f"Слишком мало сцен: {len(scenes.get('scenes', []))}")

    required_scene_fields = ["id", "voiceover", "duration_sec", "visual", "camera", "transition_out"]
    for i, scene in enumerate(scenes["scenes"]):
        for field in required_scene_fields:
            if field not in scene:
                raise ValueError(f"В сцене #{i} ({scene.get('id', '?')}) отсутствует поле: {field}")

        if "type" not in scene["visual"]:
            raise ValueError(f"В сцене #{i} нет visual.type")

        if "movement" not in scene["camera"]:
            raise ValueError(f"В сцене #{i} нет camera.movement")
