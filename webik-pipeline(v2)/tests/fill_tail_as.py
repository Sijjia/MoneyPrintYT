"""Точечный дозабор 18 хвостовых сцен Adult Swim без медиа: реальный футаж с YouTube
(жуткие инфомершлы-ARG, возвращение Toonami, MDE World Peace, пресс-конференция про причёски),
для инцидента-2008 без футажа — атмосферное ночное ТВ (Pexels). Пишет в assets/images/manifest.json.
Требует запущенный POT-сервер (порт 4416).
  ../webik-pipeline/.venv/Scripts/python.exe tests/fill_tail_as.py
"""
import json, sys, tempfile, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tests.source_media_dw import fetch_movie
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
IMG = PROJECT / "assets" / "images"
VID = PROJECT / "assets" / "video_stock"
VID.mkdir(parents=True, exist_ok=True)

# Ручные запросы под реальный футаж. yt = YouTube (fetch_movie), px = Pexels атмосфера.
YT = {
    "scene_044": "Mooninite Boston 2007 press conference haircuts Berdovsky Stevens",
    "scene_045": "Peter Berdovsky Sean Stevens press conference 1970s hairstyles",
    "scene_056": "Toonami return 2012 TOM Adult Swim April Fools",
    "scene_059": "Toonami revival 2012 TOM SARA Adult Swim",
    "scene_061": "Toonami 2012 comeback Adult Swim announcement bump",
    "scene_188": "This House Has People In It Adult Swim infomercial",
    "scene_189": "Unedited Footage of a Bear Adult Swim infomercial",
    "scene_190": "Live Forever As You Are Now with Alan Resnick Adult Swim",
    "scene_191": "This House Has People In It Adult Swim creepy",
    "scene_195": "Adult Swim infomercial unsettling night",
    "scene_196": "Alantutorial Adult Swim infomercial",
    "scene_197": "This House Has People In It ending Adult Swim",
    "scene_207": "Million Dollar Extreme World Peace Adult Swim",
    "scene_209": "Sam Hyde Million Dollar Extreme World Peace Adult Swim show",
    "scene_210": "Million Dollar Extreme World Peace sketch Adult Swim",
}
PX = {
    "scene_214": "empty playground dusk eerie",
    "scene_224": "dark living room tv glow night",
    "scene_225": "old crt television static dark room",
}


def md5f(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None


def main() -> int:
    man = json.loads((IMG / "manifest.json").read_text(encoding="utf-8"))
    tmp = Path(tempfile.mkdtemp())
    px = PexelsVideosClient()
    seen = {md5f(m.get("path")) for m in man.values() if m.get("path")}
    seen.discard(None)
    ok = fail = 0

    for k, (sid, q) in enumerate(YT.items()):
        out = VID / f"{sid}.mp4"
        got = False
        for attempt, idx in enumerate((k, k + 5, k + 11)):
            if fetch_movie(q, out, idx, tmp):
                h = md5f(out)
                if h and h not in seen:           # против визуальных повторов
                    seen.add(h); got = True; break
        if got:
            man[sid] = {"path": str(out), "query": q, "kind": "video", "source": "youtube-as"}
            ok += 1; print(f"  ✓ {sid} «{q[:45]}»", flush=True)
        else:
            fail += 1; print(f"  ✗ {sid} НЕ скачалось «{q[:45]}»", flush=True)

    for k, (sid, q) in enumerate(PX.items()):
        out = VID / f"{sid}.mp4"
        got = False
        for query in (q, "dark night television old", "vhs static noise dark"):
            try:
                if px.search_and_download(query, out, index=(k % 3)) and out.stat().st_size > 20000:
                    h = md5f(out)
                    if h and h not in seen:
                        seen.add(h); got = True; break
            except Exception:
                pass
        if got:
            man[sid] = {"path": str(out), "query": q, "kind": "video", "source": "pexels-atmos"}
            ok += 1; print(f"  ✓ {sid} (атмосфера) «{q[:40]}»", flush=True)
        else:
            fail += 1; print(f"  ✗ {sid} атмосфера не нашлась", flush=True)

    (IMG / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nИТОГ: добрано {ok}, не удалось {fail} | manifest = {len(man)} записей", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
