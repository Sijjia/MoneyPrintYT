"""Рендер живой сцены первой темы GTA: капибара (липсинк) + разнотипные моушн-графики
с человечками (толпа-просмотры → кэш → стопки денег → диски). Одна длинная сцена на
весь отрезок 008→конец темы; заменяет счётчики 008-012. Обновляет manifest.
  ../webik-pipeline/.venv/Scripts/python.exe tests/records_stage_gta.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.mascot_demo as md

PROJECT = ROOT / "projects" / "2026-09-06_aysberg-gta-temnaya-storona-realnye-dela-vnutriigrovye-tayny"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "graphics"; GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
FPS = 30
ANCHOR = "scene_008"
END_SID = "scene_013"          # начало след. темы — конец нашего отрезка
DROP = ["scene_009", "scene_010", "scene_011", "scene_012"]  # уберём из манифеста (накроет 008)


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    t0 = al[ANCHOR]["start"]
    t_end = al[END_SID]["start"]
    dur = t_end - t0
    frames = int(dur * FPS)
    rf = lambda sid: int((al[sid]["start"] - t0) * FPS)

    segments = [
        {"from": 0,               "to": rf("scene_010"), "kind": "views",  "value": 90421491,
         "label": "ПРОСМОТРОВ ЗА 24 ЧАСА", "sub": "трейлер GTA VI · рекорд Гиннесса"},
        {"from": rf("scene_010"), "to": rf("scene_011"), "kind": "cash",   "value": 800000000, "prefix": "$",
         "label": "ЗА ПЕРВЫЙ ДЕНЬ", "sub": "GTA V · 2013"},
        {"from": rf("scene_011"), "to": rf("scene_012"), "kind": "stacks", "value": 6000000000, "prefix": "$",
         "label": "ВЫРУЧКА К 2018", "sub": "GTA Online — сотни млн ежегодно"},
        {"from": rf("scene_012"), "to": frames,          "kind": "discs",  "value": 200000000,
         "label": "КОПИЙ ПРОДАНО", "sub": "на всех платформах"},
    ]

    # липсинк на весь отрезок
    seg_wav = GFX / "_records_voice.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{t0:.2f}", "-t", f"{dur:.2f}", "-i", str(VOICE),
                    "-ac", "1", "-ar", "22050", str(seg_wav)], capture_output=True)
    mouth = md.mouth_track(seg_wav, dur + 0.2, FPS)

    props = {"mouth": mouth, "segments": segments, "accent": "#ff2d78", "accent2": "#25e0c8",
             "durationInFrames": frames}
    pf = REMOTION / "_records_stage.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{ANCHOR}.mp4"
    print(f"рендер GTARecordsStage {dur:.1f}с ({frames}f), сегменты по {[s['kind'] for s in segments]}", flush=True)
    r = subprocess.run(f'npx remotion render GTARecordsStage "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    if not (out.exists() and out.stat().st_size > 100000):
        print(f"✗ рендер упал: {r.stderr[-400:]}"); return 1

    # манифест: 008 → сцена-стейдж, 009-012 убрать (накроет длинная сцена)
    man[ANCHOR] = {"path": str(out.resolve()), "kind": "video", "graphic": "records_stage", "query": "GTA records stage"}
    for sid in DROP:
        man.pop(sid, None)
    (PROJECT / "assets" / "images" / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    # чистим _trimmed этих сцен
    tr = PROJECT / "assets" / "video_stock" / "_trimmed"
    for sid in [ANCHOR] + DROP:
        f = tr / f"{sid}.mp4"
        if f.exists(): f.unlink()
    print(f"✓ GTARecordsStage → {out.name} ({dur:.1f}с); манифест: 008=стейдж, 009-012 убраны", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
