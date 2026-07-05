"""
services/stocks/youtube_search.py
Авто-поиск архивных YouTube-роликов под факт/сущность сцены + выбор клип-окна.

Связка для фичи «факт → архивный материал с YouTube»:
    NER/LLM даёт запрос  →  search_candidates() ищет ролики (yt-dlp ytsearch,
    БЕЗ API-ключа, БЕЗ кредитов)  →  select_clip() выбирает ролик и [start,end]
    →  youtube_clipper.fetch_clip() качает+режет  →  кладётся в таймлайн.

Два режима выбора (select_clip):
  • llm_pick=None  → эвристика: archival-ключевые слова в заголовке + вменяемая
    длительность + просмотры. Работает прямо сейчас, без кредитов.
  • llm_pick=callable → LLM по метаданным (заголовки/описания/главы) выбирает
    лучший ролик и точное окно. Включаем когда на ключе есть кредиты.

Юр. серая зона (как и youtube_clipper): использовать для public news / archive /
кинохроники, где fair-use очевиден. Атрибуция автора сохраняется в результате
для end-screen / описания видео.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from core.logger import setup_logger

log = setup_logger("youtube-search")

# Слова, повышающие шанс что ролик = реальная архивная съёмка, а не реакция/обзор.
ARCHIVAL_HINTS = [
    "архив", "archive", "кадры", "footage", "хроника", "кинохроника",
    "newsreel", "документ", "съёмка", "съемка", "19", "20",  # годы
    "запись", "video", "видео", "real", "реальн", "подлинн",
]
# Слова-минусы: обзоры/реакции/мемы/шортсы — не архив.
JUNK_HINTS = [
    "обзор", "review", "реакция", "reaction", "топ ", "top ", "прикол",
    "мем", "meme", "разбор", "тикток", "tiktok", "#shorts", "shorts",
    "трейлер", "trailer", "мультфильм", "cartoon", "игра", "gameplay",
]


def _cookie_opts() -> dict:
    """Cookies для обхода bot-detection (как в youtube_clipper).

    Для flat-поиска обычно НЕ нужны, но для extract_info глав/описания
    конкретного ролика могут потребоваться. Безопасно подмешиваем если заданы.
    """
    opts: dict = {}
    cookies_browser = os.environ.get("YT_COOKIES_BROWSER")
    cookies_file = os.environ.get("YT_COOKIES_FILE")
    if not cookies_browser and not cookies_file:
        try:
            from core.config import get_settings
            s = get_settings()
            if getattr(s, "yt_cookies_file", None):
                cookies_file = str(s.yt_cookies_file)
            elif getattr(s, "yt_cookies_browser", None):
                cookies_browser = s.yt_cookies_browser
        except Exception:
            pass
    if cookies_file and Path(cookies_file).exists():
        opts["cookiefile"] = cookies_file
    elif cookies_browser:
        opts["cookiesfrombrowser"] = (cookies_browser,)
    return opts


def search_candidates(
    query: str,
    n: int = 8,
    min_dur: float = 5.0,
    max_dur: float = 3600.0,
) -> List[Dict]:
    """Ищет до `n` YouTube-роликов по запросу (flat, без скачивания).

    Возвращает список dict: {id, url, title, channel, duration, view_count,
    upload_date}. Отфильтрован по длительности [min_dur, max_dur].
    Пустой список — если yt-dlp недоступен / ничего не нашлось.
    """
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        log.warning("yt-dlp не установлен (pip install yt-dlp)")
        return []

    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,       # не лезть в каждый ролик — быстро
        "skip_download": True,
        "default_search": "ytsearch",
    }
    ydl_opts.update(_cookie_opts())

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{int(n)}:{query}", download=False)
    except Exception as e:
        log.warning(f"  ytsearch failed для '{query}': {str(e)[:200]}")
        return []

    entries = (info or {}).get("entries") or []
    out: List[Dict] = []
    for e in entries:
        if not e:
            continue
        dur = e.get("duration")
        if dur is not None and not (min_dur <= dur <= max_dur):
            continue
        vid = e.get("id")
        out.append({
            "id": vid,
            "url": e.get("url") or (f"https://www.youtube.com/watch?v={vid}" if vid else None),
            "title": e.get("title") or "",
            "channel": e.get("channel") or e.get("uploader") or "",
            "duration": dur,
            "view_count": e.get("view_count"),
            "upload_date": e.get("upload_date"),
        })
    log.info(f"  ytsearch '{query}': {len(out)} кандидатов (из {len(entries)})")
    return out


def fetch_video_details(url: str) -> Optional[Dict]:
    """Полные метаданные одного ролика БЕЗ скачивания (для выбора окна):
    description, chapters [{title,start_time,end_time}], duration.
    Может потребовать cookies. None при ошибке.
    """
    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        return None
    ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
    ydl_opts.update(_cookie_opts())
    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
    except Exception as e:
        log.warning(f"  details failed {url}: {str(e)[:160]}")
        return None
    if not info:
        return None
    return {
        "id": info.get("id"),
        "title": info.get("title") or "",
        "description": info.get("description") or "",
        "duration": info.get("duration"),
        "chapters": info.get("chapters") or [],
        "channel": info.get("channel") or info.get("uploader") or "",
    }


def _score_candidate(c: Dict, query: str) -> float:
    """Эвристический скор «насколько это похоже на архивную съёмку»."""
    title = (c.get("title") or "").lower()
    score = 0.0
    for kw in ARCHIVAL_HINTS:
        if kw in title:
            score += 2.0
    for kw in JUNK_HINTS:
        if kw in title:
            score -= 4.0
    # перекрытие слов запроса с заголовком
    q_words = {w for w in re.findall(r"\w+", query.lower()) if len(w) > 3}
    if q_words:
        overlap = len(q_words & set(re.findall(r"\w+", title))) / len(q_words)
        score += overlap * 3.0
    # длительность: 30с..20мин — комфортно; слишком коротко/длинно — минус
    dur = c.get("duration") or 0
    if 30 <= dur <= 1200:
        score += 1.5
    elif dur > 2400:
        score -= 1.0
    # популярность как слабый сигнал достоверности
    vc = c.get("view_count") or 0
    if vc > 50_000:
        score += 0.5
    return score


def _heuristic_window(detail: Optional[Dict], cand: Dict, want_sec: float, query: str):
    """Без LLM: выбрать [start,end]. Если есть главы — берём главу, чей
    заголовок пересекается с запросом; иначе окно в ~12% от начала (скип интро).
    """
    dur = (detail or {}).get("duration") or cand.get("duration") or (want_sec * 4)
    chapters = (detail or {}).get("chapters") or []
    if chapters:
        q_words = {w for w in re.findall(r"\w+", query.lower()) if len(w) > 3}
        best = None
        for ch in chapters:
            t = (ch.get("title") or "").lower()
            ov = len(q_words & set(re.findall(r"\w+", t)))
            if best is None or ov > best[0]:
                best = (ov, ch)
        ch = best[1]
        start = float(ch.get("start_time") or 0)
        end = ch.get("end_time")
        end = float(end) if end else min(start + want_sec, dur)
        # ограничим длину окна до want_sec (берём начало главы)
        return start, min(start + want_sec, end if end > start else start + want_sec)
    # нет глав → скип интро ~12%, но не дальше чем dur-want
    start = min(max(dur * 0.12, 3.0), max(dur - want_sec, 0.0))
    return start, start + want_sec


def select_clip(
    query: str,
    candidates: List[Dict],
    *,
    fact: str = "",
    want_sec: float = 6.0,
    llm_pick: Optional[Callable[[str, str, List[Dict]], Optional[Dict]]] = None,
    fetch_details: bool = True,
) -> Optional[Dict]:
    """Выбирает ролик + клип-окно из кандидатов.

    llm_pick(fact, query, candidates) -> {"index": int, "clip_start": float,
        "clip_end": float, "reason": str} | None
        — если задан, доверяем выбор LLM (по заголовкам/описаниям). Иначе эвристика.

    Возвращает {url, title, channel, clip_start, clip_end, reason, candidate}
    или None если кандидатов нет.
    """
    cands = [c for c in candidates if c.get("url")]
    if not cands:
        return None

    if llm_pick is not None:
        try:
            pick = llm_pick(fact, query, cands)
        except Exception as e:
            log.warning(f"  llm_pick упал, откат на эвристику: {str(e)[:160]}")
            pick = None
        if pick and 0 <= pick.get("index", -1) < len(cands):
            c = cands[pick["index"]]
            cs = float(pick.get("clip_start", 0.0))
            ce = float(pick.get("clip_end", cs + want_sec))
            if ce <= cs:
                ce = cs + want_sec
            return {
                "url": c["url"], "title": c["title"], "channel": c["channel"],
                "clip_start": cs, "clip_end": ce,
                "reason": pick.get("reason", "llm"), "candidate": c,
            }
        log.info("  llm_pick без результата → эвристика")

    # эвристика
    ranked = sorted(cands, key=lambda c: _score_candidate(c, query), reverse=True)
    best = ranked[0]
    detail = fetch_video_details(best["url"]) if fetch_details else None
    cs, ce = _heuristic_window(detail, best, want_sec, query)
    return {
        "url": best["url"], "title": best["title"], "channel": best["channel"],
        "clip_start": round(cs, 2), "clip_end": round(ce, 2),
        "reason": f"heuristic score={_score_candidate(best, query):.1f}",
        "candidate": best,
    }


def auto_archive_clip(
    query: str,
    project_dir: Path,
    scene_id: str,
    *,
    fact: str = "",
    want_sec: float = 6.0,
    n: int = 8,
    llm_pick: Optional[Callable] = None,
) -> Optional[Dict]:
    """End-to-end: поиск → выбор → скачивание+нарезка через youtube_clipper.

    Возвращает dict от fetch_clip (+ поля title/channel/reason) или None.
    Сетевые/cookie-ошибки скачивания не валят пайплайн — просто None (fallback
    на Wikimedia/сток сработает выше по иерархии Stage 4).
    """
    cands = search_candidates(query, n=n)
    if not cands:
        log.info(f"  {scene_id}: ytsearch '{query}' — пусто")
        return None
    sel = select_clip(query, cands, fact=fact, want_sec=want_sec, llm_pick=llm_pick)
    if not sel:
        return None
    log.info(
        f"  {scene_id}: выбран '{sel['title'][:60]}' "
        f"[{sel['clip_start']:.1f}-{sel['clip_end']:.1f}s] ({sel['reason']})"
    )
    from services.stocks.youtube_clipper import fetch_clip
    res = fetch_clip(
        url=sel["url"],
        clip_start=sel["clip_start"],
        clip_end=sel["clip_end"],
        project_dir=project_dir,
        scene_id=scene_id,
        caption=f"{sel['title']} — {sel['channel']} (YouTube)",
    )
    if res is None:
        return None
    res.update({"title": sel["title"], "channel": sel["channel"],
                "reason": sel["reason"], "source": "youtube-auto"})
    return res
