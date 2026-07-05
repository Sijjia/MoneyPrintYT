"""
Stage 1: Концепция
Идея пользователя → outline.json (структура айсберга)
"""
import json
from pathlib import Path
from typing import Optional

from core.config import get_settings
from core.logger import setup_logger
from core.state import Stage, StateManager
from services.llm.claude import ClaudeService

log = setup_logger("stage1")


def run(
    project_dir: Path,
    idea: str,
    duration_min: int = 15,
    forced_preset: Optional[str] = None,
    feedback: Optional[str] = None,
    levels: int = 4,
) -> dict:
    """
    Запустить Stage 1.

    Args:
        project_dir: путь к папке проекта
        idea: идея пользователя ("Айсберг Эпштейна")
        duration_min: целевая длительность
        forced_preset: принудительный пресет (если задан)
        feedback: фидбек на переделку (если есть)

    Returns:
        outline dict
    """
    log.info(f"[bold cyan]Stage 1: Концепция[/]")
    log.info(f"Идея: {idea}")

    state_manager = StateManager(project_dir)
    state = state_manager.load()
    state.mark_running(Stage.CONCEPT)
    state_manager.save(state)

    try:
        # Подключаем Claude
        claude = ClaudeService()
        template = claude.load_prompt("concept")

        # Если есть фидбек — добавляем в идею
        idea_with_feedback = idea
        if feedback:
            idea_with_feedback = f"{idea}\n\nФИДБЕК НА ПРЕДЫДУЩУЮ ПОПЫТКУ — учти его:\n{feedback}"

        # Рендерим промт
        prompt = claude.render(template, {
            "IDEA": idea_with_feedback,
            "DURATION_MIN": duration_min,
            "FORCED_PRESET": forced_preset or "не задан, выбери сам",
            "LEVELS_COUNT": levels,
        })

        log.info("Отправляю запрос в Claude...")
        outline = claude.call_json(prompt, max_tokens=8000, temperature=1.0)

        # Валидация структуры
        _validate_outline(outline, expected_levels=levels)

        # Сохраняем
        outline_path = project_dir / "outline.json"
        outline_path.write_text(
            json.dumps(outline, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Обновляем state
        state.preset = outline.get("preset")
        state.target_duration_min = outline.get("estimated_duration_min", duration_min)
        state.total_cost_usd += claude.estimate_cost()
        state.mark_awaiting(Stage.CONCEPT)
        state_manager.save(state)

        log.info(f"[green]✓[/] Outline сохранён: {outline_path}")
        log.info(f"  Title: {outline['title']}")
        log.info(f"  Preset: {outline['preset']}")
        log.info(f"  Уровней: {len(outline['levels'])}")
        log.info(f"  Тем: {sum(len(l['topics']) for l in outline['levels'])}")
        log.info(f"  Cost: ${claude.estimate_cost():.4f}")

        return outline

    except Exception as e:
        state.mark_failed(Stage.CONCEPT, str(e))
        state_manager.save(state)
        raise


def _validate_outline(outline: dict, expected_levels: int = 4):
    """Проверка обязательных полей."""
    required = ["title", "preset", "intro_hook", "levels", "outro_text"]
    for field in required:
        if field not in outline:
            raise ValueError(f"В outline отсутствует обязательное поле: {field}")

    if len(outline["levels"]) != expected_levels:
        raise ValueError(
            f"Должно быть {expected_levels} уровня(ей), получено {len(outline['levels'])}"
        )

    for level in outline["levels"]:
        if not level.get("topics") or len(level["topics"]) < 2:
            raise ValueError(f"Уровень {level.get('level')} должен иметь минимум 2 темы")
