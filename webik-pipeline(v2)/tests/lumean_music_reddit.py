"""Музыка по 4 уровням «Айсберг GTA» через Lumean — вайб СИНТ-НУАР НОЧНОЙ ГОРОД:
L1 глянцевый неон-нуар (верхушка — рекорды, деньги) → L2 ночные тайны/мифы, лёгкая тревога →
L3 криминальный неон-нуар, напряжение → L4 бездна: тёмный дроун, реальные дела/аресты.
Инструментал, БЕЗ вокала/сильной мелодии, чтобы сидело под закадром. Потом build_level_music_gta.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("reddit_L1_surface",
     "Eerie ambient digital underscore, the strange surface of the internet, soft glassy synth pads, faint "
     "dial-up-era hum, subtle curiosity and unease, cold blue tone, very low tension, NO drops, instrumental, "
     "no vocals, no strong melody so it sits under narration", 300000),
    ("reddit_L2_horror",
     "Dark creepypasta underscore, campfire internet horror stories, low drone with a slow pulsing heartbeat "
     "bass, distant whispering textures, nocturnal dread, unsettling but restrained, no jumpscares, "
     "instrumental, no vocals, understated, sits under narration", 300000),
    ("reddit_L3_cipher",
     "Cryptic glitchy suspense underscore, encrypted subreddits and ARG mysteries, cold metallic arpeggio, "
     "ticking data pulses, decoding tension, hacker-terminal atmosphere, dark and curious, controlled, "
     "instrumental, no vocals, sits under narration", 300000),
    ("reddit_L4_abyss",
     "Deep ominous drone, the abyss of the internet, heavy low sub drones, distant distorted digital "
     "glimmers, bleak cold dread of things that cannot be unseen, oppressive tension without loud drops, "
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
