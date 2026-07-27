"""Генерит НОВЫЙ пул SFX через Lumean (ElevenLabs sound-effects по текстовому
описанию) взамен интернет-сборки. Категории под sfx_choreograph.py:
  w* вуши, t* тики, i* удары, r* ревилеры.

Каждый звук — точное англ. описание. БЕЗ восходящего swoosh/riser (Айдар не любит).
Конверт в wav + loudnorm -30 LUFS (консистентная громкость; общий уровень потом
опускается clip volume 0.12 в Premiere).

Старый пул удаляем БЕЗОПАСНЫМ глобом {prefix}[0-9]*.wav — чтобы НЕ задеть typing_*.wav.
"""
import glob
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
SFX = (PROJECT / "assets" / "sfx").resolve()

# (prefix, [(описание, длительность_с), ...]) — влияние промпта высокое (точный звук)
POOLS = {
    "w": [  # вуши: короткие, БЕЗ роста тона
        ("quick short subtle whoosh, soft air swish, clean, no rising pitch, no music", 0.6),
        ("fast light transition swish, soft air movement, brief, no music", 0.5),
        ("gentle whoosh pass by, soft brief cinematic air, no music", 0.6),
    ],
    "t": [  # тики: счёт/события/узлы/плашки
        ("single soft subtle UI tick, short clean digital blip, no music", 0.5),
        ("soft mechanical tick click, short subtle, no music", 0.5),
        ("gentle data point tick, small soft digital beep, short, no music", 0.5),
        ("soft snap tick, brief clean click, no music", 0.5),
        ("subtle short tick blip, minimal clean, no music", 0.5),
    ],
    "i": [  # удары: приземление после подъёма
        ("soft deep cinematic impact thud, subtle low bass hit, short, no music", 0.7),
        ("muffled low impact boom, soft short, not harsh, no music", 0.7),
        ("gentle bass drop hit, soft impact, short, no music", 0.6),
        ("soft punch impact, low thud, brief clean, no music", 0.6),
    ],
    "r": [  # ревилеры: растекание карты (длиннее)
        ("gentle shimmer reveal, soft sparkle wash, smooth, no music", 1.3),
        ("soft airy reveal texture, gentle particles sweep, smooth, no music", 1.3),
        ("soft ambient reveal shimmer, gentle glow wash, smooth, no music", 1.2),
    ],
}


def to_wav_norm(src: Path, dst: Path) -> bool:
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(src),
        "-af", "loudnorm=I=-30:TP=-1.5:LRA=11", "-ar", "48000", "-ac", "2",
        str(dst),
    ]
    try:
        subprocess.run(cmd, check=True)
        return dst.exists() and dst.stat().st_size > 1000
    except Exception as e:
        print(f"    ffmpeg упал: {str(e)[:120]}")
        return False


def main() -> int:
    SFX.mkdir(parents=True, exist_ok=True)
    # снести старый пул — БЕЗОПАСНО (только {prefix}<цифра>*, не typing_*)
    removed = 0
    for pref in POOLS:
        for p in glob.glob(str(SFX / f"{pref}[0-9]*.wav")):
            Path(p).unlink(); removed += 1
    print(f"старый пул удалён: {removed} файлов")

    lm = LumeanTTS()
    tmp = Path(tempfile.gettempdir())
    total = ok = 0
    for pref, items in POOLS.items():
        for n, (text, dur) in enumerate(items, 1):
            total += 1
            dst = SFX / f"{pref}{n}.wav"
            raw = tmp / f"_lm_sfx_{pref}{n}.mp3"
            print(f"[{pref}{n}] «{text[:48]}» {dur}с")
            try:
                lm.generate_sfx(text, raw, duration_seconds=dur, prompt_influence=0.7)
            except Exception as e:
                print(f"    генерация упала: {str(e)[:140]}"); continue
            if to_wav_norm(raw, dst):
                ok += 1
            raw.unlink(missing_ok=True)
    print(f"\nСгенерировано {ok}/{total} SFX в {SFX}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
