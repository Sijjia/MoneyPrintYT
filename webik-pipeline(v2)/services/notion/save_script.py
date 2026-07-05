"""
services/notion/save_script.py
Сохранение готового сценария (Stage 2) обратно в Notion — как дочернюю
страницу под «Webik» (рядом с остальными айсбергами).

Идемпотентно: если передан replace_page_id (из state прошлого прогона) — старая
страница архивируется, создаётся свежая. Так в Notion всегда «последняя версия»
без дублей при повторных прогонах.
"""
from typing import Optional

from core.config import get_settings
from core.logger import setup_logger
from services.notion import NotionClient

log = setup_logger("notion-save")


def save_script_to_notion(
    title: str,
    markdown: str,
    *,
    parent_id: Optional[str] = None,
    replace_page_id: Optional[str] = None,
) -> Optional[dict]:
    """Создаёт страницу со сценарием в Notion. Возвращает {id, url} или None.

    Ошибки не валят пайплайн — Notion это «приятный бонус», а не критичный шаг.
    """
    s = get_settings()
    if not s.notion_token:
        log.info("NOTION_TOKEN не задан — пропускаю сохранение в Notion")
        return None
    parent = parent_id or s.notion_scripts_parent_id
    if not parent:
        log.warning("Не задан notion_scripts_parent_id — некуда сохранять")
        return None

    try:
        n = NotionClient()
        if replace_page_id:
            try:
                n.archive_page(replace_page_id)
                log.info(f"Архивировал прошлую версию сценария {replace_page_id}")
            except Exception as e:
                log.warning(f"Не смог заархивировать старую страницу: {str(e)[:120]}")
        pg = n.create_page(parent, title, markdown)
        log.info(f"Сценарий сохранён в Notion: {pg.get('url')}")
        return {"id": pg["id"], "url": pg.get("url", "")}
    except Exception as e:
        log.warning(f"Сохранение в Notion не удалось: {str(e)[:160]}")
        return None
