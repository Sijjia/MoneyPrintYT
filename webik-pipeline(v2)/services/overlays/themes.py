"""
services/overlays/themes.py
Пер-видео «тема» оверлеев — чтобы ролики не были под копирку.

Каждый проект детерминированно (по хешу имени папки) получает свою тему:
акцентный цвет + вариант раскладки + «энергия» анимации. Внутри ролика тема
единая, между роликами — разная. Можно перебить вручную (override).
"""
from __future__ import annotations

import hashlib
from typing import Dict, List, Optional

# Все палитры выдержаны в тёмном док-стиле; меняется только акцент.
THEMES: List[Dict] = [
    {"name": "Кровь", "accent": "#d92828", "align": "left", "energy": 1.0},
    {"name": "Амбер", "accent": "#e0a020", "align": "center", "energy": 1.15},
    {"name": "Токсик", "accent": "#1fa48a", "align": "left", "energy": 0.9},
    {"name": "Лёд", "accent": "#3d7fd1", "align": "center", "energy": 1.0},
    {"name": "Вино", "accent": "#a11d3a", "align": "left", "energy": 0.85},
    {"name": "Золото", "accent": "#c8a24a", "align": "center", "energy": 1.1},
]

# Композиции, поддерживающие проп align (лево/центр или лево/право).
_ALIGN_COMPS = {"CountUpBar", "NameLabel"}


def pick_theme(seed: str, override: Optional[str] = None) -> Dict:
    """Тема по сид-строке (имя проекта). override — имя темы вручную."""
    if override:
        for t in THEMES:
            if t["name"].lower() == override.lower():
                return t
    h = int(hashlib.md5(seed.encode("utf-8")).hexdigest(), 16)
    return THEMES[h % len(THEMES)]


def apply_theme(overlays: List[dict], theme: Dict) -> List[dict]:
    """Проставляет акцент/раскладку/энергию в props каждого оверлея (не перетирая
    уже заданное вручную)."""
    for ov in overlays:
        props = ov.setdefault("props", {})
        props.setdefault("accent", theme["accent"])
        props.setdefault("energy", theme["energy"])
        comp = ov.get("composition")
        if comp == "CountUpBar":
            props.setdefault("align", theme["align"])  # left | center
        elif comp == "NameLabel":
            # у нижнего третьего оси лево/право
            props.setdefault("align", "left" if theme["align"] == "left" else "right")
    return overlays
