"""
Stage 3: Сцены
script.md + outline.json → scenes.json (разбивка для монтажа)
"""
import json
from pathlib import Path
from typing import Optional

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

        # Подключаем Claude
        claude = ClaudeService()
        template = claude.load_prompt("scenes")

        # Если есть фидбек — добавляем
        feedback_section = ""
        if feedback:
            feedback_section = f"\n\nФИДБЕК НА ПЕРЕДЕЛКУ:\n{feedback}\n"

        prompt = claude.render(template, {
            "SCRIPT_MD": script_text + feedback_section,
            "OUTLINE_JSON": outline,
            "PRIMARY_PRESET": primary_preset,
            "MODIFIERS": modifiers,
            "PROJECT_ID": state.project_id,
        })

        log.info("Разбиваю сценарий на микро-сцены через Claude...")
        scenes = claude.call_json(prompt, max_tokens=32000, temperature=0.7)

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
        log.info(f"  Длительность: {scenes.get('total_duration_sec', 0)/60:.1f} мин")
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
