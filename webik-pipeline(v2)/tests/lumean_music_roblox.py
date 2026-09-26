"""Музыка по 4 уровням «Айсберг Roblox» через Lumean — вайб «тёмный кибер/хакер»:
L1 холодный цифровой пульс (поверхность) → L2 нарастающая тревога/скам → L3 взломы, напряжение,
глитч → L4 бездна: тёмный дроун, деньги/преступность. Инструментал, БЕЗ вокала/мелодии. Потом build."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-09-05_aysberg-robloks-temnaya-skrytaya-storona-realnye-intsidenty-"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("rb_L1_pulse",
     "Cold dark cyber documentary underscore, digital pulse and subtle glitch textures, minimal techno "
     "hum, the feeling of a vast online platform hiding something, restrained and ominous, low tension, "
     "NO drops, instrumental, no vocals, no strong melody so it sits under narration", 300000),
    ("rb_L2_unease",
     "Dark cyber tension, creeping unease of online scams and stolen accounts, cold analog synth with "
     "glitchy hi-hats and a low pulsing bass, subtle dread rising, hacker-thriller mood, no jumpscares, "
     "instrumental, no vocals, understated, sits under narration", 300000),
    ("rb_L3_breach",
     "Tense hacker-heist underscore, data breach and account hijack atmosphere, pulsing arpeggiated synth, "
     "cold metallic glitches, driving low-end tension, the feeling of systems being broken into, dark and "
     "urgent but controlled, instrumental, no vocals, sits under narration", 300000),
    ("rb_L4_abyss",
     "Dark ominous cyber-crime drone, the abyss of money laundering and organized theft, deep low drones, "
     "distant distorted glitch textures, bleak and cold criminal underworld mood, heavy dread without loud "
     "drops, no dissonant screech, instrumental, no vocals", 300000),
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
