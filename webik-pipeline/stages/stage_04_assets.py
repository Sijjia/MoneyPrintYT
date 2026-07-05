"""
Stage 4: Ассеты

scenes.json → assets/{voice/, images/, alignment.json}

Что делает:
1. Voicer TTS → один mp3 голоса (с переиспользованием если уже есть).
2. Whisper alignment → точные word-timestamps + per-scene start/end.
3. Для каждой сцены — выбор медиа в порядке приоритета:
   a. Local CLIP search в `.media_index/` (E:\YouTube Webik) — если top-1 score >= 0.25
   b. Pexels download — fallback

Manifest schema:
   {scene_id: {path, query, kind: image|video, source: local|pexels, score?}}

Что НЕ делает: 3D-камера, Flux, Suno, Pixabay (ключа нет), Wikimedia.
"""
import json
from pathlib import Path
from typing import Optional

from core.logger import setup_logger
from core.state import Stage, StateManager
from core.exceptions import StageError
from services.tts.voicer import VoicerTTS
from services.stt.aligner import (
    align_with_whisper,
    align_proportional,
    proportional_scene_timings,
    save_alignment,
)
from services.images.pexels import PexelsClient
from services.stocks.pexels_videos import PexelsVideosClient
from services.stocks.pixabay import PixabayClient
from services.stocks.wikimedia import WikimediaClient
from services.visual.parallax import render_parallax_video

log = setup_logger("stage4")

PARALLAX_MIN_SCENE_SEC = 2.0   # короче — не имеет смысла параллаксить
PARALLAX_DURATION_PAD = 1.5    # рендерим с запасом, Stage 5 обрежет butt-trim'ом


def run(project_dir: Path, feedback: Optional[str] = None) -> dict:
    log.info("[bold cyan]Stage 4: Ассеты (минимальная версия)[/]")

    state_manager = StateManager(project_dir)
    state = state_manager.load()
    state.mark_running(Stage.ASSETS)
    state_manager.save(state)

    try:
        scenes_path = project_dir / "scenes.json"
        if not scenes_path.exists():
            raise StageError(4, f"Не найден scenes.json в {project_dir}")
        scenes_data = json.loads(scenes_path.read_text(encoding="utf-8"))
        scenes = scenes_data["scenes"]

        assets_dir = project_dir / "assets"
        voice_dir = assets_dir / "voice"
        images_dir = assets_dir / "images"
        voice_dir.mkdir(parents=True, exist_ok=True)
        images_dir.mkdir(parents=True, exist_ok=True)

        # 1. Собираем единый voiceover (паузы между уровнями добавим уже в mp3,
        #    SSML break Voicer часто игнорирует)
        full_text_parts = [s.get("voiceover", "").strip() for s in scenes if s.get("voiceover")]
        full_text = " ".join(full_text_parts)
        if not full_text:
            raise StageError(4, "В scenes.json нет ни одного voiceover")

        voice_path = voice_dir / "full.mp3"
        if voice_path.exists() and voice_path.stat().st_size > 1000:
            log.info(f"TTS: переиспользую {voice_path.name} ({voice_path.stat().st_size // 1024} KB)")
        else:
            log.info(f"TTS: генерирую {len(full_text_parts)} сегментов = {len(full_text)} символов")
            tts = VoicerTTS()
            tts.synthesize(full_text, voice_path)

        # 2. Alignment текста к аудио — пробуем whisper, fallback на proportional
        log.info("Alignment: запускаю whisper для точных word-timestamps...")
        try:
            alignment = align_with_whisper(scenes, voice_path)
        except Exception as e:
            log.warning(f"Whisper alignment упал ({e}), fallback на proportional")
            alignment = align_proportional(full_text, voice_path)
            alignment["scenes"] = proportional_scene_timings(scenes, alignment["duration"])

        # 2b. Нормализация пауз перед level↑: если TTS оставил гигантский gap
        # (типично 5-9s после точки) — урезаем до target. Если коротко — добавляем.
        # Маркер «paused_at_levels» в alignment предотвращает повторную обработку.
        already_paused = bool(alignment.get("paused_at_levels"))
        if not already_paused and _normalize_level_pauses(voice_path, scenes, alignment, target_pause_sec=1.5):
            log.info("Voice: нормализованы паузы перед уровнями, re-run whisper alignment")
            try:
                alignment = align_with_whisper(scenes, voice_path)
            except Exception as e:
                log.warning(f"Whisper re-align упал ({e}), оставляю старый alignment со сдвигом")
            alignment["paused_at_levels"] = True
        elif already_paused:
            log.info("Voice уже содержит нормализованные drama pauses (skip)")

        save_alignment(alignment, assets_dir / "alignment.json")

        # 3. Картинки для каждой сцены — переиспользуем если уже есть полный manifest
        manifest_path = images_dir / "manifest.json"
        if manifest_path.exists():
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            covered = all(
                manifest.get(s["id"], {}).get("path")
                and (project_dir / manifest[s["id"]]["path"]).exists()
                for s in scenes
            )
        else:
            manifest = {}
            covered = False

        if covered:
            log.info(f"Images: переиспользую manifest ({len(manifest)} сцен)")
        else:
            log.info(f"Images: подбираю медиа для {len(scenes)} сцен (local CLIP → Pexels)...")
            manifest = _build_media_manifest(scenes, project_dir, images_dir)
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
            )

        # 4. Финал
        result = {
            "voice_path": str(voice_path.relative_to(project_dir)),
            "alignment_path": "assets/alignment.json",
            "images_manifest": "assets/images/manifest.json",
            "voice_duration_sec": alignment["duration"],
            "images_found": sum(1 for v in manifest.values() if v.get("path")),
            "images_missing": sum(1 for v in manifest.values() if not v.get("path")),
        }

        state.mark_awaiting(Stage.ASSETS)
        state_manager.save(state)

        log.info(f"[green]✓[/] Stage 4 готов")
        log.info(f"  Голос: {result['voice_duration_sec']:.1f}s")
        log.info(f"  Картинки: {result['images_found']}/{len(scenes)}")
        return result

    except Exception as e:
        state.mark_failed(Stage.ASSETS, str(e))
        state_manager.save(state)
        raise


