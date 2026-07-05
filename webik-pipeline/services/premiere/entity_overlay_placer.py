"""
services/premiere/entity_overlay_placer.py
Размещает entity overlay-карточки на V3 в момент произнесения каждой entity.

Поток:
1. NER на полном тексте voiceover → entities с тайм-стампами
2. Для PERSON — пытаемся скачать фото из Wikipedia
3. Рендерим entity card PNG (news ticker)
4. Импорт в Premiere → insertClip на V3 в entity.start, длительность 1.8s
   с fade-in 0.15s + fade-out 0.20s

Если две entities очень близки (overlap) — оставляем только первую,
чтобы не путать зрителя.
"""
import re
from pathlib import Path
from typing import Dict, List, Optional

from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from services.premiere.effects import (
    apply_dip_to_black_fade,
    find_clip_by_timeline_start,
)
from services.premiere.pymiere_wrapper import import_files
from services.text.entity_card import render_typewriter_card
from services.text.ner import extract_entities

log = setup_logger("entity_overlay")

# Минимальный интервал между двумя карточками (чтобы typewriter одной не наезжал на другую)
MIN_CARD_GAP_SEC = 1.5


def _safe_filename(s: str) -> str:
    s = re.sub(r"[^\wЀ-ӿ\- ]", "_", s, flags=re.UNICODE)
    return s.strip()[:60]


def place_entity_overlays(
    sequence,
    voiceover_text: str,
    whisper_words: List[Dict],
    project_dir: Path,
    frame_w: int = 1920,
    frame_h: int = 1080,
) -> int:
    """Извлекает entities → рендерит карточки → кладёт на V3.

    Returns кол-во размещённых карточек.
    """
    if not voiceover_text or not whisper_words:
        log.info("Нет voiceover/whisper-words для NER")
        return 0

    entities = extract_entities(voiceover_text, whisper_words)
    if not entities:
        log.info("NER не нашёл entities в тексте")
        return 0
    log.info(f"NER нашёл {len(entities)} entities: " + ", ".join(
        f"{e['type']}:{e['text']}" for e in entities[:6]
    ) + ("..." if len(entities) > 6 else ""))

    cards_dir = project_dir / "assets" / "entity_cards"
    photos_dir = project_dir / "assets" / "wiki_photos"
    cards_dir.mkdir(parents=True, exist_ok=True)
    photos_dir.mkdir(parents=True, exist_ok=True)

    video_tracks = sequence.videoTracks
    if video_tracks.numTracks < 3:
        log.warning(
            f"V3 нет в sequence ({video_tracks.numTracks} tracks) — карточки не положу"
        )
        return 0
    v3 = video_tracks[2]

    # Wikipedia photo client (lazy)
    wiki_client = None

    # Дедуп с учётом MIN_CARD_GAP_SEC (ближайшие карточки слипаются — берём первую)
    chosen: List[Dict] = []
    last_t = -10.0
    for ent in entities:
        if ent["start"] - last_t < MIN_CARD_GAP_SEC:
            continue
        chosen.append(ent)
        last_t = ent["start"]
    log.info(f"После dedup осталось {len(chosen)} карточек")

    # 1. Рендерим typewriter .mov (с alpha) — может занять секунды/карточку
    # rendered: list of (ent, mov_path, duration_sec) — только успешно отрендеренные
    rendered: List[tuple] = []
    for i, ent in enumerate(chosen):
        photo_path: Optional[Path] = None
        if ent["type"] == "PERSON":
            if wiki_client is None:
                try:
                    from services.stocks.wikipedia_photo import WikipediaPhotoClient
                    wiki_client = WikipediaPhotoClient()
                except Exception as e:
                    log.warning(f"Wikipedia client init failed: {e}")
                    wiki_client = False
            if wiki_client:
                cached_photo = photos_dir / f"{_safe_filename(ent['text'])}.jpg"
                if cached_photo.exists():
                    photo_path = cached_photo
                else:
                    try:
                        downloaded = wiki_client.download_photo(ent["text"], cached_photo)
                        if downloaded:
                            photo_path = downloaded
                            log.info(f"  wiki photo для '{ent['text']}' → {cached_photo.name}")
                    except Exception as e:
                        log.warning(f"  wiki photo failed для '{ent['text']}': {e}")

        # Cache key включает hash контента — при изменении текста файл пере-рендерится,
        # при повторном demo с тем же entity — мгновенный cache hit (избегаем ffmpeg
        # [Errno 22] при попытке overwrite файла, который Premiere может держать).
        import hashlib
        content_key = hashlib.md5(
            f"{ent['type']}|{ent['text']}|{frame_w}x{frame_h}".encode("utf-8")
        ).hexdigest()[:8]
        out_mov = cards_dir / f"card_{i:03d}_{ent['type']}_{content_key}.mov"

        if out_mov.exists() and out_mov.stat().st_size > 1000:
            # Кэш: длительность вычисляем как в render_typewriter_card
            from services.text.entity_card import (
                TYPING_CHARS_PER_SEC as _TYP,
                HOLD_AFTER_TYPING_SEC as _HOLD,
                FADE_OUT_SEC as _FADE,
            )
            n_chars = max(1, len(ent["text"]))
            dur = n_chars / _TYP + _HOLD + _FADE
            log.info(f"  card cache hit '{ent['text']}' → {out_mov.name}")
        else:
            try:
                _, dur = render_typewriter_card(
                    ent["type"], ent["text"], out_mov,
                    photo_path=photo_path,
                    frame_w=frame_w, frame_h=frame_h,
                )
            except Exception as e:
                log.warning(f"  card render failed для '{ent['text']}': {e}")
                continue
        rendered.append((ent, out_mov, dur))

    if not rendered:
        log.warning("Ни одна карточка не отрендерилась")
        return 0

    # 2. Импорт всех .mov одним пакетом
    imported = import_files([m for _, m, _ in rendered])
    items_by_name = {it.name: it for it in imported}

    placed = 0
    for i, (ent, mov_path, dur) in enumerate(rendered):
        item = items_by_name.get(mov_path.name) or items_by_name.get(mov_path.stem)
        if item is None:
            log.warning(f"  card {i}: не нашёл импортированный item ({mov_path.name})")
            continue

        start = float(ent["start"])
        try:
            v3.insertClip(item, time_from_seconds(start))
        except Exception as e:
            log.warning(f"  card {i}: V3.insertClip упал: {e}")
            continue

        # Длительность .mov естественная (Premiere сам определит).
        # Без opacity-fade — fade уже вшит в alpha-канал .mov.

        placed += 1
        log.info(
            f"  V3 card[{i}] {ent['type']}:'{ent['text']}' "
            f"@{start:.2f}s, dur={dur:.2f}s"
        )

    return placed
