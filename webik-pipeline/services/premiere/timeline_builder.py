"""
services/premiere/timeline_builder.py
Раскладка ассетов на таймлайн в Premiere.

Минимальная версия для вертикального среза C:
- A1: один файл голоса целиком, начало в 0:00
- V1: картинки/видео сцен, длительность каждой = scene.duration_sec,
       старт = накопленная длительность предыдущих сцен
- Без Ken Burns / эффектов / переходов на этом шаге (рисковый shake-out)

Дальше расширим: motion keyframes (zoom для картинок), cross-dissolve,
LUT, .mogrt оверлеи, beat-cuts по WhisperX.
"""
from pathlib import Path
from typing import Dict, List, Optional

import pymiere
from PIL import Image
from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from core.exceptions import StageError
from services.premiere.pymiere_wrapper import (
    create_sequence,
    get_active_sequence,
    import_files,
)
from services.premiere.effects import (
    apply_ken_burns,
    apply_dip_to_black_fade,
    apply_static_scale,
    compute_fit_scale_pct,
    find_clip_by_timeline_start,
    mute_linked_audio,
)
from services.premiere.transitions import (
    TransitionType,
    choose_transition_type,
    fade_duration_for,
)

log = setup_logger("timeline")

# Ken Burns: процент перекрытия fit_scale в начале/конце клипа.
# 1.05 = на 5% больше fit (запас на «дыхание»), 1.20 = +20% к концу (заметный zoom).
KEN_BURNS_START_MULT = 1.05
KEN_BURNS_END_MULT = 1.20


