"""Музыка по 4 уровням «Айсберг DreamWorks» через Lumean, инструментал, БЕЗ мелодии/вокала —
сидит под закадром. Прогрессия: L1 обманчивый глянец (любимая студия с тенью) →
L2 погребённые/отменённые фильмы → L3 безжалостная машина (цена, смерти, увольнения) →
L4 бездна (самые тёмные тайны). Сохраняет в <project>/assets/music/. Потом build_level_music_dw.sh."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
MUSIC = (PROJECT / "assets" / "music").resolve()

TRACKS = [
    ("dw_L1_gloss",
     "Warm nostalgic cinematic underscore for a documentary about a beloved animation studio. "
     "Tender childhood wonder and magic, soft piano and warm strings, gentle and heartfelt, a faint "
     "bittersweet undertone of something lost, calm and emotional, NO horror, instrumental, no "
     "vocals, no strong melody so it sits under narration", 300000),
    ("dw_L2_buried",
     "Nostalgic melancholic ambient, the studio's magic now touched by a shadow of sadness, soft "
     "piano and airy strings, wistful and tender, gentle sorrow creeping in, warm but bittersweet, "
     "no horror, no sub bass, instrumental, no vocals, understated", 300000),
    ("dw_L3_machine",
     "Sad emotional cinematic underscore, bitterness and loss, the human cost behind the magic, "
     "mournful piano and cellos, heavy-hearted and sober, slow and melancholic, dignified grief, "
     "no horror, instrumental, no vocals", 300000),
    ("dw_L4_abyss",
     "Melancholic dark cinematic ambient, deep sorrow and resignation, the studio's lost dreams, "
     "somber slow piano and low strings, bleak but beautiful, emotional weight without horror, "
     "no sub-bass nightmare, no dissonance, instrumental, no vocals", 300000),
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
