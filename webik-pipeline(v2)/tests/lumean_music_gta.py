"""Музыка по 4 уровням «Айсберг GTA» через Lumean — вайб СИНТ-НУАР НОЧНОЙ ГОРОД:
L1 глянцевый неон-нуар (верхушка — рекорды, деньги) → L2 ночные тайны/мифы, лёгкая тревога →
L3 криминальный неон-нуар, напряжение → L4 бездна: тёмный дроун, реальные дела/аресты.
Инструментал, БЕЗ вокала/сильной мелодии, чтобы сидело под закадром. Потом build_level_music_gta.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("gta_L1_neon",
     "Slick synthwave neon-noir night city underscore, GTA vibe, glossy retro analog synths, warm pulsing "
     "bass, distant city hum, the glamorous surface of a huge game empire and money, cool and confident, "
     "low tension, NO drops, instrumental, no vocals, no strong melody so it sits under narration", 300000),
    ("gta_L2_mystery",
     "Dark synth-noir night city with creeping mystery, urban legends and secrets hidden in the game, cold "
     "analog pads with a low pulsing bass and subtle arpeggio, faint unease under neon, moody and nocturnal, "
     "no jumpscares, instrumental, no vocals, understated, sits under narration", 300000),
    ("gta_L3_crime",
     "Tense neon-noir crime underscore, criminal underworld of hacks and leaks, pulsing arpeggiated synth, "
     "cold metallic textures, driving low-end tension, rain-soaked night city danger, dark and urgent but "
     "controlled, instrumental, no vocals, sits under narration", 300000),
    ("gta_L4_abyss",
     "Dark ominous synth drone, the abyss of real crimes and arrests behind the game, deep low drones, "
     "distant distorted neon glimmers, bleak cold night-city dread, heavy tension without loud drops, "
     "no dissonant screech, instrumental, no vocals", 300000),
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
