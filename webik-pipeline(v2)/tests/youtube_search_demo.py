"""Демо YouTube авто-архива: поиск кандидатов + эвристический выбор клип-окна.
Скачивание НЕ делаем (только поиск/выбор). Результат пишем в UTF-8 файл.

Запуск:
  PYTHONIOENCODING=utf-8 ../webik-pipeline/.venv/Scripts/python.exe tests/youtube_search_demo.py
"""
from __future__ import annotations
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.stocks.youtube_search import search_candidates, select_clip

QUERIES = [
    "Чернобыль ликвидация 1986 архивные кадры",
    "Михаил Горбачёв выступление 1991 хроника",
    "падение Берлинской стены 1989 кадры",
]

OUT = Path(__file__).resolve().parent / "_youtube_search_demo_out.txt"


def main():
    lines = []
    def w(s=""):
        print(s)
        lines.append(s)

    for q in QUERIES:
        w("=" * 70)
        w(f"ЗАПРОС: {q}")
        cands = search_candidates(q, n=6)
        for i, c in enumerate(cands, 1):
            d = c.get("duration")
            m = f"{int(d)//60}:{int(d)%60:02d}" if d else "?"
            w(f"  {i}. [{m}] {c['title'][:64]}")
            w(f"      {c['channel']} | views={c.get('view_count')} | {c['url']}")
        # выбор без LLM (эвристика). fetch_details=False — не лезем в каждый ролик
        # (быстро + без cookie-гейта); окно берём по дефолту от длительности.
        sel = select_clip(q, cands, want_sec=6.0, fetch_details=False)
        if sel:
            w("  >>> ВЫБРАНО:")
            w(f"      {sel['title'][:64]}")
            w(f"      окно [{sel['clip_start']:.1f}s — {sel['clip_end']:.1f}s] | {sel['reason']}")
            w(f"      {sel['url']}")
        else:
            w("  >>> кандидатов нет")
        w()

    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n[written] {OUT}")


if __name__ == "__main__":
    main()
