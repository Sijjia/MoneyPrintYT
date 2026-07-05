"""
tools/sync_notion_scripts.py
Вытягивает сценарии-референсы Айдара из Notion в локальный корпус
services/llm/prompts/style_examples/*.txt — чтобы промпты Stage 1-3 могли
кормиться его реальным стилем (а не пятью захардкоженными примерами).

Запуск:
  PYTHONIOENCODING=utf-8 ../webik-pipeline/.venv/Scripts/python.exe tools/sync_notion_scripts.py

Берёт все доступные интеграции страницы с «Айсберг» в названии (его сценарии),
сохраняет как <slug>.txt + index.json с метаданными (заголовок, кол-во символов).
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from services.notion import NotionClient  # noqa: E402

OUT_DIR = Path(__file__).resolve().parents[1] / "services" / "llm" / "prompts" / "style_examples"


def _slug(title: str) -> str:
    s = title.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE)
    s = re.sub(r"\s+", "_", s)
    return s[:60] or "untitled"


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    n = NotionClient()
    pages = n.search("", filter_type="page")
    index = []
    saved = 0
    for p in pages:
        title = n.get_page_title(p)
        # Берём только сценарии-айсберги (не служебные страницы вроде «Webik»).
        if "айсберг" not in title.lower():
            continue
        text = n.get_page_text(p["id"])
        if len(text) < 500:  # пустые/заглушки пропускаем
            print(f"  skip (мало текста): {title}")
            continue
        slug = _slug(title)
        (OUT_DIR / f"{slug}.txt").write_text(text, encoding="utf-8")
        index.append({"slug": slug, "title": title, "page_id": p["id"], "chars": len(text)})
        saved += 1
        print(f"  saved: {slug}.txt  «{title}»  ({len(text)} симв.)")

    (OUT_DIR / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\nГотово: {saved} сценариев → {OUT_DIR}")


if __name__ == "__main__":
    main()
