"""
services/notion/notion_client.py
Тонкий клиент Notion API (REST через httpx — без новых зависимостей).

Назначение: читать сценарии-референсы Айдара (для style-guide и few-shot в
промптах Stage 1-3) и сохранять готовые сценарии обратно в Notion.

Аутентификация: internal integration token (NOTION_TOKEN в .env). Интеграции
должен быть расшарен доступ к нужным страницам/базе (в Notion: страница →
"..." → Connections → выбрать интеграцию).
"""
from typing import Any, Dict, List, Optional

import httpx

from core.config import get_settings
from core.logger import setup_logger

log = setup_logger("notion")

API_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# Типы блоков, у которых есть rich_text с осмысленным текстом сценария.
_TEXT_BLOCKS = {
    "paragraph", "heading_1", "heading_2", "heading_3",
    "bulleted_list_item", "numbered_list_item", "quote", "callout",
    "to_do", "toggle",
}


class NotionClient:
    def __init__(self, token: Optional[str] = None):
        self.token = token or get_settings().notion_token
        if not self.token:
            raise ValueError("NOTION_TOKEN не задан в .env")
        self._client = httpx.Client(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )

    # ---------- низкоуровневое ----------
    def _get(self, path: str, **params) -> Dict[str, Any]:
        r = self._client.get(path, params=params or None)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json: Dict[str, Any]) -> Dict[str, Any]:
        r = self._client.post(path, json=json)
        r.raise_for_status()
        return r.json()

    # ---------- поиск / листинг ----------
    def search(self, query: str = "", *, filter_type: Optional[str] = None,
               page_size: int = 50) -> List[Dict[str, Any]]:
        """Поиск по доступным интеграции страницам/базам.

        filter_type: "page" | "database" | None (всё).
        Возвращает сырые объекты результата (с id/title/object).
        """
        body: Dict[str, Any] = {"page_size": page_size}
        if query:
            body["query"] = query
        if filter_type:
            body["filter"] = {"property": "object", "value": filter_type}
        return self._post("/search", body).get("results", [])

    def query_database(self, database_id: str, *, page_size: int = 100) -> List[Dict[str, Any]]:
        """Все строки (страницы) базы данных."""
        results, cursor = [], None
        while True:
            body: Dict[str, Any] = {"page_size": page_size}
            if cursor:
                body["start_cursor"] = cursor
            data = self._post(f"/databases/{database_id}/query", body)
            results.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        return results

    # ---------- чтение содержимого ----------
    def get_page_title(self, page: Dict[str, Any]) -> str:
        """Достаёт заголовок из объекта page (ищет title-property)."""
        props = page.get("properties", {})
        for prop in props.values():
            if prop.get("type") == "title":
                return _rich_to_text(prop.get("title", []))
        return ""

    def get_page_text(self, page_id: str, *, max_depth: int = 3) -> str:
        """Рекурсивно собирает весь текст со страницы в plain markdown-ish.
        Достаточно для разбора стиля сценария."""
        lines: List[str] = []
        self._collect_blocks(page_id, lines, depth=0, max_depth=max_depth)
        return "\n".join(lines).strip()

    def _collect_blocks(self, block_id: str, out: List[str], depth: int, max_depth: int):
        cursor = None
        while True:
            params = {"page_size": 100}
            if cursor:
                params["start_cursor"] = cursor
            data = self._get(f"/blocks/{block_id}/children", **params)
            for blk in data.get("results", []):
                btype = blk.get("type", "")
                if btype in _TEXT_BLOCKS:
                    txt = _rich_to_text(blk[btype].get("rich_text", []))
                    if txt:
                        prefix = ""
                        if btype.startswith("heading"):
                            prefix = "#" * int(btype[-1]) + " "
                        elif btype in ("bulleted_list_item", "to_do", "toggle"):
                            prefix = "- "
                        elif btype == "numbered_list_item":
                            prefix = "1. "
                        elif btype == "quote":
                            prefix = "> "
                        out.append("  " * depth + prefix + txt)
                # рекурсия в детей (toggle, колонки и т.д.)
                if blk.get("has_children") and depth < max_depth:
                    self._collect_blocks(blk["id"], out, depth + 1, max_depth)
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")

    # ---------- запись ----------
    def create_page(self, parent_id: str, title: str, markdown: str,
                    *, parent_type: str = "page_id") -> Dict[str, Any]:
        """Создаёт страницу с текстом (абзацы). parent_type: page_id|database_id.

        Для database_id title кладётся в title-property "Name" (стандарт Notion).
        """
        blocks = _markdown_to_blocks(markdown)
        # Notion разрешает максимум 100 child-блоков за запрос. Длинные сценарии
        # (200+ абзацев) создаём первой сотней, остальное докидываем батчами.
        first, rest = blocks[:100], blocks[100:]
        if parent_type == "database_id":
            payload = {
                "parent": {"database_id": parent_id},
                "properties": {"Name": {"title": [_text_obj(title)]}},
                "children": first,
            }
        else:
            payload = {
                "parent": {"page_id": parent_id},
                "properties": {"title": {"title": [_text_obj(title)]}},
                "children": first,
            }
        page = self._post("/pages", payload)
        page_id = page["id"]
        for i in range(0, len(rest), 100):
            batch = rest[i:i + 100]
            r = self._client.patch(f"/blocks/{page_id}/children", json={"children": batch})
            r.raise_for_status()
        return page

    def archive_page(self, page_id: str) -> None:
        """Мягко удаляет (архивирует) страницу."""
        r = self._client.patch(f"/pages/{page_id}", json={"archived": True})
        r.raise_for_status()


# ---------- helpers ----------
def _rich_to_text(rich: List[Dict[str, Any]]) -> str:
    return "".join(r.get("plain_text", "") for r in rich)


def _text_obj(s: str) -> Dict[str, Any]:
    return {"type": "text", "text": {"content": s[:2000]}}


def _markdown_to_blocks(md: str) -> List[Dict[str, Any]]:
    """Очень простой markdown → Notion-блоки (заголовки/абзацы). Notion лимит —
    100 детей на запрос; режем."""
    blocks: List[Dict[str, Any]] = []
    for raw in md.split("\n"):
        line = raw.rstrip()
        if not line:
            continue
        if line.startswith("### "):
            btype, content = "heading_3", line[4:]
        elif line.startswith("## "):
            btype, content = "heading_2", line[3:]
        elif line.startswith("# "):
            btype, content = "heading_1", line[2:]
        elif line.startswith("- "):
            btype, content = "bulleted_list_item", line[2:]
        else:
            btype, content = "paragraph", line
        blocks.append({
            "object": "block", "type": btype,
            btype: {"rich_text": [_text_obj(content)]},
        })
    return blocks
