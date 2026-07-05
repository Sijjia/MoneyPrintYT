"""
services/sfx/drone.py
Процедурная генерация сабсонического drone'а для переходов между уровнями
айсберга.

Принцип: deep sub-bass (30-50Hz) с медленной LFO-модуляцией и брауновым
rumble'ом — слышен скорее как давление, чем как тон. Чем глубже уровень,
тем ниже частота и громче амплитуда.

Использование:
    from services.sfx.drone import synthesize_drone
    seg = synthesize_drone(duration_ms=2000, level=3)
    seg.export("transition_l3.wav", format="wav")
"""
from typing import Tuple

import numpy as np
from pydub import AudioSegment

SAMPLE_RATE = 44100

# level → (base_freq_hz, target_dbfs, modulation_depth)
# L1 = «чуть-чуть», L4 = «максимально жутко». L0 (intro) — самый лёгкий.
LEVEL_PROFILES: dict[int, Tuple[float, float, float]] = {
    0: (50.0, -34.0, 0.05),
    1: (45.0, -30.0, 0.10),
    2: (40.0, -26.0, 0.15),
    3: (35.0, -22.0, 0.20),
    4: (30.0, -18.0, 0.25),
}

LFO_HZ = 0.3       # медленный «дышащий» throb
FADE_MS = 200      # анти-щелчок на стыках
HARMONIC_GAIN = 0.15
NOISE_GAIN = 0.10


def _level_profile(level: int) -> Tuple[float, float, float]:
    if level <= 0:
        return LEVEL_PROFILES[0]
    if level >= 4:
        return LEVEL_PROFILES[4]
    return LEVEL_PROFILES[level]


def synthesize_drone(
    duration_ms: int,
    level: int,
    sample_rate: int = SAMPLE_RATE,
    seed: int = 0,
) -> AudioSegment:
    """Сгенерировать sub-bass drone заданной длительности под уровень айсберга.

    Mono, int16 PCM. Готов к микшированию через pydub.

    Args:
        duration_ms: длительность в миллисекундах
        level: 0..4 (см. LEVEL_PROFILES) — 1=лёгкий, 4=максимально жуткий
        sample_rate: частота семплирования (default 44.1kHz)
        seed: фиксированный seed для voспроизводимости brown noise
    """
    base_freq, target_dbfs, mod_depth = _level_profile(level)
    n_samples = int(duration_ms / 1000.0 * sample_rate)
    if n_samples <= 0:
        return AudioSegment.silent(duration=0, frame_rate=sample_rate)

    t = np.arange(n_samples, dtype=np.float64) / sample_rate

    lfo = 1.0 + mod_depth * np.sin(2.0 * np.pi * LFO_HZ * t)
    base = np.sin(2.0 * np.pi * base_freq * t) * lfo

    harmonic = HARMONIC_GAIN * np.sin(2.0 * np.pi * base_freq * 2.0 * t)

    rng = np.random.default_rng(seed + level)
    white = rng.standard_normal(n_samples)
    brown = np.cumsum(white)
    brown_peak = float(np.max(np.abs(brown))) or 1.0
    brown = brown / brown_peak * NOISE_GAIN

    signal = base + harmonic + brown
    peak = float(np.max(np.abs(signal))) or 1.0
    signal = signal / peak

    target_amp = 10.0 ** (target_dbfs / 20.0)
    signal = signal * target_amp

    fade_samples = int(FADE_MS / 1000.0 * sample_rate)
    if n_samples > fade_samples * 2 and fade_samples > 0:
        fade_in = np.linspace(0.0, 1.0, fade_samples)
        fade_out = np.linspace(1.0, 0.0, fade_samples)
        signal[:fade_samples] *= fade_in
        signal[-fade_samples:] *= fade_out

    pcm = np.clip(signal * 32767.0, -32768, 32767).astype(np.int16)

    return AudioSegment(
        pcm.tobytes(),
        frame_rate=sample_rate,
        sample_width=2,
        channels=1,
    )


def match_to_target(drone: AudioSegment, target: AudioSegment) -> AudioSegment:
    """Привести drone к каналам/sample_rate/sample_width целевого audio,
    чтобы pydub не ругался при конкатенации."""
    out = drone
    if out.frame_rate != target.frame_rate:
        out = out.set_frame_rate(target.frame_rate)
    if out.sample_width != target.sample_width:
        out = out.set_sample_width(target.sample_width)
    if target.channels == 2 and out.channels == 1:
        out = AudioSegment.from_mono_audiosegments(out, out)
    elif target.channels == 1 and out.channels == 2:
        out = out.set_channels(1)
    return out
