"""
services/premiere/effects.py
Эффекты-обёртки над pymiere: Motion keyframes (Ken Burns), Scale, Opacity и т.д.

Pymiere позволяет управлять keyframes через clip.components → effect.properties.
Время keyframes — float секунды относительно clip.inPoint.seconds (clip-local time),
не относительно timeline. См. pymiere.wrappers.animate_effect_using_function.
"""
from typing import Optional, Tuple

from core.logger import setup_logger

log = setup_logger("effects")


def _find_component(clip, name: str):
    """Найти компонент эффекта по displayName (без учёта регистра)."""
    for comp in clip.components:
        if comp.displayName.lower() == name.lower():
            return comp
    return None


def _find_property(component, name: str):
    """Найти property компонента по displayName (без учёта регистра)."""
    for prop in component.properties:
        if prop.displayName.lower() == name.lower():
            return prop
    return None


def compute_fit_scale_pct(image_w: int, image_h: int, frame_w: int = 1920, frame_h: int = 1080) -> float:
    """Минимальный scale (в процентах) чтобы картинка покрыла frame целиком.

    Используется cover-стратегия: max(frame_w/image_w, frame_h/image_h) — картинка
    выйдет за края frame по одной из осей, чёрных полос не будет.
    """
    if image_w <= 0 or image_h <= 0:
        return 100.0
    return max(frame_w / image_w, frame_h / image_h) * 100.0


def apply_ken_burns(
    clip,
    start_scale_pct: float,
    end_scale_pct: float,
) -> bool:
    """Анимировать Motion → Scale от start_scale_pct до end_scale_pct за длительность клипа.

    Создаёт 2 keyframe: на clip.inPoint и clip.outPoint.

    Returns:
        True если keyframes успешно добавлены, False если Motion/Scale недоступен.
    """
    motion = _find_component(clip, "Motion")
    if motion is None:
        log.warning(f"Motion component не найдена в clip {getattr(clip, 'name', '?')}")
        return False

    scale_prop = _find_property(motion, "Scale")
    if scale_prop is None:
        log.warning("Scale property не найдена в Motion")
        return False

    if not scale_prop.areKeyframesSupported():
        log.warning("Scale property не поддерживает keyframes")
        return False

    if not scale_prop.isTimeVarying():
        scale_prop.setTimeVarying(True)

    in_sec = clip.inPoint.seconds
    out_sec = clip.outPoint.seconds

    # Очищаем существующие ключи в диапазоне (на случай повторного вызова)
    try:
        scale_prop.removeKeyRange(in_sec, out_sec, True)
    except Exception:
        pass

    scale_prop.addKey(in_sec)
    scale_prop.setValueAtKey(in_sec, float(start_scale_pct), True)
    scale_prop.addKey(out_sec)
    scale_prop.setValueAtKey(out_sec, float(end_scale_pct), True)
    return True


def apply_dip_to_black_fade(
    clip,
    fade_in_sec: float = 0.25,
    fade_out_sec: float = 0.25,
    do_fade_in: bool = True,
    do_fade_out: bool = True,
) -> bool:
    """Opacity keyframes для fade-in (0→100%) и fade-out (100→0%).

    Длительности clampятся внутри: каждая половина не больше 1/4 длительности клипа,
    чтобы не «съесть» весь кадр. Если do_fade_in/do_fade_out False — соответствующая
    половина пропускается.

    Применяется поверх Ken Burns на той же sequence без конфликта (Opacity и Motion —
    разные components).
    """
    opacity_comp = _find_component(clip, "Opacity")
    if opacity_comp is None:
        log.warning(f"Opacity component не найдена в clip {getattr(clip, 'name', '?')}")
        return False
    opacity_prop = _find_property(opacity_comp, "Opacity")
    if opacity_prop is None:
        log.warning("Opacity property не найдена в Opacity component")
        return False
    if not opacity_prop.areKeyframesSupported():
        log.warning("Opacity не поддерживает keyframes")
        return False
    if not opacity_prop.isTimeVarying():
        opacity_prop.setTimeVarying(True)

    in_sec = clip.inPoint.seconds
    out_sec = clip.outPoint.seconds
    clip_dur = max(0.0, out_sec - in_sec)
    if clip_dur <= 0:
        return False

    # Clamp каждой половины до 1/4 длительности клипа
    max_half = clip_dur / 4.0
    fi = min(fade_in_sec, max_half) if do_fade_in else 0.0
    fo = min(fade_out_sec, max_half) if do_fade_out else 0.0

    try:
        opacity_prop.removeKeyRange(in_sec, out_sec, True)
    except Exception:
        pass

    # Fade-in: 0% на in_sec → 100% на in_sec+fi
    if do_fade_in and fi > 0:
        opacity_prop.addKey(in_sec)
        opacity_prop.setValueAtKey(in_sec, 0.0, True)
        opacity_prop.addKey(in_sec + fi)
        opacity_prop.setValueAtKey(in_sec + fi, 100.0, True)
    else:
        # Стартуем с полной непрозрачности
        opacity_prop.addKey(in_sec)
        opacity_prop.setValueAtKey(in_sec, 100.0, True)

    # Fade-out: 100% на out_sec-fo → 0% на out_sec
    if do_fade_out and fo > 0:
        opacity_prop.addKey(out_sec - fo)
        opacity_prop.setValueAtKey(out_sec - fo, 100.0, True)
        opacity_prop.addKey(out_sec)
        opacity_prop.setValueAtKey(out_sec, 0.0, True)
    else:
        opacity_prop.addKey(out_sec)
        opacity_prop.setValueAtKey(out_sec, 100.0, True)

    return True


