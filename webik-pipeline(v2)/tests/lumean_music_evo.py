"""Музыка по 4 уровням «Айсберг эволюции» через Lumean (music_v2), инструментал, БЕЗ
мелодии/вокала — сидит под закадром. Вайб: холодный био/научный хоррор, прогрессия:
 L1 древняя тайна (жуткое любопытство) → L2 биологический ужас (паразиты/каннибализм/крах) →
 L3 холодный клинический гнёт (евгеника) → L4 генетическая бездна (человек играет в бога).
Сохраняет в <project>/assets/music/. Потом build_level_music_evo.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("evo_L1_mystery",
     "Cold eerie ambient underscore for a dark documentary about human evolution and extinct "
     "human species. Ancient mysterious dread, deep icy drone, faint unsettling tones, sense of "
     "something old and hidden, restrained and clinical, NO melody so it sits under narration, "
     "instrumental, no vocals",
     300000),
    ("evo_L2_biohorror",
     "Dark biological horror ambient, creeping organic dread, low subharmonic pulse, wet unsettling "
     "textures, parasites and near-extinction mood, slow suffocating tension building, sickly and "
     "cold, instrumental, no vocals, no melody",
     300000),
    ("evo_L3_clinical",
     "Cold clinical institutional menace, sterile ominous drones, slow bureaucratic dread, "
     "eugenics-era horror, metallic sparse tones, inhuman and detached, growing unease, "
     "instrumental, no vocals, no melody",
     300000),
    ("evo_L4_abyss",
     "Bleak genetic-horror abyss, crushing dissonant sub bass, nightmarish industrial cold, "
     "humanity playing god, terrifying slow descent into darkness, hopeless and vast, "
     "instrumental, no vocals, no melody",
     300000),
]


def main() -> int:
    MUSIC.mkdir(parents=True, exist_ok=True)
    lm = LumeanTTS()
    done = []
    for name, prompt, length in TRACKS:
        dst = MUSIC / f"{name}.mp3"
        if dst.exists() and dst.stat().st_size > 100000:
            print(f"[кэш] {dst.name}"); done.append(dst); continue
        print(f"[gen] {name}: «{prompt[:56]}…»")
        try:
            outs = lm.generate_music(prompt, dst, length_ms=length, force_instrumental=True, n_variants=1)
            done += outs; print(f"    ✓ {dst.name}")
        except Exception as e:
            print(f"    ✗ {str(e)[:150]}")
    print(f"\nГотово {len(done)}/{len(TRACKS)} треков в {MUSIC}")
    return 0 if len(done) == len(TRACKS) else 1


if __name__ == "__main__":
    sys.exit(main())
