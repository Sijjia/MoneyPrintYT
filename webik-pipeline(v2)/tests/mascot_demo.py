"""Демо маскота с ЛИПСИНКОМ по громкости голоса. Считает рот-открыт/закрыт по кадрам из RMS голоса
(со сглаживанием от мельтешения), рендерит Remotion Mascot + примешивает звук → demo_mascot.mp4."""
import audioop, json, os, subprocess, sys, wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REMOTION = ROOT / "remotion"
RU = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
VOICE = RU / "assets" / "voice" / "voice_timeline_ru.mp3"
OUT = ROOT / "projects" / "_mascot_demo"
OUT.mkdir(parents=True, exist_ok=True)
FPS = 30
START = float(os.environ.get("MASCOT_START", "62"))
DUR = float(os.environ.get("MASCOT_DUR", "8"))


def mouth_track(audio_wav: Path, dur: float, fps: int):
    """массив 0/1 на кадр: открыт когда голос громкий; сглаживание (мин. удержание состояния)."""
    w = wave.open(str(audio_wav), "rb")
    sw, sr, ch = w.getsampwidth(), w.getframerate(), w.getnchannels()
    n = int(dur * fps)
    per = int(sr / fps)
    vals = []
    for i in range(n):
        w.setpos(min(i * per, w.getnframes() - 1))
        raw = w.readframes(per)
        vals.append(audioop.rms(raw, sw) if raw else 0)
    w.close()
    # адаптивный порог: ~перцентиль громкости → рот двигается в такт слогам (не всегда открыт)
    nz = sorted(v for v in vals if v > 0) or [1]
    thr = nz[int(len(nz) * 0.55)]          # выше ~55-го перцентиля = «говорит»
    raw_open = [1 if v > thr else 0 for v in vals]
    # сглаживание: не дёргать состояние чаще, чем раз в 2 кадра
    out, hold, cur = [], 0, 0
    for o in raw_open:
        if o != cur and hold >= 2:
            cur = o; hold = 0
        else:
            hold += 1
        out.append(cur)
    return out


def grab_frame(video: Path, dst: Path):
    subprocess.run(["ffmpeg", "-y", "-ss", "1", "-i", str(video), "-frames:v", "1",
                    "-vf", "scale=360:-1", str(dst)], capture_output=True)
    return dst.exists()


def main() -> int:
    seg = OUT / "seg.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{START}", "-t", f"{DUR}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
    mouth = mouth_track(seg, DUR, FPS)
    print(f"кадров: {len(mouth)} | открыт: {sum(mouth)} ({100*sum(mouth)//len(mouth)}%)")

    # 2 картинки-улики (кадры из тела) для демо companions
    comps = []
    pubm = REMOTION / "public" / "mascot"
    vids = sorted((RU / "assets" / "video_stock" / "_trimmed").glob("scene_0[5-9]*.mp4"))[:2] \
        or sorted((RU / "assets" / "video_stock" / "_fixed").glob("*.mp4"))[:2]
    layout = [{"x": 0.70, "y": 0.34, "w": 620}, {"x": 0.74, "y": 0.70, "w": 560}]
    for k, v in enumerate(vids):
        p = pubm / f"demo_comp{k}.jpg"
        if grab_frame(v, p):
            L = layout[k]
            comps.append({"src": f"mascot/demo_comp{k}.jpg", "x": L["x"], "y": L["y"], "w": L["w"],
                          "from": 18 + k * 45, "to": len(mouth) - 10})

    props = {"mouth": mouth, "position": "left", "scale": 0.96, "jitter": 0.8,
             "companions": comps, "caption": "", "accent": "#e2080d",
             "durationInFrames": len(mouth)}
    pf = REMOTION / "_mascot_props.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

    silent = OUT / "mascot_silent.mp4"
    r = subprocess.run(f'npx remotion render Mascot "{os.path.relpath(silent, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not silent.exists():
        print("рендер упал:", r.stderr[-300:]); return 1
    # примешиваем голос
    final = OUT / "demo_mascot.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(seg),
                    "-c:v", "copy", "-c:a", "aac", "-shortest", str(final)], capture_output=True)
    print(f"\nГОТОВО: {final}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
