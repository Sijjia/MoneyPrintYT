"""Добивает пропущенные archive-сцены DreamWorks через yt-dlp-видео (интервью/хроника/тесты)
+ апскейл. Читает media_plan_dw.json, берёт то, чего нет в манифесте."""
import json, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.source_media_dw import fetch_movie, VID, IMG

PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"

def main():
    plan = json.loads((PROJECT / "media_plan_dw.json").read_text(encoding="utf-8"))
    man = json.loads((IMG / "manifest.json").read_text(encoding="utf-8"))
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    order = {s["id"]: i for i, s in enumerate(scenes)}
    miss = sorted([(sid, p) for sid, p in plan.items() if sid not in man],
                  key=lambda kv: order.get(kv[0], 9999))
    print(f"добиваю: {len(miss)}")
    tmp = Path(tempfile.mkdtemp())
    ok = fail = 0
    for k, (sid, p) in enumerate(miss):
        q = p.get("query", ""); fb = p.get("fallback", "")
        out = VID / f"{sid}.mp4"
        got = fetch_movie(q, out, k, tmp) or (fb and fetch_movie(fb, out, k + 2, tmp))
        if got:
            man[sid] = {"path": str(out), "query": q, "kind": "video", "source": "youtube-dw"}
            ok += 1; print(f"  ✓ {sid} «{q[:44]}»", flush=True)
        else:
            fail += 1; print(f"  ✗ {sid} «{q[:44]}»", flush=True)
        if (k + 1) % 10 == 0:
            (IMG / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (IMG / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nдобито: {ok}, осталось битых: {fail} | манифест {len(man)}")

if __name__ == "__main__":
    main()
