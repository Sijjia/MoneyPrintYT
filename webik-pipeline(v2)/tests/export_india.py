"""Экспорт активной секвенции «Айсберг Индии» (RU) в H.264 1080p (пресет High Quality 1080 HD) → E:\\...\\_RU.mp4.
ВНИМАНИЕ: для ЭТОГО ролика SFX-дорожка (A4) замучена вручную — экспорт без звуковых эффектов.
Запускать при ОТКРЫТОМ Premiere. exportAsMediaDirect блокирует до конца рендера (~10-15 мин)."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere

PRESET = r"C:\Program Files\Adobe\Adobe Premiere Pro 2025\CEP\extensions\com.adobe.frameio.v4\assets\epr\High Quality 1080 HD.epr"
OUT = r"E:\video for ytb\Webik\Айсберг Индии\Айсберг Индии_RU.mp4"
WORKAREA_ENTIRE = 0  # вся секвенция


def main() -> int:
    if not Path(PRESET).exists():
        print("НЕТ пресета:", PRESET); return 1
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name} → {OUT}", flush=True)
    # страховка: SFX (A4) должна быть замучена
    try:
        print("A4(SFX) isMuted:", pymiere.core.eval_script('app.project.activeSequence.audioTracks[3].isMuted()'), flush=True)
    except Exception:
        pass
    t0 = time.time()
    ok = seq.exportAsMediaDirect(OUT, PRESET, WORKAREA_ENTIRE)
    dt = time.time() - t0
    out = Path(OUT)
    size = out.stat().st_size // (1024 * 1024) if out.exists() else 0
    print(f"РЕНДЕР ГОТОВ за {dt/60:.1f}мин | файл {'есть' if out.exists() else 'НЕТ'} {size}MB | ret={ok}")
    return 0 if out.exists() and size > 1 else 1


if __name__ == "__main__":
    sys.exit(main())
