"""
Stage 2: Сценарий
outline.json → script.md (полный текст для озвучки)
"""
import json
from pathlib import Path
from typing import Optional

from core.logger import setup_logger
from core.state import Stage, StateManager
from services.llm.claude import ClaudeService

log = setup_logger("stage2")


def run(project_dir: Path, feedback: Optional[str] = None) -> str:
    """
    Запустить Stage 2.

    Args:
        project_dir: путь к папке проекта
        feedback: фидбек на переделку (если есть)

    Returns:
        текст сценария
    """
    log.info(f"[bold cyan]Stage 2: Сценарий[/]")

    state_manager = StateManager(project_dir)
    state = state_manager.load()
    state.mark_running(Stage.SCRIPT)
    state_manager.save(state)

    try:
        # Загружаем outline
        outline_path = project_dir / "outline.json"
        if not outline_path.exists():
            raise FileNotFoundError("outline.json не найден. Выполни Stage 1 сначала.")
        outline = json.loads(outline_path.read_text(encoding="utf-8"))

        # Подключаем Claude
        claude = ClaudeService()
        template = claude.load_prompt("script")

        prompt = claude.render(template, {
            "OUTLINE_JSON": outline,
            "USER_FEEDBACK": feedback or "Нет фидбека, пиши с нуля по outline",
        })

        log.info("Генерирую сценарий через Claude (это займёт 1-3 минуты)...")
        script_text = claude.call(prompt, max_tokens=16000, temperature=1.0)

        # Минимальная валидация
        if len(script_text) < 1000:
            raise ValueError(f"Сценарий слишком короткий ({len(script_text)} символов). Что-то пошло не так.")

        if "УРОВЕНЬ" not in script_text.upper() and "уровень" not in script_text.lower():
            log.warning("В сценарии не найдено слово 'уровень' — проверь структуру")

        # Сохраняем
        script_path = project_dir / "script.md"
        script_path.write_text(script_text, encoding="utf-8")

        # Статистика
        word_count = len(script_text.split())
        estimated_duration_min = word_count / 150  # средняя скорость диктора 150 слов/мин

        # Обновляем state
        state.total_cost_usd += claude.estimate_cost()
        state.mark_awaiting(Stage.SCRIPT)
        state_manager.save(state)

        log.info(f"[green]✓[/] Сценарий сохранён: {script_path}")
        log.info(f"  Символов: {len(script_text):,}")
        log.info(f"  Слов: {word_count:,}")
        log.info(f"  Расчётная длительность: ~{estimated_duration_min:.1f} мин")
        log.info(f"  Cost: ${claude.estimate_cost():.4f}")

        return script_text

    except Exception as e:
        state.mark_failed(Stage.SCRIPT, str(e))
        state_manager.save(state)
        raise
