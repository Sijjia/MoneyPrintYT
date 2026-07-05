"""
Stage 2: Сценарий
outline.json → script.md (полный текст для озвучки)
"""
import json
from pathlib import Path
from typing import Optional

from core.config import get_settings
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

        # Динамический блок примеров стиля из корпуса реальных сценариев
        # (services/llm/prompts/style_examples/, синк из Notion). Фолбэк "" —
        # промпт остаётся рабочим на своих правилах стиля.
        from services.llm.style_examples import build_style_block
        style_block = build_style_block()
        if style_block:
            log.info(f"Подключил {style_block.count('ПРИМЕР ')} примеров стиля из корпуса")

        prompt = claude.render(template, {
            "OUTLINE_JSON": outline,
            "USER_FEEDBACK": feedback or "Нет фидбека, пиши с нуля по outline",
            "STYLE_EXAMPLES": style_block,
        })

        log.info("Генерирую сценарий через Claude (это займёт 1-3 минуты)...")
        # 20-30 мин озвучки на русском ≈ 28-35k символов ≈ ~13-15k токенов;
        # берём с запасом, чтобы модель не обрывала сценарий на середине.
        script_text = claude.call(prompt, max_tokens=24000, temperature=1.0)

        # Минимальная валидация
        if len(script_text) < 1000:
            raise ValueError(f"Сценарий слишком короткий ({len(script_text)} символов). Что-то пошло не так.")

        if "УРОВЕНЬ" not in script_text.upper() and "уровень" not in script_text.lower():
            log.warning("В сценарии не найдено слово 'уровень' — проверь структуру")

        # Сохраняем
        script_path = project_dir / "script.md"
        script_path.write_text(script_text, encoding="utf-8")

        # Сохранение в Notion (если включено NOTION_SAVE_SCRIPTS=true). Идемпотентно:
        # перезаписывает страницу прошлого прогона (state.notion_page_id).
        if get_settings().notion_save_scripts:
            from services.notion.save_script import save_script_to_notion
            title = outline.get("title", f"Сценарий {project_dir.name}")
            res = save_script_to_notion(
                title, script_text, replace_page_id=getattr(state, "notion_page_id", None)
            )
            if res:
                state.notion_page_id = res["id"]
                log.info(f"[green]✓[/] В Notion: {res['url']}")

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
