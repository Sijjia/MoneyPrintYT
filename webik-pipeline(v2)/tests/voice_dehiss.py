"""Убирает шипение/сибилянты ИИ-голоса (Lumean): мягкий FFT-денойз + де-эссер + лёгкий срез верха.
Бэкапит оригинал в full.raw_hiss.mp3, перезаписывает full.mp3. Настраивается через env.
  ../webik-pipeline/.venv/Scripts/python.exe tests/voice_dehiss.py <full.mp3>
Env: DEHISS_NR (денойз dB, дефолт 10), DEHISS_DEESS (интенсивность 0-1, дефолт 0.3),
     DEHISS_SHELF (срез верха dB, дефолт -2)."""
import os, subprocess, sys, shutil
from pathlib import Path


def dehiss(src: Path, dst: Path):
    deess = os.environ.get("DEHISS_DEESS", "0.35")
    nr = os.environ.get("DEHISS_NR", "0")            # денойз ВЫКЛ по умолчанию (давал «под водой»)
    shelf = os.environ.get("DEHISS_SHELF", "0")       # срез верха выкл по умолчанию
    presence = os.environ.get("VOICE_PRESENCE", "1")  # студийная объёмность ВКЛ по умолчанию
    rev = os.environ.get("VOICE_REVERB", "0.10")      # доля румрева (0 = выкл, 0.10 = тонко)
    parts = []
    if float(nr) > 0:
        parts.append(f"afftdn=nr={nr}:nf=-30")
    parts.append(f"deesser=i={deess}:m=0.5:f=0.5")       # против свиста «с/ш/ц»
    # ИИ-«писк»: аномальный бугор ~10.5кГц → УЗКИЙ нотч (только тон, верх/воздух НЕ глушим)
    whz = os.environ.get("VOICE_WHINE_HZ", "10500")
    wg = os.environ.get("VOICE_WHINE_G", "-12")
    if float(wg) < 0:
        parts.append(f"equalizer=f={whz}:width_type=q:w=3.0:g={wg}")        # узкий глубокий нотч на писк
    # компенсация «глухо/басово»: чуть убрать бас-бубнёж + вернуть разборчивость речи
    if os.environ.get("VOICE_CLARITY", "1") == "1":
        parts.append("equalizer=f=250:width_type=q:w=1.2:g=-2.0")           # меньше баса/бубнежа
        parts.append("equalizer=f=4000:width_type=q:w=1.5:g=2.5")           # презенс/разборчивость
        parts.append("highshelf=f=7000:g=1.5")                              # лёгкий «воздух» назад
    if presence == "1":
        # студийный голос: мягкий компрессор (плотность) + тепло низов + презенс верхов
        parts += [
            "acompressor=threshold=-20dB:ratio=2.5:attack=15:release=180:makeup=2",
            "equalizer=f=180:width_type=q:w=1.0:g=1.5",     # тепло/тело
            "equalizer=f=4500:width_type=q:w=1.2:g=2.0",    # презенс/разборчивость
            "equalizer=f=250:width_type=q:w=1.4:g=-1.5",    # убрать бубнёж
        ]
        if float(rev) > 0:
            # тонкий студийный «воздух»/румрев — короткие ранние отражения
            parts.append(f"aecho=0.9:0.9:22|38:{rev}|{max(0.0,float(rev)-0.03):.2f}")
        parts.append("loudnorm=I=-16:TP=-1.5:LRA=11")       # ровный вещательный уровень
    else:
        if float(shelf) < 0:
            parts.append(f"highshelf=f=9500:g={shelf}")
    af = ",".join(parts)
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-af", af,
                        "-c:a", "libmp3lame", "-b:a", "192k", str(dst)],
                       capture_output=True, text=True)
    return dst.exists() and dst.stat().st_size > 10000, r.stderr[-200:]


def main() -> int:
    full = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(os.environ["FULL_MP3"])
    bak = full.with_name(full.stem + ".raw_hiss.mp3")
    if not bak.exists():
        shutil.copy(full, bak)
    tmp = full.with_name("_dehiss_tmp.mp3")
    ok, err = dehiss(bak, tmp)   # всегда обрабатываем ОРИГИНАЛ (из бэкапа), не накапливаем
    if not ok:
        print(f"✗ де-хисс упал: {err}"); return 1
    shutil.move(str(tmp), str(full))
    def dur(p):
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                           capture_output=True, text=True)
        try: return float(r.stdout.strip())
        except: return 0.0
    print(f"✓ де-хисс применён → {full.name} ({dur(full):.1f}с) | оригинал: {bak.name}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
