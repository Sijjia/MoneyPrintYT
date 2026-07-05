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
from services.stocks.wikipedia_photo import WikipediaPhotoClient
from services.text.ner import extract_entity_terms
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
        #    SSML break Voicer часто игнорирует). Между уровнями вставляем SEAM_MARKER:
        #    voicer порежет TTS-куски именно по этим швам, и микро-дрейф тембра между
        #    запросами ElevenLabs ляжет на вставляемую паузу уровня (не слышен).
        from services.tts.voicer import SEAM_MARKER
        full_text_parts = []
        prev_level = None
        n_seams = 0
        for s in scenes:
            vo = s.get("voiceover", "").strip()
            if not vo:
                continue
            lvl = s.get("level", 0)
            if prev_level is not None and lvl != prev_level:
                full_text_parts.append(SEAM_MARKER)
                n_seams += 1
            full_text_parts.append(vo)
            prev_level = lvl
        full_text = " ".join(full_text_parts)
        if not full_text.replace(SEAM_MARKER, "").strip():
            raise StageError(4, "В scenes.json нет ни одного voiceover")
        log.info(f"TTS: собран voiceover с {n_seams} структурными швами (границы уровней)")

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
            alignment = align_proportional(full_text.replace(SEAM_MARKER, " "), voice_path)
            alignment["scenes"] = proportional_scene_timings(scenes, alignment["duration"])

        # 2b. Нормализация пауз перед level↑: если TTS оставил гигантский gap
        # (типично 5-9s после точки) — урезаем до target. Если коротко — добавляем.
        # Маркер «paused_at_levels» в alignment предотвращает повторную обработку.
        already_paused = bool(alignment.get("paused_at_levels"))
        if not already_paused and _insert_structured_pauses(voice_path, scenes, alignment, default_pause_sec=1.5):
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
            try:
                from core.config import get_settings
                _yt_auto = bool(get_settings().youtube_auto_archive)
            except Exception:
                _yt_auto = False
            manifest = _build_media_manifest(scenes, project_dir, images_dir,
                                             youtube_auto=_yt_auto)
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


