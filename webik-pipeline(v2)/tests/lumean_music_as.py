"""Музыка по 4 уровням «Айсберг Adult Swim» через Lumean — вайб «ностальгия → жуть»:
L1 тёплая ретро-ТВ ностальгия с лёгкой тревогой → L2 ностальгия меркнет, ползёт беспокойство →
L3 жуткая ARG-загадка, растущий страх → L4 бездна ночного эфира, тёмный дроун.
Инструментал, БЕЗ вокала/сильной мелодии — сидит под закадром. Потом build_level_music_as.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("as_L1_nostalgia",
     "Warm nostalgic late-night television underscore, retro cartoon nostalgia, cozy analog synth "
     "and soft warm pads, the glow of an old CRT TV after midnight, gentle and wistful with a faint "
     "uneasy undertone of something hidden, calm, NO horror, instrumental, no vocals, no strong melody "
     "so it sits under narration", 300000),
    ("as_L2_unease",
     "Nostalgic hazy ambient with creeping unease, the late-night warmth now touched by static and "
     "shadow, wistful detuned analog synth, dreamy but unsettling, subtle dread slowly rising, no "
     "jumpscares, instrumental, no vocals, understated, sits under narration", 300000),
    ("as_L3_dread",
     "Eerie mysterious ambient, hidden-signal ARG tension, cold glitchy detuned synth and distant "
     "reversed textures, growing dread and paranoia, unsettling and strange, the feeling of a secret "
     "broadcast, no harsh noise, instrumental, no vocals, sits under narration", 300000),
    ("as_L4_abyss",
     "Dark disturbing ambient drone, the abyss at the bottom of night TV, deep dread and resignation, "
     "low ominous drones and faint distorted textures, bleak and cold, heavy dread without loud "
     "jumpscares, no dissonant screech, instrumental, no vocals", 300000),
]


def main() -> int:
    MUSIC.mkdir(parents=True, exist_ok=True)
    lm = LumeanTTS()
    done = []
    for name, prompt, length in TRACKS:
        dst = MUSIC / f"{name}.mp3"
        if dst.exists() and dst.stat().st_size > 100000:
            print(f"[кэш] {dst.name}"); done.append(dst); continue
        print(f"[gen] {name}: «{prompt[:56]}…»", flush=True)
        try:
            outs = lm.generate_music(prompt, dst, length_ms=length, force_instrumental=True, n_variants=1)
            done += outs; print(f"    ✓ {dst.name}", flush=True)
        except Exception as e:
            print(f"    ✗ {str(e)[:150]}", flush=True)
    print(f"\nГотово {len(done)}/{len(TRACKS)} треков в {MUSIC}")
    return 0 if len(done) == len(TRACKS) else 1


if __name__ == "__main__":
    sys.exit(main())