# CLIP min similarity для использования локального файла. Ниже — fallback на Pexels.
# 0.25 пропускал почти любую тёмную картинку как «совпадение» для незнакомых тем
# (Snickers 1992 для мицелия, Minecraft для Орегонского леса). 0.40 заставляет
# использовать local только когда CLIP уверен, иначе — стоки.
LOCAL_CLIP_MIN_SCORE = 0.40


def _build_media_manifest(scenes, project_dir: Path, images_dir: Path) -> dict:
    """Подбирает медиа для каждой сцены: local CLIP > Pexels.

    Returns manifest dict в формате:
        {sid: {path, query, kind: image|video, source: local|pexels, score?}}

    Для local — path абсолютный (in-place из E:\\YouTube Webik\\).
    Для pexels — относительный к project_dir (скачанный в assets/images/).
    """
    # Lazy init: CLIP search, Wikimedia, Pexels, Pixabay — могут не понадобиться если manifest целиком local
    media_search = None
    wikimedia = None
    pexels_videos = None
    pixabay = None
    pexels = None
    manifest = {}

    for scene in scenes:
        sid = scene["id"]
        visual = scene.get("visual", {})
        query = visual.get("search_query") or visual.get("fallback_query") or sid

        # 0) YouTube clip — высший приоритет если LLM явно указал source_url
        # с clip_start/end. Используется для архивных кадров, реакций, интервью.
        if visual.get("type") == "youtube_clip" and visual.get("source_url"):
            clip_start = float(visual.get("clip_start", 0))
            clip_end = float(visual.get("clip_end", 0))
            if clip_end > clip_start:
                from services.stocks.youtube_clipper import fetch_clip
                result = fetch_clip(
                    url=visual["source_url"],
                    clip_start=clip_start,
                    clip_end=clip_end,
                    project_dir=project_dir,
                    scene_id=sid,
                    caption=visual.get("caption", ""),
                )
                if result:
                    manifest[sid] = {
                        "path": str(Path(result["path"]).relative_to(project_dir)),
                        "query": query,
                        "kind": "video",
                        "source": "youtube",
                        "source_url": result["source_url"],
                        "caption": result["caption"],
                    }
                    log.info(f"  {sid}: '{query}' → youtube clip {Path(result['path']).name}")
                    continue
                # Если yt-dlp/ffmpeg упали — падаем в обычный fallback ниже

        # 1) Local CLIP search
        if media_search is None:
            media_search = _try_init_media_search()
        local_hit = None
        if media_search is not None:
            try:
                results = media_search.search(
                    query, k=1, min_score=LOCAL_CLIP_MIN_SCORE, kind_filter="any"
                )
                if results:
                    path, score, kind = results[0]
                    local_hit = (path, score, kind)
            except Exception as e:
                log.warning(f"  {sid}: CLIP search упал ({e}) — иду на Pexels")

        if local_hit:
            path, score, kind = local_hit
            final_path = Path(path).resolve()
            if kind == "video":
                silent_target = (project_dir / "assets" / "videos_silent" / final_path.name).resolve()
                silent = _strip_video_audio(final_path, silent_target)
                if silent:
                    final_path = silent.resolve()
            manifest[sid] = {
                "path": str(final_path),
                "query": query,
                "kind": kind,
                "source": "local",
                "score": round(score, 3),
            }
            log.info(f"  {sid}: '{query}' → local {kind} score={score:.3f} ({final_path.name})")
            continue

        # 2) Wikimedia Commons (реальные архивные фото)
        if wikimedia is None:
            try:
                wikimedia = WikimediaClient()
            except Exception as e:
                log.warning(f"Wikimedia init failed: {e}")
        if wikimedia is not None:
            wm_out = images_dir / f"{sid}_wm.jpg"
            try:
                downloaded = wikimedia.search_and_download(query, wm_out)
                if downloaded:
                    manifest[sid] = {
                        "path": str(wm_out.relative_to(project_dir)),
                        "query": query,
                        "kind": "image",
                        "source": "wikimedia",
                    }
                    log.info(f"  {sid}: '{query}' → wikimedia {wm_out.name}")
                    continue
            except Exception as e:
                log.warning(f"  {sid}: Wikimedia ошибка ({e}), иду на Pexels")

        # 3) Pexels Videos — атмосферный B-roll вместо статичной картинки
        if pexels_videos is None:
            try:
                pexels_videos = PexelsVideosClient()
            except Exception as e:
                log.warning(f"PexelsVideos init failed: {e}")
        if pexels_videos is not None:
            scene_dur = float(scene.get("duration_sec", 5.0))
            # min: чуть короче сцены чтобы было что использовать; max: 1.5x сцены чтобы не качать гиганты
            min_dur = max(3, int(scene_dur * 0.6))
            max_dur = max(min_dur + 2, int(scene_dur * 2.0))
            video_stock_dir = project_dir / "assets" / "video_stock"
            v_out = video_stock_dir / f"{sid}.mp4"
            try:
                downloaded_v = pexels_videos.search_and_download(
                    query, v_out, min_duration=min_dur, max_duration=max_dur
                )
                if downloaded_v:
                    manifest[sid] = {
                        "path": str(v_out.relative_to(project_dir)),
                        "query": query,
                        "kind": "video",
                        "source": "pexels-video",
                    }
                    log.info(f"  {sid}: '{query}' → pexels-video {v_out.name}")
                    continue
            except Exception as e:
                log.warning(f"  {sid}: PexelsVideos ошибка ({e}), иду на Pexels images")

        # 3b) Pixabay Videos — fallback после Pexels Videos (больше variety стокового видео)
        if pixabay is None:
            try:
                pixabay = PixabayClient()
            except Exception as e:
                log.warning(f"Pixabay init failed: {e}")
        if pixabay is not None:
            scene_dur = float(scene.get("duration_sec", 5.0))
            video_stock_dir = project_dir / "assets" / "video_stock"
            v_out = video_stock_dir / f"{sid}_pixabay.mp4"
            try:
                # quality="small" даёт ровно 1920x1080 (Pixabay naming странное:
                # large=4K, medium=2.5K, small=Full HD, tiny=HD)
                downloaded_v = pixabay.search_and_download_video(query, v_out, quality="small")
                if downloaded_v:
                    manifest[sid] = {
                        "path": str(v_out.relative_to(project_dir)),
                        "query": query,
                        "kind": "video",
                        "source": "pixabay-video",
                    }
                    log.info(f"  {sid}: '{query}' → pixabay-video {v_out.name}")
                    continue
            except Exception as e:
                log.warning(f"  {sid}: Pixabay videos ошибка ({e}), иду на Pexels images")

        # 4) Pexels Images — последний fallback
        if pexels is None:
            try:
                pexels = PexelsClient()
            except Exception as e:
                log.warning(f"Pexels init failed: {e}")
                manifest[sid] = {"path": None, "query": query, "error": "no_pexels"}
                continue

        out = images_dir / f"{sid}.jpg"
        try:
            downloaded = pexels.search_and_download(query, out)
            if downloaded:
                manifest[sid] = {
                    "path": str(out.relative_to(project_dir)),
                    "query": query,
                    "kind": "image",
                    "source": "pexels",
                }
                log.info(f"  {sid}: '{query}' → pexels {out.name}")
            else:
                manifest[sid] = {"path": None, "query": query, "error": "not_found"}
                log.warning(f"  {sid}: '{query}' → НЕ НАЙДЕНО")
        except Exception as e:
            manifest[sid] = {"path": None, "query": query, "error": str(e)}
            log.warning(f"  {sid}: Pexels ошибка: {e}")

    # Post-process: для каждой image-сцены рендерим parallax mp4
    _add_parallax_to_image_scenes(scenes, manifest, project_dir)

    return manifest