def apply_opacity_dip(
    clip,
    dim_start_abs: float,
    dim_end_abs: float,
    dim_pct: float = 20.0,
    fade_sec: float = 0.35,
) -> bool:
    """Затемняет opacity клипа до dim_pct в [dim_start_abs..dim_end_abs] (абсолютные сек).

    Используется для cinematic dim под level title cards: V1 уходит в фон,
    overlay-карта на V4 видна полностью.
    """
    opacity_comp = _find_component(clip, "Opacity")
    if opacity_comp is None:
        return False
    opacity_prop = _find_property(opacity_comp, "Opacity")
    if opacity_prop is None or not opacity_prop.areKeyframesSupported():
        return False
    if not opacity_prop.isTimeVarying():
        opacity_prop.setTimeVarying(True)

    in_sec = clip.inPoint.seconds
    out_sec = clip.outPoint.seconds
    if dim_end_abs <= in_sec or dim_start_abs >= out_sec:
        return False

    ds = max(in_sec, dim_start_abs)
    de = min(out_sec, dim_end_abs)
    pre = max(in_sec, ds - fade_sec)
    post = min(out_sec, de + fade_sec)

    try:
        opacity_prop.removeKeyRange(pre, post, True)
    except Exception:
        pass

    opacity_prop.addKey(pre)
    opacity_prop.setValueAtKey(pre, 100.0, True)
    opacity_prop.addKey(ds)
    opacity_prop.setValueAtKey(ds, float(dim_pct), True)
    opacity_prop.addKey(de)
    opacity_prop.setValueAtKey(de, float(dim_pct), True)
    opacity_prop.addKey(post)
    opacity_prop.setValueAtKey(post, 100.0, True)
    return True


def apply_static_opacity(clip, pct: float) -> bool:
    """Set constant opacity (без keyframes). Used for static overlay clips."""
    opacity_comp = _find_component(clip, "Opacity")
    if opacity_comp is None:
        return False
    opacity_prop = _find_property(opacity_comp, "Opacity")
    if opacity_prop is None:
        return False
    try:
        if opacity_prop.isTimeVarying():
            in_sec = clip.inPoint.seconds
            out_sec = clip.outPoint.seconds
            try:
                opacity_prop.removeKeyRange(in_sec, out_sec, True)
            except Exception:
                pass
            opacity_prop.setTimeVarying(False)
        opacity_prop.setValue(float(pct), True)
        return True
    except Exception as e:
        log.warning(f"setValue opacity={pct} failed: {e}")
        return False


# Premiere blend modes (integer mapping, проверено на Premiere 25.5)
BLEND_NORMAL = 0
BLEND_DARKEN = 2
BLEND_MULTIPLY = 3
BLEND_LIGHTEN = 13
BLEND_SCREEN = 14
BLEND_OVERLAY = 17
BLEND_SOFT_LIGHT = 18
BLEND_HARD_LIGHT = 19


def apply_blend_mode(clip, mode_int: int) -> bool:
    """Set Blend Mode property of Opacity component. Use BLEND_* constants."""
    opacity_comp = _find_component(clip, "Opacity")
    if opacity_comp is None:
        return False
    blend_prop = _find_property(opacity_comp, "Blend Mode")
    if blend_prop is None:
        return False
    try:
        blend_prop.setValue(int(mode_int), True)
        return True
    except Exception as e:
        log.warning(f"setValue blendMode={mode_int} failed: {e}")
        return False


def apply_static_scale(clip, scale_pct: float) -> bool:
    """Установить статический Scale без keyframes (для video клипов — Ken Burns не нужен).

    Returns True если property найден и setValue сработал.
    """
    motion = _find_component(clip, "Motion")
    if motion is None:
        return False
    scale_prop = _find_property(motion, "Scale")
    if scale_prop is None:
        return False
    try:
        if scale_prop.isTimeVarying():
            try:
                scale_prop.setTimeVarying(False)
            except Exception:
                pass
        scale_prop.setValue(float(scale_pct), True)
        return True
    except Exception as e:
        log.warning(f"Scale.setValue({scale_pct}) failed: {e}")
        return False


def mute_linked_audio(clip) -> int:
    """Заглушает audio у linked-clip (для video на V1 убираем встроенный звук).

    Returns кол-во audio-клипов на которых установлен Volume.Level = 0.
    """
    try:
        linked = clip.getLinkedItems()
    except Exception as e:
        log.warning(f"getLinkedItems failed: {e}")
        return 0
    if linked is None:
        return 0
    muted = 0
    n = linked.numItems if hasattr(linked, "numItems") else len(linked)
    for i in range(n):
        try:
            lc = linked[i]
            volume_comp = _find_component(lc, "Volume")
            if volume_comp is None:
                continue
            level_prop = _find_property(volume_comp, "Level")
            if level_prop is None:
                continue
            level_prop.setValue(0.0, True)
            muted += 1
        except Exception:
            continue
    return muted


def find_clip_by_timeline_start(track, start_sec: float, tol: float = 0.05):
    """Найти clip на треке с timeline-старт ~= start_sec (с погрешностью tol).

    Возвращает clip объект или None.
    """
    for i in range(track.clips.numItems):
        clip = track.clips[i]
        if abs(clip.start.seconds - start_sec) < tol:
            return clip
    return None
