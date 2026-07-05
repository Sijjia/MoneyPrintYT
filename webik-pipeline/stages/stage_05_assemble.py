"""
Stage 5: Сборка в Premiere (минимальная версия для вертикального среза C)

scenes.json + assets/ → projects/<n>/project.prproj (открыт в Premiere)

Что делает:
1. Открывает Premiere (он должен быть запущен заранее).
2. Создаёт/открывает project.prproj в папке проекта.
3. Создаёт sequence 1920x1080 30fps.
4. Импортирует голос и все картинки одним пакетом.
5. Раскладывает голос на A1, картинки на V1 по scene.duration_sec.

Что НЕ делает (для следующих итераций):
- Ken Burns / motion keyframes
- Cross-dissolve переходы
- LUT
- .mogrt оверлеи (карточки уровней, субтитры)
- Музыка / SFX
- Beat-cuts по WhisperX word-timestamps
"""
import json
from pathlib import Path
from typing import Optional

from core.logger import setup_logger
from core.state import Stage, StateManager
from core.exceptions import StageError
from core.config import get_settings
from services.premiere.timeline_builder import build_rough_cut
from services.observability.timeline_reporter import write_report

log = setup_logger("stage5")


def run(project_dir: Path, feedback: Optional[str] = None) -> dict:
    log.info("[bold cyan]Stage 5: Сборка в Premiere (минимальная версия)[/]")

    settings = get_settings()
    state_manager = StateManager(project_dir)
    state = state_manager.load()
    state.mark_running(Stage.ASSEMBLE)
    state_manager.save(state)

    try:
        scenes_path = project_dir / "scenes.json"
        voice_path = project_dir / "assets" / "voice" / "full.mp3"
        manifest_path = project_dir / "assets" / "images" / "manifest.json"
        alignment_path = project_dir / "assets" / "alignment.json"

        for p in [scenes_path, voice_path, manifest_path]:
            if not p.exists():
                raise StageError(5, f"Не найден файл: {p}. Прогони stage 4 сначала.")

        scenes_data = json.loads(scenes_path.read_text(encoding="utf-8"))
        scenes = scenes_data["scenes"]
        primary_preset = scenes_data.get("primary_preset")
        # level_titles: {1: "ОФИЦИАЛЬНАЯ ИСТОРИЯ", 2: "..."} — генерится LLM в Stage 3
        level_titles_raw = scenes_data.get("level_titles") or {}
        level_titles = {int(k): str(v) for k, v in level_titles_raw.items()}
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

        # Подтягиваем реальные тайминги сцен и word-timestamps из alignment (whisper)
        scene_timings = None
        whisper_words = None
        whisper_sentences = None
        if alignment_path.exists():
            alignment = json.loads(alignment_path.read_text(encoding="utf-8"))
            scene_timings = alignment.get("scenes")
            whisper_words = alignment.get("words") or []
            whisper_sentences = alignment.get("sentences") or []
            method = alignment.get("method", "?")
            if scene_timings:
                log.info(
                    f"Тайминги сцен: {len(scene_timings)} из alignment.json "
                    f"(method={method}, {len(whisper_words)} word-timestamps)"
                )
            else:
                log.warning("alignment.json без поля 'scenes' — fallback на duration_sec")
        else:
            log.warning("alignment.json не найден — использую duration_sec из scenes.json")

        # Преобразуем manifest → media_paths {scene_id: {"path": Path, "kind": str}}
        media_paths = {}
        for sid, entry in manifest.items():
            if entry.get("path"):
                media_paths[sid] = {
                    "path": (project_dir / entry["path"]).resolve(),
                    "kind": entry.get("kind", "image"),
                    "source": entry.get("source", "pexels"),
                }

        prproj_path = (project_dir / "project.prproj").resolve()

        # Если есть проект — Premiere должен открыть его, если нет — создаст.
        # Pymiere ловит уже запущенный Premiere через CEP.
        from services.premiere.pymiere_wrapper import open_or_create_project
        open_or_create_project(prproj_path)

        sequence = build_rough_cut(
            scenes=scenes,
            voice_path=voice_path.resolve(),
            media_paths=media_paths,
            scene_timings=scene_timings,
            whisper_words=whisper_words,
            whisper_sentences=whisper_sentences,
            project_dir=project_dir,
            sequence_name=f"Webik — {project_dir.name}",
            width=settings.video_width,
            height=settings.video_height,
            framerate=settings.default_framerate,
            primary_preset=primary_preset,
            level_titles=level_titles,
        )

        # Сохраняем проект
        import pymiere
        pymiere.objects.app.project.save()

        # Observability: timeline_manifest.json + timeline_preview.html
        try:
            report_paths = write_report(sequence, project_dir)
        except Exception as e:
            log.warning(f"Timeline report упал ({e}) — pipeline не валим")
            report_paths = {}

        result = {
            "prproj_path": str(prproj_path),
            "sequence_name": sequence.name,
            "scenes_placed": len([s for s in scenes if s["id"] in media_paths]),
            "scenes_total": len(scenes),
            "timeline_manifest": str(report_paths.get("json")) if report_paths.get("json") else None,
            "timeline_preview": str(report_paths.get("html")) if report_paths.get("html") else None,
        }

        state.mark_awaiting(Stage.ASSEMBLE)
        state_manager.save(state)

        log.info(f"[green]✓[/] Stage 5 готов")
        log.info(f"  Проект: {prproj_path}")
        log.info(f"  Sequence: {sequence.name}")
        log.info(f"  Сцен размещено: {result['scenes_placed']}/{result['scenes_total']}")
        if result["timeline_preview"]:
            log.info(f"  Timeline: {result['timeline_preview']}")
        log.info(f"  Открой Premiere и посмотри таймлайн.")
        return result

    except Exception as e:
        state.mark_failed(Stage.ASSEMBLE, str(e))
        state_manager.save(state)
        raise
