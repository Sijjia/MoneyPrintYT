"""
services/premiere/pymiere_wrapper.py
Высокоуровневая обёртка над pymiere.

Pymiere управляет уже открытым Premiere Pro через CEP-расширение Pymiere Link.
Расширение запускается автоматически при старте Premiere (AutoVisible=false).

Перед использованием Premiere должен быть запущен.
"""
import time
from pathlib import Path
from typing import List, Optional

import pymiere
from pymiere import exe_utils
from pymiere.wrappers import time_from_seconds

from core.logger import setup_logger
from core.exceptions import StageError

log = setup_logger("pymiere")


def ensure_premiere_running() -> None:
    """Проверяет что Premiere открыт и CEP-панель отвечает.

    Raises StageError если нет связи.
    """
    if not exe_utils.is_premiere_running():
        raise StageError(5, "Premiere не запущен. Открой его вручную и повтори.")
    try:
        _ = pymiere.objects.app.version
    except Exception as e:
        raise StageError(5, f"Pymiere CEP-панель не отвечает: {e}")


def open_or_create_project(prproj_path: Path, clean_rebuild: bool = True) -> "pymiere.Project":
    """Открывает существующий .prproj либо создаёт новый.

    Args:
        prproj_path: путь к .prproj
        clean_rebuild: если True (default), сначала закрывает любой открытый
            проект Premiere (без сохранения) и удаляет старый файл — чтобы Stage 5
            всегда строил с нуля без дублей. Установи False если нужно сохранить
            существующий проект и просто его открыть.
    """
    ensure_premiere_running()
    prproj_path.parent.mkdir(parents=True, exist_ok=True)

    if clean_rebuild:
        _close_active_document_if_any()
        _delete_old_project_files(prproj_path.parent)
        # Дать Premiere освободить файлы после close
        time.sleep(0.5)

    if prproj_path.exists():
        pymiere.objects.app.openDocument(str(prproj_path))
        log.info(f"Открыт проект: {prproj_path}")
    else:
        pymiere.objects.app.newProject(str(prproj_path))
        log.info(f"Создан новый проект: {prproj_path}")
    return pymiere.objects.app.project


def _close_active_document_if_any():
    """Закрывает текущий открытый проект в Premiere без сохранения."""
    try:
        if pymiere.objects.app.isDocumentOpen():
            pymiere.objects.app.project.closeDocument(save=False)
            log.info("Закрыт активный проект Premiere (без сохранения)")
    except Exception as e:
        log.warning(f"Не смог закрыть активный проект: {e}")


def _delete_old_project_files(project_dir: Path):
    """Удаляет .prproj/.prin/.prproj-converted-* в папке проекта.

    Audio Previews и Auto-Save папки трогаем только если хотим полную чистку
    (сейчас оставляем — Premiere переиспользует кэш быстрее).
    """
    patterns = ["*.prproj", "*.prproj-converted-*", "*.prin"]
    deleted = []
    for pattern in patterns:
        for f in project_dir.glob(pattern):
            try:
                f.unlink()
                deleted.append(f.name)
            except Exception as e:
                log.warning(f"Не смог удалить {f.name}: {e}")
    if deleted:
        log.info(f"Удалены старые файлы: {', '.join(deleted)}")


def import_files(file_paths: List[Path]) -> List["pymiere.ProjectItem"]:
    """Импортирует файлы в корень bin проекта.

    Возвращает project_items в том же порядке.
    Pymiere `importFiles` принимает только строки путей.
    """
    project = pymiere.objects.app.project
    paths_str = [str(p.resolve()) for p in file_paths]

    items_before = list(_iter_root_items(project.rootItem))
    success = project.importFiles(paths_str, suppressUI=True, targetBin=project.rootItem, importAsNumberedStills=False)
    if not success:
        raise StageError(5, f"importFiles вернул False для путей: {paths_str}")

    items_after = list(_iter_root_items(project.rootItem))
    new_items = items_after[len(items_before):]
    log.info(f"Импортировано {len(new_items)} item(ов): {[i.name for i in new_items]}")
    return new_items