def build_rough_cut(
    scenes: List[Dict],
    voice_path: Path,
    media_paths: Dict[str, Dict],
    scene_timings: Optional[Dict[str, Dict]] = None,
    whisper_words: Optional[List[Dict]] = None,
    whisper_sentences: Optional[List[Dict]] = None,
    project_dir: Optional[Path] = None,
    sequence_name: str = "Webik Rough Cut",
    width: int = 1920,
    height: int = 1080,
    framerate: int = 30,
    primary_preset: Optional[str] = None,
    level_titles: Optional[Dict[int, str]] = None,
) -> "pymiere.Sequence":
    """Собирает базовый таймлайн.

    Args:
        scenes: список сцен из scenes.json
        voice_path: единый файл голоса (mp3)
        media_paths: {scene_id: {"path": Path, "kind": "image"|"video"}}.
            Для image — Ken Burns + dip-to-black. Для video — trim + static fit_scale + audio mute.
        scene_timings: реальные тайминги из alignment.json
            {scene_id: {"start": float, "end": float}}.
            Если None — используем scene.duration_sec накопительно (старое поведение).

    Returns sequence.
    """
    if not voice_path.exists():
        raise StageError(5, f"Файл голоса не найден: {voice_path}")

    # 1. Создаём sequence
    sequence = create_sequence(sequence_name, width, height, framerate)

    # 2. Импортируем все файлы одним пакетом (быстрее)
    files_to_import: List[Path] = [voice_path]
    for scene in scenes:
        sid = scene["id"]
        media = media_paths.get(sid)
        if media:
            mp = media.get("path")
            if mp and Path(mp).exists():
                files_to_import.append(Path(mp))

    items = import_files(files_to_import)

    # Создаём mapping имя_файла → ProjectItem
    # (importFiles может вернуть items в другом порядке; ищем по имени)
    items_by_name = {item.name: item for item in items}

    voice_item = _find_item_by_path(items_by_name, voice_path)
    if not voice_item:
        raise StageError(5, f"Не нашёл импортированный голос: {voice_path.name}")

    # 3. Кладём голос на A1 в 0:00
    audio_track = sequence.audioTracks[0]
    audio_track.insertClip(voice_item, time_from_seconds(0.0))
    log.info(f"A1: вставлен голос {voice_path.name}")

    # 4. Считаем butt-joined тайминги (клипы встык, cut в midpoint whisper-паузы)
    butt_timings = _butt_join_timings(scenes, scene_timings or {})
    # Считаем fade-in/fade-out для каждой сцены на основе матрицы переходов
    fade_pairs = _compute_fade_pairs(scenes)

    # Раскладываем картинки на V1 по butt-таймингам
    video_track = sequence.videoTracks[0]
    placed = 0
    cursor_sec = 0.0
    last_end = 0.0
    ken_burns_ok = 0
    fades_ok = 0

    for idx, scene in enumerate(scenes):
        sid = scene["id"]
        bt = butt_timings.get(sid)
        if bt:
            start_sec = float(bt["start"])
            end_sec = float(bt["end"])
            duration = end_sec - start_sec
            timing_src = "butt"
        else:
            start_sec = cursor_sec
            duration = float(scene.get("duration_sec", 5.0))
            end_sec = start_sec + duration
            timing_src = "fallback"

        fade_in_sec, fade_out_sec, t_in, t_out = fade_pairs[idx]
        media = media_paths.get(sid) or {}
        media_path = Path(media["path"]) if media.get("path") else None
        kind = media.get("kind", "image")

        if media_path and media_path.exists():
            item = _find_item_by_path(items_by_name, media_path)
            if item:
                video_track.insertClip(item, time_from_seconds(start_sec))
                _set_clip_duration(sequence, video_track, start_sec, duration)

                clip = find_clip_by_timeline_start(video_track, start_sec)
                if clip is not None:
                    fit_pct = _compute_fit_scale_for_media(
                        media_path, kind, frame_w=width, frame_h=height
                    )

                    if kind == "image":
                        start_pct = fit_pct * KEN_BURNS_START_MULT
                        end_pct = fit_pct * KEN_BURNS_END_MULT
                        if apply_ken_burns(clip, start_pct, end_pct):
                            ken_burns_ok += 1
                        scale_log = f"scale {start_pct:.0f}%→{end_pct:.0f}%"
                    else:
                        # Video — статический fit_scale, mute linked audio
                        apply_static_scale(clip, fit_pct)
                        muted = mute_linked_audio(clip)
                        scale_log = f"video scale {fit_pct:.0f}% (audio muted x{muted})"

                    if fade_in_sec > 0 or fade_out_sec > 0:
                        if apply_dip_to_black_fade(
                            clip,
                            fade_in_sec=fade_in_sec,
                            fade_out_sec=fade_out_sec,
                            do_fade_in=fade_in_sec > 0,
                            do_fade_out=fade_out_sec > 0,
                        ):
                            fades_ok += 1

                    log.info(
                        f"  V1 {sid}: {start_sec:.2f}s→{end_sec:.2f}s "
                        f"(dur={duration:.2f}s, kind={kind}, src={timing_src}, "
                        f"{scale_log}, "
                        f"in:{t_in.value}={fade_in_sec:.2f}s, "
                        f"out:{t_out.value}={fade_out_sec:.2f}s)"
                    )
                else:
                    log.warning(f"  V1 {sid}: не нашёл вставленный clip для эффектов")
                placed += 1
            else:
                log.warning(f"Не нашёл импортированный item для {media_path.name}")
        else:
            log.warning(f"Сцена {sid}: нет медиа, пропускаю (будет чёрный кадр)")

        cursor_sec = end_sec
        last_end = end_sec

    log.info(
        f"V1: размещено {placed}/{len(scenes)} сцен, "
        f"Ken Burns {ken_burns_ok}/{placed}, fades {fades_ok}/{placed}, "
        f"total={last_end:.2f}s"
    )

    # 4b. Cleanup V1 ghost-клипов (доли секунды от leftover insert'ов)
    removed = _cleanup_short_clips(video_track, threshold_sec=0.1, label="V1")
    if removed:
        log.info(f"V1: cleanup убрал {removed} ghost-клип(ов) <0.1s")

    # 5. Film burn overlays на V2 для FILM_BURN стыков (между уровнями айсберга)
    from core.config import get_settings
    from services.premiere.film_burn import place_film_burns
    from services.premiere.sfx import place_sfx
    s = get_settings()
    if s.film_burn_dir and Path(s.film_burn_dir).exists():
        seed = abs(hash(sequence_name)) % (2**32)
        n_burns = place_film_burns(
            sequence, scenes, butt_timings, fade_pairs, Path(s.film_burn_dir), seed=seed
        )
        if n_burns:
            log.info(f"V2: film burn размещён на {n_burns} стыках")

    # 6. SFX по trigger_word на A3 (Old Sport SFX Pack)
    if s.sfx_dir and Path(s.sfx_dir).exists() and whisper_words:
        sfx_seed = abs(hash(f"sfx-{sequence_name}")) % (2**32)
        n_sfx = place_sfx(
            sequence, scenes, whisper_words, Path(s.sfx_dir),
            seed=sfx_seed, total_duration_sec=last_end,
        )
        if n_sfx:
            log.info(f"A3: SFX размещён в {n_sfx} точках по trigger_word")

    # 7. Subtitles на каждое предложение — ОТКЛЮЧЕНО (заменены entity overlays ниже).
    # Код в services/premiere/subtitle_placer.py переиспользуем для chapter-cards.

    # 7b. Entity overlays на V3 (даты/имена/числа/места) с Wikipedia-фото для PERSON
    if whisper_words and project_dir:
        from services.premiere.entity_overlay_placer import place_entity_overlays
        # Полный voiceover текст: собираем из scenes
        voiceover_full = " ".join(
            (s.get("voiceover") or "").strip() for s in scenes if s.get("voiceover")
        )
        if voiceover_full:
            n_cards = place_entity_overlays(
                sequence, voiceover_full, whisper_words, project_dir,
                frame_w=width, frame_h=height,
            )
            if n_cards:
                log.info(f"V3: entity overlays размещены ({n_cards} карточек)")

    # 7c. Iceberg level title cards на V4 (при смене level)
    if project_dir:
        from services.premiere.level_card_placer import place_level_overlays
        n_levels = place_level_overlays(
            sequence, scenes, butt_timings, project_dir,
            frame_w=width, frame_h=height,
            level_titles=level_titles,
        )
        if n_levels:
            log.info(f"V4: level title cards размещены ({n_levels})")

    # 7d. Animated overlays: V5 grain (OFF by default), V6 light leaks, V7 vignette
    if project_dir:
        from services.premiere.animated_overlays import (
            place_grain_overlay,
            place_light_leak_on_cuts,
            place_vignette_overlay,
        )
        # total = последняя сцена end (по butt) или последняя whisper
        total_dur = 0.0
        for sid in (s["id"] for s in scenes):
            bt = butt_timings.get(sid)
            if bt and bt.get("end") is not None:
                total_dur = max(total_dur, float(bt["end"]))
        if total_dur > 0:
            # V5 grain отключён по умолчанию (user сказал «не корректно появляется»).
            # Раскомментируй когда найдём качественный источник зерна (текущий
            # Dust Texture.mp4 1280x720 нужно scale 150% → блёкло выглядит).
            # n_grain = place_grain_overlay(
            #     sequence, total_dur, project_dir,
            #     frame_w=width, frame_h=height,
            # )
            # if n_grain:
            #     log.info(f"V5: film grain overlay размещён ({n_grain} loops)")

            # Light leaks на level↑ моментах (драматический подсвет)
            level_cuts = []
            prev_lvl = None
            for s in scenes:
                cur_lvl = int(s.get("level", 0))
                if prev_lvl is not None and cur_lvl > prev_lvl:
                    bt = butt_timings.get(s["id"])
                    if bt:
                        level_cuts.append(float(bt["start"]))
                prev_lvl = cur_lvl
            if level_cuts:
                n_leak = place_light_leak_on_cuts(
                    sequence, level_cuts, project_dir,
                    frame_w=width, frame_h=height,
                )
                if n_leak:
                    log.info(f"V6: light leaks на level cuts ({n_leak})")

            n_vig = place_vignette_overlay(
                sequence, total_dur, project_dir,
                frame_w=width, frame_h=height,
            )
            if n_vig:
                log.info(f"V7: vignette overlay ({total_dur:.1f}s)")

    # 7e. Animated charts на V8 (counter / donut / rank_bar по scene.charts[])
    if project_dir and whisper_words:
        from services.premiere.chart_placer import place_charts
        n_charts = place_charts(
            sequence, scenes, whisper_words, project_dir,
            total_duration_sec=last_end,
            frame_w=width, frame_h=height,
        )
        if n_charts:
            log.info(f"V8: animated charts размещены ({n_charts})")

    # 7f. Media bursts на V9 (beat-cuts на перечислениях по scene.media_burst)
    if project_dir and whisper_words:
        from services.premiere.media_burst_placer import place_media_bursts
        # NB: переменная `s` выше перезатёрта внутри `for s in scenes` — load заново
        _settings = get_settings()
        burst_seed = abs(hash(f"burst-{sequence_name}")) % (2**32)
        n_burst = place_media_bursts(
            sequence, scenes, whisper_words, project_dir,
            sfx_dir=Path(_settings.sfx_dir) if _settings.sfx_dir else None,
            seed=burst_seed,
            frame_w=width, frame_h=height,
        )
        if n_burst:
            log.info(f"V9: media bursts размещены ({n_burst} cuts)")

    # 7g. Outro CTA card на V10 (ПОДПИШИСЬ + название канала, в конце таймлайна)
    if project_dir:
        from services.premiere.outro_placer import place_outro_card
        if place_outro_card(
            sequence,
            project_dir,
            content_end_sec=last_end,
            frame_w=width, frame_h=height,
        ):
            log.info(f"V10: outro CTA добавлена в конце ({last_end:.2f}s+)")

    # 8. Музыка-фон — НЕ ставим автоматически (пользователь сам подбирает треки).
    # services/premiere/music.py оставлен как dead code на случай возврата.

    # 8. Маскот «бебрик» — отложено. Требует visual_modes в scenes.json
    # (fullscreen / split_left / with_chart). Код в services/premiere/mascot.py.

    return sequence


