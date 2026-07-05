"""
services/stocks/clip_llm_pick.py
LLM-адаптер для выбора архивного YouTube-клипа — фабрика `llm_pick`,
совместимая с youtube_search.select_clip / auto_archive_clip.

Идея гибрида: LLM ранжирует кандидатов по релевантности факту/запросу (его
сильная сторона — понять, что «обзор Каца» это не архив, а «хроника 1986» —
архив), а тайм-окно внутри выбранного ролика считает chapter-aware эвристика
`_heuristic_window` (детерминированно, по главам/описанию).

Работает через ClaudeService → провайдер берётся из .env (OpenRouter или
Anthropic напрямую). Любая ошибка LLM наверху (select_clip) ловится и даёт
откат на чистую эвристику — пайплайн не падает.
"""
from typing import Callable, Dict, List, Optional

from core.logger import setup_logger
from services.llm.claude import ClaudeService
from services.stocks.youtube_search import fetch_video_details, _heuristic_window

log = setup_logger("clip-llm-pick")


_PROMPT = """Ты подбираешь архивный видеофрагмент с YouTube как подложку под факт из закадрового текста ролика.

ФАКТ (что говорит диктор): {fact}
ПОИСКОВЫЙ ЗАПРОС: {query}

КАНДИДАТЫ:
{cands}

Выбери ОДИН ролик, лучший как АРХИВНАЯ ПОДЛОЖКА под этот факт:
- настоящие архивные кадры / хроника / съёмка события — НЕ обзоры, реакции, нарезки-приколы, shorts;
- тема совпадает с фактом;
- вменяемая длительность (не многочасовой стрим/подкаст).
Если ни один не подходит как архив — верни index = -1.

Ответь СТРОГО одним JSON-объектом без пояснений и markdown:
{{"index": <0..{maxidx} или -1>, "reason": "<кратко почему>"}}"""


def make_llm_pick(
    claude: Optional[ClaudeService] = None,
    *,
    want_sec: float = 6.0,
) -> Callable[[str, str, List[Dict]], Optional[Dict]]:
    """Возвращает callable `llm_pick(fact, query, candidates)` для select_clip.

    claude — переиспользуемый ClaudeService (для общей статистики/стоимости).
    Создаётся лениво, если не передан.
    """
    svc = claude or ClaudeService()

    def llm_pick(fact: str, query: str, candidates: List[Dict]) -> Optional[Dict]:
        lines = []
        for i, c in enumerate(candidates):
            dur = c.get("duration")
            dur_s = f"{int(dur)}s" if dur else "?"
            lines.append(
                f"[{i}] {c.get('title', '')} | канал: {c.get('channel', '')} | "
                f"длит: {dur_s} | просмотры: {c.get('view_count') or '?'}"
            )
        prompt = _PROMPT.format(
            fact=(fact or query), query=query,
            cands="\n".join(lines), maxidx=len(candidates) - 1,
        )
        data = svc.call_json(prompt, max_tokens=500, temperature=0.0)
        idx = int(data.get("index", -1))
        if not (0 <= idx < len(candidates)):
            log.info(f"  LLM не выбрал архивный ролик (index={idx})")
            return None

        reason = str(data.get("reason", "llm"))[:200]
        # Окно внутри выбранного ролика — chapter-aware эвристикой.
        c = candidates[idx]
        try:
            detail = fetch_video_details(c["url"])
        except Exception as e:
            log.warning(f"  детали ролика не получены ({str(e)[:120]}) — окно по дефолту")
            detail = None
        cs, ce = _heuristic_window(detail, c, want_sec, query)
        return {
            "index": idx,
            "clip_start": round(cs, 2),
            "clip_end": round(ce, 2),
            "reason": f"llm: {reason}",
        }

    return llm_pick
