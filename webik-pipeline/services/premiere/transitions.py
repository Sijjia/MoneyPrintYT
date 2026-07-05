"""
services/premiere/transitions.py
Матрица переходов между сценами Webik.

Логика выбора (по убыванию приоритета):
1. scene.transition_out override:
   - "shadow_cut" → JUST_CUT (резкий, под драматическую сцену)
   - "between_topics" → DIP_TO_BLACK
   - "default" → ничего, идём дальше
2. Изменение level (уровень айсберга): level_a != level_b → FILM_BURN
   (пока film burn не реализован — fallback на DIP_TO_BLACK)
3. Изменение topic_id: topic_a != topic_b → DIP_TO_BLACK
4. Иначе → JUST_CUT (default, динамичные cuts внутри одной мысли)

Длительности fade-in/fade-out для каждого типа в FADE_DURATIONS.
JUST_CUT = 0 — клипы встык, opacity-keyframes не ставим.
"""
from enum import Enum
from typing import Dict, Optional


class TransitionType(str, Enum):
    JUST_CUT = "just_cut"
    SHORT_DIP = "short_dip"
    DIP_TO_BLACK = "dip_to_black"
    FILM_BURN = "film_burn"  # fallback на DIP_TO_BLACK пока


# Длительности fade-in/fade-out (секунды) для каждого типа.
# fade_in = на входе клипа, fade_out = на выходе. JUST_CUT = ничего.
FADE_DURATIONS: Dict[TransitionType, float] = {
    TransitionType.JUST_CUT: 0.0,
    TransitionType.SHORT_DIP: 0.06,
    TransitionType.DIP_TO_BLACK: 0.15,
    TransitionType.FILM_BURN: 0.0,  # V1 без fade — burn overlay на V2 перекрывает cut
}


def choose_transition_type(
    prev_scene: Optional[Dict],
    next_scene: Optional[Dict],
) -> TransitionType:
    """Выбрать тип перехода между двумя соседними сценами.

    Args:
        prev_scene: предыдущая сцена (None если current — первая)
        next_scene: следующая сцена (None если current — последняя)

    Returns:
        TransitionType. JUST_CUT если границ нет (None соседей) или нет повода.
    """
    if prev_scene is None or next_scene is None:
        # На самом краю sequence (вход первого / выход последнего): нет перехода.
        # Это значит fade в самое начало/конец видео не делаем.
        return TransitionType.JUST_CUT

    # 1. Override через transition_out предыдущей сцены
    t_out = prev_scene.get("transition_out", "default")
    if t_out == "shadow_cut":
        return TransitionType.JUST_CUT
    if t_out == "between_topics":
        return TransitionType.DIP_TO_BLACK
    # default → продолжаем анализ

    # 2. Level changed (между уровнями айсберга)
    if prev_scene.get("level") != next_scene.get("level"):
        return TransitionType.FILM_BURN  # пока fallback DIP_TO_BLACK

    # 3. Topic changed
    if prev_scene.get("topic_id") != next_scene.get("topic_id"):
        return TransitionType.DIP_TO_BLACK

    # 4. Default — резкий cut
    return TransitionType.JUST_CUT


def fade_duration_for(transition_type: TransitionType) -> float:
    return FADE_DURATIONS.get(transition_type, 0.0)