def _build_media_manifest(scenes, project_dir: Path, images_dir: Path,
                          youtube_auto: bool = False) -> dict:
    """Подбирает медиа для каждой сцены: local CLIP > Pexels.

    Returns manifest dict в формате:
        {sid: {path, query, kind: image|video, source: local|pexels, score?}}

    Для local — path абсолютный (in-place из E:\\YouTube Webik\\).
    Для pexels — относительный к project_dir (скачанный в assets/images/).

    youtube_auto: если True — для сцен-фактов (NER нашёл сущность ИЛИ
        visual.type=archive_video) включается авто-подбор архивного ВИДЕО с
        YouTube (тир 0.5, выше локального CLIP). Клип привязывается к сцене
        и потом ложится накладкой на её слот (archive_clip_placer).
    """
    # Lazy init: CLIP search, Wikimedia, Pexels, Pixabay — могут не понадобиться если manifest целиком local
    media_search = None
    wikimedia = None
    wiki_photo = None
    pexels_videos = None
    pixabay = None
    pexels = None
    manifest = {}
    # LLM-выбор архивного клипа: ленивый ClaudeService (один на прогон). None,
    # если LLM недоступен (нет ключа) — тогда auto_archive_clip идёт эвристикой.
    _llm_svc = None
    _llm_svc_failed = False

    # Сцены, по которым НЕ ищем медиа из веба (плашки рисуются отдельно).
    _CARD_TYPES = {"level_card", "topic_card"}

    for scene in scenes:
        sid = scene["id"]
        visual = scene.get("visual", {})
        query = visual.get("search_query") or visual.get("fallback_query") or sid
        vtype = visual.get("type", "")

        # NER-driven подбор включаем ТОЛЬКО когда LLM не задал визуал (search_query
        # пуст) — тогда LLM-выбор всегда уважается, а NER заполняет пробелы:
        # топовая сущность → запрос; имя человека → портрет из Wikipedia (шаг 1.5).
        person_name = None
        entity_found = False
        if vtype not in _CARD_TYPES and not visual.get("search_query"):
            try:
                entities = extract_entity_terms(scene.get("voiceover", ""))
            except Exception as e:
                entities = []
                log.warning(f"  {sid}: NER упал ({e})")
            if entities:
                entity_found = True
                person_name = next((e["text"] for e in entities if e["type"] == "PERSON"), None)
                # приоритет места/организации (узнаваемый кадр), иначе первая сущность
                loc = next((e["text"] for e in entities if e["type"] in ("LOC", "ORG")), None)
                query = loc or entities[0]["text"]
                log.info(f"  {sid}: search_query пуст → NER-запрос '{query}'")

        # 0.5) Авто-архив с YouTube — движущийся «доказательный» B-roll под факт.
        #      Срабатывает когда: контентная сцена И (явный visual.type=archive_video
        #      ИЛИ включён флаг youtube_auto и NER нашёл конкретную сущность).
        #      Качаем+режем; при неудаче (нет роликов / бот-гейт) тихо падаем в
        #      обычные тиры ниже (CLIP/wiki/сток) — фича не ломает прогон.
        want_archive = vtype in ("archive_video", "youtube_search")
        if vtype not in _CARD_TYPES and (want_archive or (youtube_auto and entity_found)):
            from services.stocks.youtube_search import auto_archive_clip
            scene_dur = float(scene.get("duration_sec", 6.0))
            want_sec = max(4.0, min(scene_dur, 8.0))
            # LLM ранжирует кандидатов по релевантности факту (откат на эвристику
            # внутри select_clip при любой ошибке). Сервис создаём один раз.
            _pick = None
            if not _llm_svc_failed:
                if _llm_svc is None:
                    try:
                        from services.llm.claude import ClaudeService
                        from core.config import get_settings as _gs
                        # выбор клипа — механика, берём дешёвую модель
                        _llm_svc = ClaudeService(model=_gs().llm_model_cheap or None)
                    except Exception as e:
                        _llm_svc_failed = True
                        log.warning(f"  LLM-выбор клипа недоступен ({str(e)[:120]}) — эвристика")
                if _llm_svc is not None:
                    from services.stocks.clip_llm_pick import make_llm_pick
                    _pick = make_llm_pick(_llm_svc, want_sec=want_sec)
            try:
                res = auto_archive_clip(
                    query=query,
                    project_dir=project_dir,
                    scene_id=sid,
                    fact=scene.get("voiceover", "")[:200],
                    want_sec=want_sec,
                    llm_pick=_pick,
                )
            except Exception as e:
                res = None
                log.warning(f"  {sid}: auto_archive_clip упал ({e})")
            if res:
                manifest[sid] = {
                    "path": str(Path(res["path"]).relative_to(project_dir)),
                    "query": query,
                    "kind": "video",
                    "source": "youtube-auto",
                    "source_url": res.get("source_url"),
                    "caption": res.get("caption", ""),
                }
                log.info(f"  {sid}: '{query}' → youtube-auto архив {Path(res['path']).name}")
                continue

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

        # 1.5) Wikipedia-портрет персоны (если NER нашёл человека) — реальное фото
        #      конкретной личности лучше любого стока. Только для контентных сцен.
        if person_name and vtype not in _CARD_TYPES:
            if wiki_photo is None:
                try:
                    wiki_photo = WikipediaPhotoClient()
                except Exception as e:
                    log.warning(f"WikipediaPhoto init failed: {e}")
            if wiki_photo is not None:
                wp_out = images_dir / f"{sid}_person.jpg"
                try:
                    got = wiki_photo.download_photo(person_name, wp_out)
                    if got and wp_out.stat().st_size > 5000:
                        manifest[sid] = {
                            "path": str(wp_out.relative_to(project_dir)),
                            "query": person_name,
                            "kind": "image",
                            "source": "wikipedia-person",
                        }
                        log.info(f"  {sid}: '{person_name}' → wikipedia портрет {wp_out.name}")
                        continue
                except Exception as e:
                    log.warning(f"  {sid}: Wikipedia photo ошибка ({e})")

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


