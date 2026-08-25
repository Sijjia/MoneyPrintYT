"""Тематическая музыка КНДР через Lumean (music_v2), инструментал, БЕЗ мелодии/вокала —
сидит под закадром. Прогрессия по 4 уровням айсберга:
 L1 витрина-пропаганда (холод/гипноз) → L2 тотальная слежка (паранойя) →
 L3 военный гнёт (тяжесть) → L4 бездна (хоррор/крах).
Сохраняет в <project>/assets/music/. Потом build_level_music_nk.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-08_aysberg-severnoy-korei-samye-zakrytye-zhutkie-i-maloizvestny"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("nk_L1_surface",
     "Cold sterile totalitarian ambient underscore for a documentary about North Korea. "
     "Slow icy synth drone, distant hollow martial undertone, hypnotic propaganda-parade "
     "grandeur turned eerie and unsettling, controlled and minimal, NO melody so it sits "
     "under narration, cold and clinical, instrumental, no vocals",
     300000),
    ("nk_L2_surveillance",
     "Ominous surveillance-state tension, paranoid cold atmosphere, faint mechanical ticking "
     "pulse, deep watchful sub bass, sense of always being watched, claustrophobic dread "
     "building slowly, restrained, instrumental, no vocals, no melody",
     300000),
    ("nk_L3_oppression",
     "Dark oppressive military dread, heavy slow low brass swells, distant menacing war "
     "drums, cold brutal totalitarian weight, growing fear and hopelessness, grim and "
     "crushing, cinematic but restrained, instrumental, no vocals",
     300000),
    ("nk_L4_abyss",
     "Brutal bleak horror abyss, crushing dissonant sub bass drones, industrial cold metallic "
     "textures, hopeless and terrifying, slow suffocating descent into darkness, nightmarish "
     "climax, instrumental, no vocals, no melody",
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
        print(f"[gen] {name}: «{prompt[:56]}…» {length/1000:.0f}с")
        try:
            outs = lm.generate_music(prompt, dst, length_ms=length,
                                     force_instrumental=True, n_variants=1)
            done += outs
            print(f"    ✓ {dst.name}")
        except Exception as e:
            print(f"    ✗ упало: {str(e)[:160]}")
    print(f"\nГотово {len(done)} треков в {MUSIC}")
    for d in done:
        print("  ", d.name, f"{d.stat().st_size // 1024} KB")
    return 0 if len(done) == len(TRACKS) else 1


if __name__ == "__main__":
    sys.exit(main())
