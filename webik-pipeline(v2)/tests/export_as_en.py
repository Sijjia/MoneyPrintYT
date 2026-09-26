"""Экспорт активной секвенции Adult Swim в H.264 1080p (пресет High Quality 1080 HD) → E:\\...\\_RU.mp4.
Запускать при ОТКРЫТОМ Premiere. exportAsMediaDirect блокирует до конца рендера (~10 мин)."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere

PRESET = r"C:\Program Files\Adobe\Adobe Premiere Pro 2025\CEP\extensions\com.adobe.frameio.v4\assets\epr\High Quality 1080 HD.epr"
OUT = r"E:\video for ytb\Webik\Айсберг Adult Swim\Айсберг Adult Swim_EN.mp4"
WORKAREA_ENTIRE = 0  # вся секвенция


def main() -> int:
    if not Path(PRESET).exists():
        print("НЕТ пресета:", PRESET); return 1
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name} → {OUT}", flush=True)
    t0 = time.time()
    ok = seq.exportAsMediaDirect(OUT, PRESET, WORKAREA_ENTIRE)
    dt = time.time() - t0
    out = Path(OUT)
    size = out.stat().st_size // (1024 * 1024) if out.exists() else 0
    print(f"РЕНДЕР ГОТОВ за {dt/60:.1f}мин | файл {'есть' if out.exists() else 'НЕТ'} {size}MB | ret={ok}")
    return 0 if out.exists() and size > 1 else 1


if __name__ == "__main__":
    sys.exit(main())