def _iter_root_items(root_item) -> List:
    """Итератор по children корневого bin."""
    items = []
    for i in range(root_item.children.numItems):
        items.append(root_item.children[i])
    return items


def _resolve_sequence_preset() -> str:
    """Возвращает путь к стандартному 1080p preset с stereo Master audio.

    Premiere по умолчанию для пустого preset делает routing stereo input как
    L→A1, R→A2 (mono pair) — это даёт SFX в одном ухе. С явным preset
    HD 1080p 29.97 fps audio Master = Stereo, stereo input mapped правильно.

    Returns:
        Путь к .sqpreset файлу или "" если не нашли (тогда default settings).
    """
    try:
        premiere_path = pymiere.objects.app.path
        candidate = (
            Path(premiere_path) / "Settings" / "SequencePresets" /
            "HD 1080p" / "HD 1080p 29.97 fps.sqpreset"
        )
        if candidate.exists():
            return str(candidate)
        log.warning(f"Preset не найден: {candidate}, использую default")
    except Exception as e:
        log.warning(f"Не смог разрешить preset: {e}")
    return ""


def create_sequence(
    name: str,
    width: int = 1920,
    height: int = 1080,
    framerate: int = 30,
) -> "pymiere.Sequence":
    """Создаёт новую sequence заданных параметров.

    Использует pymiere.objects.qe (Quick Engine API) с явным preset
    «HD 1080p 29.97 fps» (stereo Master audio). После создания подгоняет
    видео-параметры под нужное разрешение/framerate.
    """
    project = pymiere.objects.app.project

    # Если sequence с таким именем уже есть — переиспользуем
    for i in range(project.sequences.numSequences):
        seq = project.sequences[i]
        if seq.name == name:
            log.info(f"Sequence '{name}' уже существует, открываю.")
            project.activeSequence = seq
            return seq

    pymiere.objects.app.enableQE()
    qe_project = pymiere.objects.qe.project
    preset_path = _resolve_sequence_preset()
    qe_project.newSequence(name, preset_path)
    new_seq = project.activeSequence

    # Подгоняем video settings под наши нужды (preset 29.97 fps → 30 fps)
    settings = new_seq.getSettings()
    settings.videoFrameWidth = width
    settings.videoFrameHeight = height
    settings.videoFrameRate = time_from_seconds(1.0 / framerate)
    new_seq.setSettings(settings)

    log.info(
        f"Создана sequence: '{name}' {width}x{height}@{framerate}fps "
        f"(preset={'HD 1080p 29.97' if preset_path else 'default'})"
    )
    return new_seq


def get_active_sequence() -> "pymiere.Sequence":
    seq = pymiere.objects.app.project.activeSequence
    if not seq:
        raise StageError(5, "Активной sequence нет — создай через create_sequence().")
    return seq


def ensure_video_tracks(sequence, min_tracks: int) -> bool:
    """Добавляет video tracks к sequence если их меньше min_tracks.

    Returns True если все требуемые tracks теперь есть.
    """
    current = sequence.videoTracks.numTracks
    if current >= min_tracks:
        return True
    needed = min_tracks - current
    try:
        pymiere.objects.app.enableQE()
        qe_seq = pymiere.objects.qe.project.getActiveSequence()
        # addTracks(videoCount, videoIndex, audioCount, audioIndex,
        #          subAudioType, subAudioCount, subAudioIndex)
        qe_seq.addTracks(needed, current, 0, 0)
        log.info(f"Добавлено {needed} video tracks (было {current}, стало {current + needed})")
        return sequence.videoTracks.numTracks >= min_tracks
    except Exception as e:
        log.warning(f"Не смог добавить video tracks: {e}")
        return False
