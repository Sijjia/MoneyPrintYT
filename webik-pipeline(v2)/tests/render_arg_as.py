"""Рендерит bespoke ARG-графику (ARGSignal) как БАЗОВОЕ медиа для L3-блока Adult Swim
(скрытый сигнал → дешифровка → тишина → нет ответа → передача прервана → проект брошен).
6 уникальных режимов, длительность = слот сцены. Пишет в video_stock + manifest.json.
  ../webik-pipeline/.venv/Scripts/python.exe tests/render_arg_as.py
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.assemble_as as A

REMOTION = ROOT / "remotion"
PROJECT = A.PROJECT_DIR
VID = PROJECT / "assets" / "video_stock"
IMG = PROJECT / "assets" / "images"
VID.mkdir(parents=True, exist_ok=True)

# sid → (mode, caption, code)
JOBS = {
    "scene_188": ("signal", "Скрытые сайты. Коды. Послания в ночном эфире.", "as://hidden/delilah_signal"),
    "scene_190": ("decode", "Каждую неделю — новая деталь. ARG набирал обороты.", "decrypt: fragment_47 … ok"),
    "scene_191": ("silence", "А потом проект внезапно заглох.", "as://feed status: STALLED"),
    "scene_195": ("static", "Ни объявлений. Ни объяснений.", "query: why? -> (no response)"),
    "scene_196": ("terminated", "Создателей ARG уволили при реструктуризации.", "creators -> TERMINATED"),
    "scene_197": ("abandoned", "Проект потерял команду. Его так и не закончили.", "project: unfinished // team=0"),
}


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    alignment = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    manifest = json.loads((IMG / "manifest.json").read_text(encoding="utf-8"))
    plan = A.build_scene_plan(scenes, alignment["scenes"], float(alignment["duration"]), manifest)
    dur = {e["id"]: e["target_dur"] for e in plan}

    ok = 0
    for sid, (mode, caption, code) in JOBS.items():
        frames = max(60, round(dur.get(sid, 3.0) * 30))
        props = REMOTION / f"_arg_{sid}.json"
        props.write_text(json.dumps({"mode": mode, "caption": caption, "code": code,
                                     "durationInFrames": frames}, ensure_ascii=False), encoding="utf-8")
        outp = VID / f"{sid}.mp4"
        cmd = (f'npx remotion render ARGSignal "{os.path.relpath(outp, REMOTION)}" '
               f'--props="{os.path.relpath(props, REMOTION)}" --codec=h264 --muted --log=error')
        r = subprocess.run(cmd, cwd=str(REMOTION), shell=True, capture_output=True, text=True)
        props.unlink(missing_ok=True)
        if r.returncode == 0 and outp.exists() and outp.stat().st_size > 20000:
            manifest[sid] = {"path": str(outp), "query": f"ARG {mode}", "kind": "video", "source": "arg-graphic"}
            ok += 1
            print(f"  ✓ {sid} [{mode}] {frames}f", flush=True)
        else:
            print(f"  ✗ {sid} render fail: {(r.stderr or r.stdout)[-200:]}", flush=True)

    (IMG / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nARG-графика: {ok}/{len(JOBS)} | manifest={len(manifest)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
