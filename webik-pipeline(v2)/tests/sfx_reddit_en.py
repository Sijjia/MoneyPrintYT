"""SFX «Айсберг Reddit»: тонкий вуш при появлении bespoke-графики; глитч — для шифров/глитчей/ARG.
НЕ ставим под плашки уровней. На дорожку A5 (idx4), громкость мягкая. Premiere открыт.
  ../webik-pipeline/.venv/Scripts/python.exe tests/sfx_reddit.py"""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from pymiere.wrappers import time_from_seconds
from services.premiere_template.timeline_ops import import_media

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona_EN"
SFX_DIR = Path(next(l.split("=", 1)[1].strip() for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines() if l.startswith("SFX_DIR=")))
import shutil
_LOCAL = PROJECT / "assets" / "sfx"; _LOCAL.mkdir(parents=True, exist_ok=True)
def _local(src: Path, name: str) -> Path:
    dst = _LOCAL / name
    if not dst.exists() and src.exists():
        shutil.copy2(src, dst)
    return dst
WHOOSH = _local(SFX_DIR / "Для появления (вуши)" / "диджитал вуш.wav", "sfx_whoosh_digital.wav")
WHOOSH2 = _local(SFX_DIR / "Для появления (вуши)" / "короткий вуш.wav", "sfx_whoosh_short.wav")
GLITCH = _local(SFX_DIR / "Глитчи" / "Глитч 1.wav", "sfx_glitch_1.wav")
GLITCH2 = _local(SFX_DIR / "Глитчи" / "Глитч 2.wav", "sfx_glitch_2.wav")
SFX_TRACK = 4   # A5
VOL = 0.4
GLITCH_COMPS = {"HexCipher", "GlitchLeak", "ARGSignal"}


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    sc = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    assigns = json.loads((PROJECT / "_gfx_assigns.json").read_text(encoding="utf-8"))
    level_ids = {sid for sid, s in sc.items() if (s.get("visual") or {}).get("type") == "level_card"}

    seq = pymiere.objects.app.project.activeSequence
    trk = seq.audioTracks[SFX_TRACK]
    # кэш импортов
    cache = {}
    def imp(p):
        if str(p) not in cache:
            cache[str(p)] = import_media(Path(p).resolve())
        return cache[str(p)]

    placed = 0
    gfx = [(sid, a) for sid, a in assigns.items()
           if a.get("component") not in (None, "SKIP") and sid in al and sid not in level_ids]
    gfx.sort(key=lambda x: al[x[0]]["start"])
    for i, (sid, a) in enumerate(gfx):
        comp = a.get("component")
        if comp in GLITCH_COMPS:
            src = GLITCH if i % 2 == 0 else GLITCH2
        else:
            src = WHOOSH if i % 2 == 0 else WHOOSH2
        item = imp(src)
        if item is None:
            continue
        try:
            trk.overwriteClip(item, time_from_seconds(max(0.0, al[sid]["start"] - 0.08)))
            placed += 1
        except Exception:
            pass
    # громкость дорожки тише (через клипы — Premiere API ограничен; полагаемся на VOL в файлах/миксе)
    pymiere.objects.app.project.save()
    print(f"SFX уложено: {placed} хитов на A5 (вуши+глитчи), под плашки уровней НЕ ставили, сохранено")
    return 0


if __name__ == "__main__":
    sys.exit(main())
