"""Рендер анимированных счётчиков (StolenCounter) для числовых моментов GTA-ролика.
Полноэкранная графика 1080p как base-media на V3 (кладётся финальной пере-сборкой).
Пишет assets/graphics/scene_XXX.mp4 + обновляет manifest (kind=video, graphic=counter).
  ../webik-pipeline/.venv/Scripts/python.exe tests/counters_gta.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "graphics"; GFX.mkdir(parents=True, exist_ok=True)
ACCENT = "#37c85a"  # деньги/успех — зелёный акцент

# sid → props StolenCounter
COUNTERS = {
    "scene_008": {"value": 90421491, "prefix": "", "suffix": "", "label": "ПРОСМОТРОВ ЗА 24 ЧАСА",
                  "sub": "трейлер GTA VI · рекорд Гиннесса", "caption": "Обошёл даже MrBeast с его 59 миллионами."},
    "scene_010": {"value": 800000000, "prefix": "$", "suffix": "", "label": "ЗА ПЕРВЫЙ ДЕНЬ ПРОДАЖ",
                  "sub": "GTA V · 2013", "caption": "Миллиард выручки — меньше чем за три дня."},
    "scene_011": {"value": 6000000000, "prefix": "$", "suffix": "", "label": "СОВОКУПНАЯ ВЫРУЧКА К 2018",
                  "sub": "без учёта последних лет", "caption": "GTA Online приносит сотни миллионов ежегодно."},
    "scene_012": {"value": 200000000, "prefix": "", "suffix": "", "label": "КОПИЙ ПРОДАНО",
                  "sub": "на всех платформах", "caption": "Один из самых прибыльных продуктов в истории."},
}


def slot_durations():
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    starts = sorted([(al[s["id"]]["start"], s["id"]) for s in sc if s["id"] in al])
    return {sid: (starts[i + 1][0] if i + 1 < len(starts) else st + 5) - st
            for i, (st, sid) in enumerate(starts)}


def render(sid, props, frames):
    props = dict(props); props["accent"] = ACCENT; props["durationInFrames"] = frames
    pf = REMOTION / f"_cnt_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}.mp4"
    r = subprocess.run(f'npx remotion render StolenCounter "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 50000):
        print(f"  ✗ {sid}: {r.stderr[-200:]}"); return None
    return out


def main() -> int:
    slots = slot_durations()
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    n = 0
    for sid, props in COUNTERS.items():
        d = max(4.0, slots.get(sid, 5.0) + 0.4)
        frames = int(d * 30)
        out = render(sid, props, frames)
        if out:
            man[sid] = {"path": str(out.resolve()), "kind": "video", "graphic": "counter", "query": props["label"]}
            t = PROJECT / "assets" / "video_stock" / "_trimmed" / f"{sid}.mp4"
            if t.exists(): t.unlink()
            n += 1
            print(f"  ✓ счётчик {sid} → {props['prefix']}{props['value']:,} ({d:.1f}с)", flush=True)
    (PROJECT / "assets" / "images" / "manifest.json").write_text(
        json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nсчётчиков отрендерено: {n}; манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