def _compute_fit_scale_for_media(path: Path, kind: str, frame_w: int, frame_h: int) -> float:
    """Прочитать размер медиа (image через PIL, video через ffprobe) и вычислить fit-scale %."""
    try:
        if kind == "image":
            with Image.open(path) as im:
                iw, ih = im.size
        else:
            import ffmpeg
            probe = ffmpeg.probe(str(path))
            iw, ih = frame_w, frame_h
            for stream in probe.get("streams", []):
                if stream.get("codec_type") == "video":
                    iw = int(stream.get("width", frame_w))
                    ih = int(stream.get("height", frame_h))
                    break
        return compute_fit_scale_pct(iw, ih, frame_w, frame_h)
    except Exception as e:
        log.warning(f"Не смог прочитать размер {path.name}: {e}, scale=100%")
        return 100.0


def _butt_join_timings(
    scenes: List[Dict], whisper_timings: Dict[str, Dict]
) -> Dict[str, Dict]:
    """Расширяет тайминги сцен чтобы они стыковались встык.

    Cut между сценами ставим в **середину** whisper-паузы — диктор делает
    вдох ровно на смене кадра, без чёрной дыры.

    Первая сцена начинается с 0.0, последняя кончается на whisper end.
    Если whisper не даёт timing для какой-то сцены — пропускаем её (fallback
    в build_rough_cut на duration_sec).
    """
    if not scenes:
        return {}

    sids = [s["id"] for s in scenes]
    levels = [int(s.get("level", 0)) for s in scenes]
    out: Dict[str, Dict] = {}

    for i, sid in enumerate(sids):
        wt = whisper_timings.get(sid)
        if not wt:
            continue
        new_t = dict(wt)

        if i == 0:
            new_t["start"] = 0.0
        else:
            prev_wt = whisper_timings.get(sids[i - 1])
            if prev_wt:
                # Если уровень повышается на этой границе — оставляем РЕАЛЬНЫЙ gap
                # (драматическая пауза для level title card).
                if levels[i] > levels[i - 1]:
                    new_t["start"] = float(wt["start"])
                else:
                    midpoint = (float(prev_wt["end"]) + float(wt["start"])) / 2.0
                    new_t["start"] = midpoint

        if i < len(sids) - 1:
            next_wt = whisper_timings.get(sids[i + 1])
            if next_wt:
                if levels[i + 1] > levels[i]:
                    # Текущая сцена кончается на конце голоса — не extending в gap
                    new_t["end"] = float(wt["end"])
                else:
                    midpoint = (float(wt["end"]) + float(next_wt["start"])) / 2.0
                    new_t["end"] = midpoint
        # i == last → end оставляем = whisper end (= конец голоса)

        out[sid] = new_t

    return out


