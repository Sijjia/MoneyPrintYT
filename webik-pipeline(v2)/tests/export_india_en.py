"""Экспорт EN «Iceberg of India» (Debik) в H.264 1080p (пресет High Quality 1080 HD) → E:\\...Deb1k...\\_EN.mp4.
БЕЗ SFX (A4 замучена вручную, как в RU). Premiere открыт с EN-проектом. exportAsMediaDirect блокирует ~40 мин."""
import sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere

PRESET = r"C:\Program Files\Adobe\Adobe Premiere Pro 2025\CEP\extensions\com.adobe.frameio.v4\assets\epr\High Quality 1080 HD.epr"
OUT = r"E:\video for ytb\Deb1k\Iceberg India\Iceberg India_EN.mp4"
WORKAREA_ENTIRE = 0


def main() -> int:
    if not Path(PRESET).exists():
        print("НЕТ пресета:", PRESET); return 1
    Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name} → {OUT}", flush=True)
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