def _insert_structured_pauses(
    voice_path: Path, scenes, alignment,
    default_pause_sec: float = 1.5,
    search_window_ms: int = 350,
    silence_thresh_db: int = -40,
    tail_preserve_ms: int = 300,
) -> bool:
    """Вставляет drone-паузу перед каждой сценой с полем `pause_before_sec`.

    Logика:
      1) Триггер — наличие `pause_before_sec` у сцены (legacy: или level↑).
      2) В окне ±search_window_ms вокруг whisper-границы ищем НАСТОЯЩУЮ тишину
         через pydub.silence.detect_silence. Whisper word.end/word.start
         сдвинуты на 50-200ms внутрь речи (детект гласной, не атаки согласной),
         так что если резать по ним — съедаются consonant'ы.
      3) Найдена тишина → заменяем именно её на drone нужной длительности.
         Не найдена → INSERT drone в midpoint без cut'а.
      4) Drone-level берётся из самой сцены (s.level), seed по индексу — чтобы
         каждый из 3 drone'ов на одном переходе чуть отличался текстурой.

    Returns True если mp3 модифицирован (значит надо re-run whisper).
    """
    scene_timings = alignment.get("scenes") or {}
    candidates: list[dict] = []
    for i, s in enumerate(scenes):
        if i == 0:
            continue
        pause_sec = float(s.get("pause_before_sec") or 0)
        cur_level = int(s.get("level", 0))
        prev_level = int(scenes[i - 1].get("level", 0))
        # Legacy fallback: если pause_before_sec не задан, но это level↑ —
        # используем default_pause_sec, чтобы старые fixture без поля работали.
        if pause_sec <= 0 and cur_level > prev_level:
            pause_sec = default_pause_sec
        if pause_sec <= 0:
            continue

        prev_sid = scenes[i - 1]["id"]
        cur_sid = s["id"]
        prev_t = scene_timings.get(prev_sid, {}) or {}
        cur_t = scene_timings.get(cur_sid, {}) or {}
        prev_end = prev_t.get("end")
        cur_start = cur_t.get("start")
        if prev_end is None or cur_start is None:
            continue

        candidates.append({
            "prev_end_sec": float(prev_end),
            "next_start_sec": float(cur_start),
            "prev_sid": prev_sid,
            "next_sid": cur_sid,
            "level": cur_level,
            "pause_sec": pause_sec,
            "section": s.get("section", ""),
            "seed": i,
        })

    if not candidates:
        return False

    try:
        from pydub import AudioSegment
        from pydub.silence import detect_silence
        from services.sfx.drone import synthesize_drone, match_to_target, _level_profile
    except Exception as e:
        log.warning(f"pydub/drone недоступен ({e}) — паузы не вставляю")
        return False

    try:
        audio = AudioSegment.from_file(voice_path)
    except Exception as e:
        log.warning(f"Не смог загрузить voice mp3 ({e})")
        return False

    audio_len_ms = len(audio)
    modified = False

    # Идём с конца, чтобы earlier offsets оставались стабильными при insert/replace.
    for c in sorted(candidates, key=lambda x: -x["prev_end_sec"]):
        target_ms = int(c["pause_sec"] * 1000)
        prev_end_ms = int(c["prev_end_sec"] * 1000)
        next_start_ms = int(c["next_start_sec"] * 1000)

        # Окно поиска тишины: ±search_window_ms вокруг whisper-границы.
        win_start = max(0, prev_end_ms - search_window_ms)
        win_end = min(audio_len_ms, next_start_ms + search_window_ms)
        window = audio[win_start:win_end]

        silence_regions = detect_silence(
            window,
            min_silence_len=50,
            silence_thresh=silence_thresh_db,
        )

        drone = synthesize_drone(target_ms, level=c["level"], seed=c["seed"])
        drone = match_to_target(drone, audio)
        base_freq, target_dbfs, _ = _level_profile(c["level"])

        if silence_regions:
            # Берём самую длинную тишину в окне.
            longest = max(silence_regions, key=lambda r: r[1] - r[0])
            sil_start_abs = win_start + longest[0]
            sil_end_abs = win_start + longest[1]
            sil_len_ms = sil_end_abs - sil_start_abs
            # Не начинаем drone сразу — сохраняем до tail_preserve_ms естественного
            # decay-хвоста после спада голоса под threshold. Это убирает ощущение
            # «голос обрубается» когда drone накладывается на затухающий вокабл.
            tail_clamped = min(tail_preserve_ms, max(0, sil_len_ms))
            insert_at = sil_start_abs + tail_clamped
            audio = audio[:insert_at] + drone + audio[sil_end_abs:]
            log.info(
                f"  pause {c['prev_sid']}→{c['next_sid']} "
                f"[{c['section']}, L{c['level']}]: "
                f"silence {sil_len_ms}ms @ [{sil_start_abs/1000:.2f}..{sil_end_abs/1000:.2f}]s "
                f"→ preserve {tail_clamped}ms tail + drone {target_ms}ms @ {base_freq:.0f}Hz, {target_dbfs:.0f}dBFS"
            )
        else:
            # Настоящей тишины нет (Voicer не оставил паузу). Вставляем drone
            # СРАЗУ ПЕРЕД следующим словом — не в midpoint, чтобы drone не
            # резал текущую речь.
            insert_at = next_start_ms
            audio = audio[:insert_at] + drone + audio[insert_at:]
            log.info(
                f"  pause {c['prev_sid']}→{c['next_sid']} "
                f"[{c['section']}, L{c['level']}]: "
                f"no silence found, INSERT drone {target_ms}ms @ {base_freq:.0f}Hz "
                f"before next word at {insert_at/1000:.2f}s"
            )
        modified = True

    if modified:
        try:
            audio.export(voice_path, format="mp3", bitrate="128k")
            log.info(f"Voice + structured pauses: новая длительность {len(audio)/1000:.2f}s")
        except Exception as e:
            log.warning(f"Voice export failed: {e}")
            return False
    return modified


# Backward-compat alias: stage_05 или внешний код может ссылаться на старое имя.
_normalize_level_pauses = _insert_structured_pauses


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
