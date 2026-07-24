"""Переякоривает всю графику (overlays_rendered.json + cine_scenes.json) под НОВЫЙ
alignment (после пересборки голоса). Позиция берётся по тексту-anchor в новом
alignment; если не нашёлся — старт сцены. Оверлеи, привязанные к удалённым сценам
(подытог), дропаются. Потом переукладка через place_all_graphics.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
TAKEOVER = {"cine", "kinetic", "network", "timeline", "crowd", "shock", "mapspread", "dossier", "scene"}


def norm(s: str) -> str:
    return re.sub(r"[^а-яёa-z0-9]", "", (s or "").replace("́", "").lower())


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))
    words = al["words"]
    scenes = al["scenes"]
    nw = [norm(w["word"]) for w in words]

    def find_anchor(anchor: str):
        t = [norm(x) for x in (anchor or "").split() if norm(x)]
        if len(t) < 2:
            return None
        for i in range(len(nw) - len(t) + 1):
            if nw[i:i + len(t)] == t:
                return words[i]["start"]
        for i in range(len(nw) - 1):  # fuzzy: первое+последнее рядом
            if nw[i] == t[0]:
                for j in range(i + 1, min(i + len(t) + 4, len(nw))):
                    if nw[j] == t[-1]:
                        return words[i]["start"]
        return None

    def reanchor(entry, typ):
        sid = entry.get("scene_id")
        if sid and sid not in scenes:
            return None  # сцена удалена (подытог) → дроп
        lead = 0.5 if typ in TAKEOVER else 0.3
        at = find_anchor(entry.get("anchor", ""))
        if at is None:
            at = scenes.get(sid, {}).get("start")
            if at is None:
                return None
            lead = 0.0
        ns = max(0.0, round(at - lead, 2))
        # не раньше старта своей сцены (для быстрых)
        ss = scenes.get(sid, {}).get("start")
        if ss is not None and typ not in TAKEOVER:
            ns = max(ns, round(ss, 2))
        entry["start"] = ns
        return entry

    # overlays
    data = json.loads((PROJECT / "overlays_rendered.json").read_text(encoding="utf-8"))
    kept = []
    dropped = []
    for o in data["overlays"]:
        r = reanchor(o, o.get("type", ""))
        (kept if r else dropped).append(o["id"])
        if r:
            pass
    data["overlays"] = [o for o in data["overlays"] if o["id"] in kept]
    data["overlays"].sort(key=lambda o: o["start"])
    (PROJECT / "overlays_rendered.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"overlays: переякорено {len(kept)}, дропнуто {len(dropped)} {dropped}")

    # cine scenes
    cs = json.loads((PROJECT / "cine_scenes.json").read_text(encoding="utf-8"))
    ck, cd = [], []
    for c in cs["scenes"]:
        r = reanchor(c, "cine")
        (ck if r else cd).append(c["id"])
    cs["scenes"] = [c for c in cs["scenes"] if c["id"] in ck]
    cs["scenes"].sort(key=lambda c: c["start"])
    (PROJECT / "cine_scenes.json").write_text(json.dumps(cs, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"cine: переякорено {len(ck)}, дропнуто {len(cd)} {cd}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
