"""
services/llm/style_examples.py
Динамическая сборка блока примеров стиля для промпта Stage 2 (script.txt)
из корпуса реальных сценариев Айдара (services/llm/prompts/style_examples/,
синхронизируется tools/sync_notion_scripts.py из Notion).

Вместо 5 захардкоженных эксцерптов — берём из 11 сценариев разнообразную
выборку: хуки-вступления (сильнейший сигнал стиля), куски тела и концовки.
Если корпус пуст — возвращаем "" (промпт остаётся рабочим на своих правилах).
"""
import json
import re
from pathlib import Path
from typing import List, Optional, Tuple

EXAMPLES_DIR = Path(__file__).resolve().parent / "prompts" / "style_examples"

_LEVEL_RE = re.compile(r"уровень", re.IGNORECASE)
_CONCL_RE = re.compile(r"заключени|на поверхность|возвращаемся|финал", re.IGNORECASE)
_INTRO_HDR_RE = re.compile(r"^\s*#{0,3}\s*вступлени", re.IGNORECASE)


def _split_sections(text: str) -> Tuple[str, str, str]:
    """Грубо делит сценарий на (intro, body_item, conclusion).

    intro       — текст до первого «УРОВЕНЬ» (хук-вступление);
    body_item   — содержимое первого уровня (без заголовка);
    conclusion  — текст после «ЗАКЛЮЧЕНИЕ»/«на поверхность».
    Любой кусок может быть "" если не нашёлся.
    """
    lines = text.split("\n")
    first_level = next((i for i, l in enumerate(lines) if _LEVEL_RE.search(l)), None)
    concl_idx = next((i for i in range(len(lines) - 1, -1, -1) if _CONCL_RE.search(lines[i])), None)

    # intro
    if first_level is not None:
        intro_lines = [l for l in lines[:first_level] if not _INTRO_HDR_RE.match(l)]
    else:
        intro_lines = lines[:25]
    intro = "\n".join(intro_lines).strip()

    # body item = от первого уровня до следующего уровня/заключения
    body = ""
    if first_level is not None:
        nxt = next((i for i in range(first_level + 1, len(lines)) if _LEVEL_RE.search(lines[i])), None)
        end = nxt if nxt is not None else (concl_idx if concl_idx is not None else len(lines))
        # пропускаем сам заголовок уровня
        body = "\n".join(lines[first_level + 1:end]).strip()

    # conclusion
    conclusion = ""
    if concl_idx is not None:
        conclusion = "\n".join(lines[concl_idx + 1:]).strip()

    return intro, body, conclusion


_LIST_LINE_RE = re.compile(r"^\s*(?:[-•*]|\d+[.)])\s+")


def _is_prose(chunk: str) -> bool:
    """Кусок похож на прозу для озвучки, а не на план/список.
    Отсеивает страницы-аутлайны (как «Айсберг РОССИИ»), где сплошные пункты."""
    lines = [l for l in chunk.split("\n") if l.strip()]
    if len(lines) < 2:
        return False
    list_ratio = sum(1 for l in lines if _LIST_LINE_RE.match(l)) / len(lines)
    sentences = chunk.count(". ") + chunk.count("! ") + chunk.count("? ")
    return list_ratio < 0.3 and sentences >= 2


def _clip(text: str, max_chars: int) -> str:
    """Обрезает по границе предложения, не разрывая слово."""
    text = re.sub(r"^#{1,3}\s*", "", text).strip()
    if len(text) <= max_chars:
        return text
    cut = text[:max_chars]
    # назад до конца предложения
    m = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "), cut.rfind("…"))
    if m > max_chars * 0.5:
        cut = cut[:m + 1]
    return cut.strip() + " […]"


def _load_index() -> List[dict]:
    idx = EXAMPLES_DIR / "index.json"
    if not idx.exists():
        return []
    try:
        return json.loads(idx.read_text(encoding="utf-8"))
    except Exception:
        return []


def build_style_block(
    *,
    intros: int = 3,
    bodies: int = 2,
    conclusions: int = 2,
    max_chars: int = 900,
) -> str:
    """Собирает markdown-блок примеров стиля из корпуса. "" если корпуса нет.

    Берёт РАЗНЫЕ сценарии под разные типы кусков, чтобы показать ширину стиля.
    """
    index = _load_index()
    if not index:
        return ""

    # кэш разобранных сценариев
    parsed = {}

    def sections(slug: str) -> Tuple[str, str, str]:
        if slug not in parsed:
            f = EXAMPLES_DIR / f"{slug}.txt"
            parsed[slug] = _split_sections(f.read_text(encoding="utf-8")) if f.exists() else ("", "", "")
        return parsed[slug]

    n = len(index)
    out: List[str] = []
    ex_num = 0
    used = set()  # чтобы один сценарий не повторялся в разных слотах
    cursor = 0

    def take(kind_label: str, count: int, sec_idx: int) -> None:
        """Берёт count прозаичных кусков типа sec_idx (0=intro,1=body,2=concl)
        из ещё не использованных сценариев, идя по списку по кругу."""
        nonlocal ex_num, cursor
        taken, scanned = 0, 0
        while taken < count and scanned < n:
            item = index[cursor % n]
            cursor += 1
            scanned += 1
            if item["slug"] in used:
                continue
            chunk = sections(item["slug"])[sec_idx]
            if not chunk or len(chunk) < 200 or not _is_prose(chunk):
                continue
            used.add(item["slug"])
            ex_num += 1
            taken += 1
            out.append(
                f"---\nПРИМЕР {ex_num} (тема: «{item['title']}», {kind_label}):\n\n"
                f"«{_clip(chunk, max_chars)}»\n"
            )

    take("ВСТУПЛЕНИЕ-ХУК", intros, 0)
    take("ТЕЛО / РАЗБОР ТЕМЫ", bodies, 1)
    take("ЗАКЛЮЧЕНИЕ", conclusions, 2)

    return "\n".join(out).strip()