def _compute_fade_pairs(scenes: List[Dict]):
    """Для каждой сцены возвращает (fade_in_sec, fade_out_sec, t_in, t_out).

    t_in — TransitionType стыка (prev → current).
    t_out — TransitionType стыка (current → next).
    На границах sequence (вход первой / выход последней) → JUST_CUT (без fade).
    """
    pairs = []
    n = len(scenes)
    for i, scene in enumerate(scenes):
        prev_scene = scenes[i - 1] if i > 0 else None
        next_scene = scenes[i + 1] if i < n - 1 else None

        t_in = choose_transition_type(prev_scene, scene)
        t_out = choose_transition_type(scene, next_scene)

        fade_in = fade_duration_for(t_in)
        fade_out = fade_duration_for(t_out)
        pairs.append((fade_in, fade_out, t_in, t_out))
    return pairs


def _find_item_by_path(items_by_name: Dict[str, "pymiere.ProjectItem"], path: Path):
    """Premiere сохраняет имя файла без расширения для stills и с — для видео.
    Пробуем оба варианта."""
    name_with_ext = path.name
    name_no_ext = path.stem
    return items_by_name.get(name_with_ext) or items_by_name.get(name_no_ext)


def _cleanup_short_clips(track, threshold_sec: float = 0.1, label: str = "V?") -> int:
    """Удаляет слишком короткие клипы с трека (ghost-clips от leftover insert'ов).

    Pymiere `insertClip` иногда оставляет sub-frame remnants после ripple-edits;
    они проявляются как clip с duration < frame (33ms на 30fps). Считаем
    threshold_sec=0.1 безопасным минимумом — реальные клипы у нас ≥ 0.5s.

    Iterate backwards чтобы remove() не сбивал индексы оставшихся клипов.
    Returns кол-во удалённых.
    """
    removed = 0
    n = _safe_num_items(track)
    for i in range(n - 1, -1, -1):
        try:
            clip = track.clips[i]
            dur = clip.end.seconds - clip.start.seconds
        except Exception:
            continue
        if 0 < dur < threshold_sec:
            try:
                # remove(inRipple=False, inAlignToVideo=False) — без сдвига остального
                clip.remove(False, False)
                removed += 1
                log.info(f"  {label}: удалён ghost-clip dur={dur*1000:.0f}ms")
            except Exception as e:
                log.warning(f"  {label}: не смог remove ghost-clip ({e})")
    return removed


def _safe_num_items(track) -> int:
    """tolerant numItems read."""
    try:
        return int(track.clips.numItems)
    except Exception:
        return 0


def _set_clip_duration(sequence, track, start_sec: float, duration_sec: float):
    """Находит последний вставленный клип на треке в районе start_sec и
    устанавливает ему длительность.

    Premiere для still-images по умолчанию ставит длительность из preferences
    (обычно 5 сек). Подрежем end-point точно под scene.duration_sec.
    """
    # Ищем clip который начинается в start_sec
    for i in range(track.clips.numItems):
        clip = track.clips[i]
        clip_start = clip.start.seconds
        if abs(clip_start - start_sec) < 0.05:
            new_end = start_sec + duration_sec
            clip.end = time_from_seconds(new_end)
            return
    log.warning(f"Не нашёл клип в start={start_sec:.2f}s для подгонки длительности")
