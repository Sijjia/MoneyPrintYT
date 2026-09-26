"""Рендерит НЕСКОЛЬКО сценариев маскота для сравнения (один и тот же закадр + звук):
1) left_evidence — маскот слева + улики справа
2) center_solo   — маскот по центру крупно, просто говорит (чёрный фон)
3) right_flip    — маскот справа, отзеркалён, улики слева
4) corner_present— маскот в углу поменьше + БОЛЬШАЯ сцена по центру (реакция/презентация)
→ projects/_mascot_demo/scenario_<name>.mp4"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.mascot_demo as md

REMOTION = ROOT / "remotion"
OUT = ROOT / "projects" / "_mascot_demo"
PUBM = REMOTION / "public" / "mascot"


def render(name, props, seg):
    props["durationInFrames"] = len(props["mouth"])
    pf = REMOTION / f"_msc_{name}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    silent = OUT / f"_sil_{name}.mp4"
    subprocess.run(f'npx remotion render Mascot "{os.path.relpath(silent, REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not silent.exists():
        print(f"  ✗ {name} рендер упал"); return
    final = OUT / f"scenario_{name}.mp4"
    subprocess.run(["ffmpeg", "-y", "-i", str(silent), "-i", str(seg), "-c:v", "copy", "-c:a", "aac",
                    "-shortest", str(final)], capture_output=True)
    silent.unlink(missing_ok=True)
    print(f"  ✓ {name} → {final.name}", flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    seg = OUT / "seg.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{md.START}", "-t", f"{md.DUR}", "-i", str(md.VOICE),
                    "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
    mouth = md.mouth_track(seg, md.DUR, md.FPS)
    n = len(mouth)
    print(f"кадров {n}, открыт {sum(mouth)} ({100*sum(mouth)//n}%)", flush=True)

    # набор кадров-улик
    vids = sorted((md.RU / "assets" / "video_stock" / "_trimmed").glob("scene_1[0-4]*.mp4"))[:4] \
        or sorted((md.RU / "assets" / "video_stock" / "_fixed").glob("*.mp4"))[:4]
    comp = []
    for k, v in enumerate(vids):
        p = PUBM / f"sc_comp{k}.jpg"
        if md.grab_frame(v, p):
            comp.append(f"mascot/sc_comp{k}.jpg")
    def C(i, x, y, w, fr): return {"src": comp[i % len(comp)], "x": x, "y": y, "w": w, "from": fr, "to": n - 8}

    scenarios = {
        "left_evidence": {"mouth": mouth, "position": "left", "scale": 0.96, "jitter": 0.8,
            "companions": [C(0, 0.70, 0.32, 640, 16), C(1, 0.74, 0.70, 580, 70)]},
        "center_solo": {"mouth": mouth, "position": "center", "scale": 1.08, "jitter": 0.8, "companions": []},
        "bust_top": {"mouth": mouth, "position": "center", "bust": True, "scale": 0.95, "jitter": 0.8,
            "companions": [C(0, 0.28, 0.24, 640, 14), C(1, 0.72, 0.24, 640, 60)]},
        "mascot_stat": {"mouth": mouth, "position": "left", "scale": 0.95, "jitter": 0.8,
            "stat": {"value": 350, "suffix": " МЛН $", "label": "УБЫТКИ ЗА ГОД", "sub": "DreamWorks, 2014"}},
        "mascot_bars": {"mouth": mouth, "position": "left", "scale": 0.95, "jitter": 0.8,
            "bars": [{"label": "Шрек 2", "value": 928}, {"label": "Мадагаскар", "value": 532},
                     {"label": "Би Муви", "value": 288}]},
        "mascot_said": {"mouth": mouth, "position": "left", "scale": 0.95, "jitter": 0.8,
            "portrait": {"photo": "portrait/katzenberg.jpg", "name": "КАТЦЕНБЕРГ",
                         "role": "сооснователь DreamWorks", "quote": "Мы построили студию, чтобы уничтожить Disney."}},
    }
    only = os.environ.get("ONLY")
    for name, props in scenarios.items():
        if only and name != only:
            continue
        render(name, props, seg)
    print(f"\nвсе сценарии в {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