def _add_parallax_to_image_scenes(scenes, manifest: dict, project_dir: Path) -> None:
    """Для каждого manifest entry с kind='image' запускаем parallax 3D рендер.

    Если успех — модифицирует manifest in-place: kind становится 'video',
    path указывает на parallax mp4, source остаётся (для трассировки),
    добавляется 'original_image_path' и 'parallax': True.
    """
    parallax_dir = project_dir / "assets" / "parallax"
    image_scenes = [
        s for s in scenes
        if manifest.get(s["id"], {}).get("kind") == "image"
        and manifest.get(s["id"], {}).get("path")
    ]
    if not image_scenes:
        return

    log.info(f"[parallax] планирую {len(image_scenes)} image-сцен → parallax 3D")
    parallax_dir.mkdir(parents=True, exist_ok=True)
    ok_count = 0

    for scene in image_scenes:
        sid = scene["id"]
        entry = manifest[sid]
        scene_dur = float(scene.get("duration_sec", 5.0))
        if scene_dur < PARALLAX_MIN_SCENE_SEC:
            log.info(f"  {sid}: scene_dur={scene_dur:.1f}s < min, оставляю image для Ken Burns")
            continue

        # Resolve abs path (для local — уже абсолютный, для downloaded — relative to project)
        raw = entry["path"]
        src_path = Path(raw)
        if not src_path.is_absolute():
            src_path = project_dir / raw
        if not src_path.exists():
            log.warning(f"  {sid}: исходный image не найден ({src_path}), пропускаю parallax")
            continue

        # Кэш по stem источника
        out_mp4 = parallax_dir / f"{sid}__{src_path.stem}.mp4"
        render_dur = scene_dur * PARALLAX_DURATION_PAD

        if out_mp4.exists() and out_mp4.stat().st_size > 10_000:
            log.info(f"  {sid}: parallax cache hit ({out_mp4.name})")
            success = True
        else:
            success = render_parallax_video(src_path, out_mp4, duration_sec=render_dur)

        if not success:
            log.warning(f"  {sid}: parallax failed — оставляю image для Ken Burns fallback")
            continue

        entry["original_image_path"] = entry["path"]
        entry["path"] = str(out_mp4.relative_to(project_dir))
        entry["kind"] = "video"
        entry["parallax"] = True
        # source оставляем как был (local/wikimedia/pexels) для трассировки
        ok_count += 1

    log.info(f"[parallax] готово: {ok_count}/{len(image_scenes)} сцен с parallax 3D")


