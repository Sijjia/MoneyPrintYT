"""Закрывает зазоры на V3 от фото-сцен: для каждой archive-картинки рендерит
PhotoZoom (Ken Burns) на длину слота сцены и кладёт на V3 (overwrite), заменяя
короткий стиль. Фаза 1 (рендер, без Premiere) → Фаза 2 (укладка, pymiere)."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
REMOTION = ROOT / "remotion"
PUB = REMOTION / "public" / "photos"
OUT = PROJECT / "assets" / "photozoom"
PUB.mkdir(parents=True, exist_ok=True); OUT.mkdir(parents=True, exist_ok=True)


def main() -> int:
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    imgs = [(sid, v) for sid, v in man.items() if v.get("kind") == "image" and sid in al]
    print(f"фото-сцен: {len(imgs)}")

    # ── Фаза 1: рендер PhotoZoom ──
    rendered = {}
    for k, (sid, v) in enumerate(imgs):
        a = al[sid]; slot = max(2.0, a["end"] - a["start"]); frames = max(60, round((slot + 0.3) * 30))
        outp = OUT / f"{sid}.mp4"
        if outp.exists() and outp.stat().st_size > 20000:
            rendered[sid] = outp; continue
        src = Path(v["path"])
        if not src.exists(): print(f"  ✗ {sid}: нет исходника"); continue
        pub = PUB / f"dwpz_{sid}.jpg"; shutil.copy(src, pub)
        props = REMOTION / f"_pz_{sid}.json"
        props.write_text(json.dumps({"img": f"photos/dwpz_{sid}.jpg",
                                     "dir": "in" if k % 2 else "out", "durationInFrames": frames}), encoding="utf-8")
        rel_out = os.path.relpath(outp, REMOTION).replace(os.sep, "/")
        rel_props = os.path.relpath(props, REMOTION).replace(os.sep, "/")
        r = subprocess.run(
            f'npx remotion render PhotoZoom "{rel_out}" '
            f'--props="{rel_props}" --codec=h264 --muted --log=error',
            cwd=str(REMOTION), capture_output=True, text=True, shell=True)
        props.unlink(missing_ok=True)
        if outp.exists() and outp.stat().st_size > 20000:
            rendered[sid] = outp
            if (len(rendered)) % 10 == 0: print(f"  ...рендер {len(rendered)}/{len(imgs)}", flush=True)
        else:
            print(f"  ✗ {sid}: рендер упал {(r.stderr or '')[-120:]}", flush=True)
    print(f"отрендерено PhotoZoom: {len(rendered)}/{len(imgs)}")

    # ── Фаза 2: укладка на V3 (overwrite) ──
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    placed = 0
    for sid, outp in sorted(rendered.items(), key=lambda kv: al[kv[0]]["start"]):
        try:
            item = import_media(outp)
            if item is None: print(f"  ✗ import {sid}"); continue
            v3.overwriteClip(item, time_from_seconds(round(al[sid]["start"], 2)))
            placed += 1
            if placed % 15 == 0: print(f"  ...уложено {placed}", flush=True)
        except Exception as e:
            print(f"  ✗ place {sid}: {str(e)[:60]}")
    pymiere.objects.app.project.save()
    print(f"\nуложено PhotoZoom на V3: {placed}/{len(rendered)}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
