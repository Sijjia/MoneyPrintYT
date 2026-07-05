"""
Анализ voice_check_22-30.mp3: реально ли там обрывы, или TTS просто растягивает слоги.

Два сигнала:
1. faster-whisper word-level probability + точные timestamps на этом куске.
   Если 'с' и 'точками' проговариваются с prob > 0.85 и без gap — обрывов нет, это растяжение.
2. Амплитуда сигнала через pydub (RMS по 20ms окнам). Если в середине слова амплитуда падает
   до ~silence (<-40 dBFS) — настоящий обрыв. Если плавная огибающая — растяжение.
"""

from pathlib import Path
from pydub import AudioSegment
from faster_whisper import WhisperModel
import numpy as np

MP3 = Path(r"C:\Users\aidar\OneDrive\Рабочий стол\voice_check_22-30.mp3")
assert MP3.exists(), MP3

# ---------- 1. Whisper word-level ----------
print("=" * 70)
print("WHISPER word-level transcription (medium, ru, int8)")
print("=" * 70)

model = WhisperModel("medium", device="cpu", compute_type="int8")
segments, info = model.transcribe(
    str(MP3),
    language="ru",
    word_timestamps=True,
    vad_filter=False,  # хотим увидеть реальные паузы, не отрезанные VAD'ом
    beam_size=5,
)

all_words = []
for seg in segments:
    print(f"\n[{seg.start:6.2f} -> {seg.end:6.2f}] {seg.text.strip()}")
    if seg.words:
        for w in seg.words:
            dur = w.end - w.start
            marker = "  <<< LONG" if dur > 1.0 else ""
            print(f"   {w.start:6.2f} -> {w.end:6.2f}  dur={dur:5.2f}s  p={w.probability:.3f}  '{w.word.strip()}'{marker}")
            all_words.append(w)

# ---------- 2. Амплитуда RMS по 20ms окнам ----------
print()
print("=" * 70)
print("AMPLITUDE (RMS по 20ms окнам, в dBFS)")
print("=" * 70)

audio = AudioSegment.from_mp3(MP3)
print(f"channels={audio.channels}  sr={audio.frame_rate}  dur={len(audio)/1000:.2f}s")

samples = np.array(audio.get_array_of_samples(), dtype=np.float32)
if audio.channels == 2:
    samples = samples.reshape(-1, 2).mean(axis=1)

max_amp = float(np.iinfo(np.int16).max)
samples /= max_amp

sr = audio.frame_rate
win = int(0.020 * sr)  # 20ms
hop = win  # без overlap

rms_db = []
for i in range(0, len(samples) - win, hop):
    chunk = samples[i:i + win]
    rms = np.sqrt(np.mean(chunk ** 2))
    db = 20 * np.log10(rms + 1e-10)
    rms_db.append(db)

rms_db = np.array(rms_db)
times = np.arange(len(rms_db)) * (hop / sr)

SILENCE_DB = -40.0
silent_windows = rms_db < SILENCE_DB

# Найдём «провалы» длиной >= 60ms посреди речи
gap_runs = []
in_gap = False
gap_start = 0
for i, is_sil in enumerate(silent_windows):
    if is_sil and not in_gap:
        in_gap = True
        gap_start = i
    elif not is_sil and in_gap:
        in_gap = False
        gap_dur_ms = (i - gap_start) * 20
        if gap_dur_ms >= 60:
            gap_runs.append((times[gap_start], times[i], gap_dur_ms))

print(f"\nSilent gaps (>=60ms, <{SILENCE_DB} dBFS):")
if not gap_runs:
    print("  (никаких — сигнал без перерывов выше порога)")
for s, e, ms in gap_runs:
    print(f"   {s:5.2f}s -> {e:5.2f}s  ({ms} ms)")

# ---------- 3. Карта по 100ms ----------
print()
print("Карта амплитуды (X = есть звук > -40 dBFS, . = тишина), шаг 100ms:")
print("Время (sec):")
bin_size = 5  # 5 окон * 20ms = 100ms
ascii_map = ""
time_labels = ""
for i in range(0, len(rms_db), bin_size):
    chunk = rms_db[i:i + bin_size]
    avg = float(np.mean(chunk))
    ascii_map += "X" if avg > SILENCE_DB else "."
    sec = (i * hop / sr)
    if i % (bin_size * 10) == 0:  # каждую 1 секунду
        time_labels += f"{sec:<10.0f}"
print(time_labels)
print(ascii_map)
