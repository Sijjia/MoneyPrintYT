"""Музыка по 4 уровням «Айсберг GTA» через Lumean — вайб СИНТ-НУАР НОЧНОЙ ГОРОД:
L1 глянцевый неон-нуар (верхушка — рекорды, деньги) → L2 ночные тайны/мифы, лёгкая тревога →
L3 криминальный неон-нуар, напряжение → L4 бездна: тёмный дроун, реальные дела/аресты.
Инструментал, БЕЗ вокала/сильной мелодии, чтобы сидело под закадром. Потом build_level_music_gta.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("india_L1_surface",
     "Mystical Indian ambient underscore, sacred surface of ancient India, soft tanpura drone, distant temple "
     "bells, faint sitar shimmer, warm incense-lit curiosity with quiet mystery, low tension, NO drops, "
     "instrumental, no vocals, no strong melody so it sits under narration", 320000),
    ("india_L2_ritual",
     "Dark Indian ritual underscore, cremation ghats and ascetic rites, low drone with a slow tabla heartbeat "
     "pulse, distant wordless chanting textures, nocturnal temple dread, unsettling but restrained, no "
     "jumpscares, instrumental, no vocals, understated, sits under narration", 320000),
    ("india_L3_descent",
     "Tense mystery underscore, Himalayan cold and forbidden places, bowed sarangi and dark strings, ticking "
     "unease, thin high-altitude wind, curious dread, controlled, instrumental, no vocals, sits under "
     "narration", 320000),
    ("india_L4_abyss",
     "Deep ominous drone, the underworld of Patala and blood cults, heavy low sub drones, distorted Indian "
     "string textures, bleak ritual-sacrifice dread, oppressive tension without loud drops, no dissonant "
     "screech, instrumental, no vocals", 320000),
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
