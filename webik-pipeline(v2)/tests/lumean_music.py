"""Генерит тематическую эмбиент-музыку через Lumean (music_v2) под ролик
«Айсберг религиозного террора» — тёмное, кинематографичное, захватывающее,
инструментал (без вокала, чтоб не бить по закадру).

Сохраняет в <project>/assets/music/. Айдар слушает и выбирает/ставит сам.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
MUSIC = (PROJECT / "assets" / "music").resolve()

# (имя файла, описание, длина_мс)  — 5 мин макс у Lumean
TRACKS = [
    ("lumean_bed_dark_ambient",
     "Dark cinematic ambient underscore for a documentary about cults and religious "
     "terror. Ominous low drone, deep sub bass, slow evolving tension, eerie sacred "
     "undertones, cold and unsettling, restrained, minimal, NO melody so it sits under "
     "narration, instrumental",
     300000),
    ("lumean_tension_gripping",
     "Cinematic dark tension, gripping and suspenseful, deep pulsing bass, eerie choir "
     "pads, ominous dread building slowly, haunting atmosphere, epic but restrained, "
     "instrumental, no vocals",
     300000),
    ("lumean_haunting_atmos",
     "Haunting ambient drone, cold unsettling atmosphere, distant wind, sparse deep "
     "tones, mysterious and ominous, sacred horror mood, very slow, instrumental",
     240000),
]


def main() -> int:
    MUSIC.mkdir(parents=True, exist_ok=True)
    lm = LumeanTTS()
    done = []
    for name, prompt, length in TRACKS:
        dst = MUSIC / f"{name}.mp3"
        if dst.exists() and dst.stat().st_size > 100000:
            print(f"[кэш] {dst.name}"); done.append(dst); continue
        print(f"[gen] {name}: «{prompt[:60]}…» {length/1000:.0f}с")
        try:
            outs = lm.generate_music(prompt, dst, length_ms=length,
                                     force_instrumental=True, n_variants=1)
            done += outs
        except Exception as e:
            print(f"    упало: {str(e)[:160]}")
    print(f"\nГотово {len(done)} треков в {MUSIC}")
    for d in done:
        print("  ", d.name, f"{d.stat().st_size // 1024} KB")
    return 0 if done else 1


if __name__ == "__main__":
    sys.exit(main())