def _normalize_level_pauses(
    voice_path: Path, scenes, alignment,
    target_pause_sec: float = 1.5,
    tolerance_sec: float = 0.3,
) -> bool:
    """Нормализует длину паузы перед каждым level↑ к target_pause_sec.

    TTS Voicer часто оставляет 5-10s паузу после конца предложения с точкой —
    это растягивает level card до уродливо-длинного hold'а. Эта функция:
      - Если |current_gap - target| <= tolerance → не трогаем
      - Если current_gap < target → добавляем silence до target
      - Если current_gap > target → режем (current_gap - target) из середины

    Returns True если mp3 модифицирован (значит надо re-run whisper).
    """
    # Собираем границы level↑ как (prev_end_sec, next_start_sec)
    boundaries: list[tuple[float, float, str, str]] = []
    scene_timings = alignment.get("scenes") or {}
    prev_level = None
    prev_sid = None
    for s in scenes:
        cur_level = int(s.get("level", 0))
        sid = s["id"]
        if prev_level is not None and cur_level > prev_level and prev_sid:
            prev_t = scene_timings.get(prev_sid, {}) or {}
            cur_t = scene_timings.get(sid, {}) or {}
            prev_end = prev_t.get("end")
            cur_start = cur_t.get("start")
            if prev_end is not None and cur_start is not None:
                boundaries.append((float(prev_end), float(cur_start), prev_sid, sid))
        prev_level = cur_level
        prev_sid = sid

    if not boundaries:
        return False

    try:
        from pydub import AudioSegment
    except Exception as e:
        log.warning(f"pydub недоступен ({e}) — паузы не нормализую")
        return False

    try:
        audio = AudioSegment.from_file(voice_path)
    except Exception as e:
        log.warning(f"Не смог загрузить voice mp3 ({e})")
        return False

    modified = False
    # Идём с конца — чтобы earlier offsets не сдвигались
    for prev_end_sec, next_start_sec, prev_sid_b, next_sid_b in sorted(boundaries, key=lambda b: -b[0]):
        gap = next_start_sec - prev_end_sec
        delta = target_pause_sec - gap  # >0 = вставить, <0 = вырезать
        if abs(delta) <= tolerance_sec:
            log.info(
                f"  level pause {prev_sid_b}→{next_sid_b}: gap={gap:.2f}s ≈ "
                f"{target_pause_sec}s, не трогаю"
            )
            continue
        mid_sec = (prev_end_sec + next_start_sec) / 2
        mid_ms = int(mid_sec * 1000)
        if delta > 0:
            silence_ms = int(delta * 1000)
            log.info(
                f"  level pause {prev_sid_b}→{next_sid_b}: gap={gap:.2f}s "
                f"→ добавляю {delta:.2f}s silence"
            )
            silence = AudioSegment.silent(duration=silence_ms)
            audio = audio[:mid_ms] + silence + audio[mid_ms:]
        else:
            trim_ms = int(-delta * 1000)
            log.info(
                f"  level pause {prev_sid_b}→{next_sid_b}: gap={gap:.2f}s "
                f"→ срезаю {-delta:.2f}s из середины паузы"
            )
            cut_start = max(0, mid_ms - trim_ms // 2)
            cut_end = min(len(audio), cut_start + trim_ms)
            audio = audio[:cut_start] + audio[cut_end:]
        modified = True

    if modified:
        try:
            audio.export(voice_path, format="mp3", bitrate="128k")
            log.info(f"Voice normalized: новая длительность {len(audio)/1000:.2f}s")
        except Exception as e:
            log.warning(f"Voice export failed: {e}")
            return False
    return modified


def _strip_video_audio(src: Path, out: Path) -> Optional[Path]:
    """Создаёт audio-free копию video через ffmpeg stream copy (мгновенно, без перекодирования).

    Returns путь к silent копии или None если не удалось.
    """
    if out.exists() and out.stat().st_size > 1000:
        return out
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        import ffmpeg
        (
            ffmpeg.input(str(src))
            .output(str(out), vcodec="copy", an=None)
            .overwrite_output()
            .global_args("-loglevel", "error")
            .run(quiet=True)
        )
        log.info(f"  Strip audio: {src.name} → {out.name}")
        return out
    except Exception as e:
        log.warning(f"  Strip audio failed для {src.name}: {e}")
        return None


def _try_init_media_search():
    """Ленивая инициализация CLIP-поиска. None если индекс отсутствует/упал."""
    try:
        from services.media_kit.search import MediaSearch
        index_dir = Path(__file__).resolve().parent.parent / ".media_index"
        if not (index_dir / "db.sqlite").exists():
            log.info(f"CLIP-индекс не найден ({index_dir}) — пропускаю local search")
            return None
        ms = MediaSearch(index_dir=index_dir)
        return ms
    except Exception as e:
        log.warning(f"MediaSearch init failed: {e}")
        return None
