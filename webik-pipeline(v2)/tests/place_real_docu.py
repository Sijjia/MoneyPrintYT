"""Точечно кладёт РЕАЛЬНЫЕ фото (DocuFrame) на конкретные сцены живого таймлайна (Premiere открыт),
overwrite на V3 — без пересборки. JOBS: (sid, image_file_in_real_photos, kicker, title, source, kb).
Разные картинки → разные сцены (без повторов)."""
import json, os, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

P = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
REMOTION = ROOT / "remotion"
PUBREAL = REMOTION / "public" / "real"; PUBREAL.mkdir(parents=True, exist_ok=True)
PHOTOS = P / "assets" / "real_photos"
GFX = P / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
MANIFEST = P / "assets" / "images" / "manifest.json"
FPS = 30

# (сцена, файл-в-real_photos, кикер, заголовок, источник, ken-burns)
JOBS = [
    # добор: лицо Момо на сцену-описание внешности + другой ракурс на «сообщения детям»
    ("scene_184", "momo_face.jpg",  "ОБРАЗ", "«Момо» — скульптура «Mother Bird»", "Keisuke Aisawa", "in"),
    ("scene_188", "momo_kids.jpg",  "СЛУХ",  "«Момо»",                            "Keisuke Aisawa", "out"),
]
_JOBS_DONE = [
    ("scene_182", "momo_artist.jpg", "РАЗОБЛАЧЕНО", "Кэйсукэ Айсо и его скульптура", "Link Factory / Mothership", "out"),
    ("scene_193", "momo_full2.jpg",  "ИСТЕРИЯ",     "«Момо» — скульптура «Mother Bird»", "Link Factory", "left"),
    ("scene_197", "bos_blast.jpg",     "15 АПРЕЛЯ 2013", "Взрывы на Бостонском марафоне",    "Aaron Tang / Wikimedia", "in"),
    ("scene_198", "bos_aftermath.jpg", "МЕСТО ВЗРЫВА",   "Экстренные службы на месте",       "Wikimedia Commons", "right"),
    ("scene_205", "bos_memorial.jpg",  "ПАМЯТЬ",         "Мемориал жертвам марафона",        "Wikimedia Commons", "out"),
]


def render_docu(sid, kicker, title, source, frames, kb):
    props = {"imgSrc": f"real/{sid}.jpg", "kicker": kicker, "title": title,
             "source": source, "kenburns": kb, "durationInFrames": frames}
    pf = REMOTION / f"_docu_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_gfx.mp4"
    if out.exists():
        out.unlink()
    subprocess.run(f'npx remotion render DocuFrame "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out if (out.exists() and out.stat().st_size > 20000) else None


def main() -> int:
    al = json.loads((P / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    ga = P / "_gfx_assigns.json"
    assigns = json.loads(ga.read_text(encoding="utf-8")) if ga.exists() else {}
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[2]
    starts = [c.start.seconds for c in v3.clips]
    ok = 0
    for sid, img, kicker, title, source, kb in JOBS:
        src = PHOTOS / img
        if not src.exists():
            print(f"  ✗ {sid}: нет файла {img}", flush=True); continue
        st = al[sid]["start"]
        clip = min(v3.clips, key=lambda c: abs(c.start.seconds - st))
        t0 = clip.start.seconds
        slot = clip.end.seconds - clip.start.seconds
        frames = max(45, round(slot * FPS))
        shutil.copy2(src, PUBREAL / f"{sid}.jpg")
        out = render_docu(sid, kicker, title, source, frames, kb)
        if not out:
            print(f"  ✗ {sid}: рендер DocuFrame упал", flush=True); continue
        item = import_media(out.resolve())
        if item is None:
            print(f"  ✗ {sid}: import упал", flush=True); continue
        v3.overwriteClip(item, time_from_seconds(t0))
        man[sid] = {"path": str(out.resolve()), "query": f"web: {title}", "kind": "video", "source": "docuframe"}
        assigns[sid] = {"id": sid, "component": "DocuFrame", "props": {"title": title}}
        ok += 1
        print(f"  ✓ {sid} «{title}» @ {int(t0//60)}:{int(t0%60):02d} ({slot:.1f}с, {frames}f)", flush=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    ga.write_text(json.dumps(assigns, ensure_ascii=False, indent=1), encoding="utf-8")
    pymiere.objects.app.project.save()
    print(f"\nГОТОВО: реальных фото уложено {ok}/{len(JOBS)}; сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
