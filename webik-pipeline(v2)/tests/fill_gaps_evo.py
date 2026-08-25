"""Заполнитель ДЫР в графике: находит пустые участки >55с на V8, для каждого просит
LLM уместную мягкую графику по закадру (KineticPhrase — ключевая фраза, или NameLabel —
имя/место), рендерит и ДОКЛАДЫВАЕТ на V8 (без чистки существующего). Равномерное покрытие."""
import json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from services.overlays.render_bridge import render_overlays

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
OUTDIR = PROJECT / "assets" / "overlays_gap"
ACCENT = "#1fa48a"
GAP_MIN = 55.0
TOTAL = 2404.0


def mmss(s): return f"{int(s)//60:02d}:{int(s)%60:02d}"


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    by_id = {s["id"]: s for s in scenes}

    # дыры считаем по ЖИВОМУ V8 (реальное состояние таймлайна)
    import pymiere as _pm
    _tps = 254016000000
    v8live = _pm.objects.app.project.activeSequence.videoTracks[7]
    spans = []
    for i in range(v8live.clips.numItems):
        c = v8live.clips[i]
        s = c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / _tps
        e = c.end.seconds if hasattr(c.end, "seconds") else float(c.end.ticks) / _tps
        spans.append((s, e))
    spans.sort()
    gaps = []
    prev = 0.0
    for s, e in spans:
        if s - prev > GAP_MIN:
            gaps.append((prev, s))
        prev = max(prev, e)
    if TOTAL - prev > GAP_MIN:
        gaps.append((prev, TOTAL))
    print(f"дыр >55с: {len(gaps)}")

    # для каждой дыры — сцены внутри (по времени) + текст
    ivals = sorted(((al[sid]["start"], al[sid]["end"], sid) for sid in al if sid in by_id), key=lambda x: x[0])
    tasks = []
    for gi, (gs, ge) in enumerate(gaps):
        mid = (gs + ge) / 2
        inside = [(st, sid) for st, en, sid in ivals if gs + 3 < st < ge - 3]
        if not inside:
            continue
        # сцена ближе к центру дыры — точка постановки
        anchor = min(inside, key=lambda x: abs(x[0] - mid))
        vo = " ".join((by_id[sid].get("voiceover") or "") for st, sid in inside)[:600]
        tasks.append({"gi": gi, "start": round(anchor[0] + 0.3, 2), "vo": vo, "win": f"{mmss(gs)}-{mmss(ge)}"})

    system = ("Ты — режиссёр монтажа. Для куска закадра подбираешь ОДНУ мягкую графику, "
              "которая УМЕСТНА тому, что говорится (без выдумок).")
    rules = """Для КАЖДОГО куска верни объект:
- gi: индекс (как дан)
- comp: "KineticPhrase" (короткая ударная ФРАЗА 3-6 слов ДОСЛОВНО из текста) ИЛИ
        "NameLabel" (если в куске назван КОНКРЕТНЫЙ человек/место/вид/термин)
- phrase: (для KineticPhrase) сама фраза из текста
- name, sub: (для NameLabel) имя/термин + короткое пояснение (2-4 слова)
Выбирай то, что реально есть в тексте. Верни ТОЛЬКО JSON-массив.

КУСКИ:
"""
    lines = [f'{{"gi":{t["gi"]},"vo":"{t["vo"].replace(chr(34)," ")}"}}' for t in tasks]
    llm = ClaudeService(model="google/gemini-2.5-flash")
    res = llm.call_json(rules + "\n".join(lines), max_tokens=6000, temperature=0.4, system=system)
    if isinstance(res, dict):
        res = res.get("items") or res.get("scenes") or []
    dec = {r.get("gi"): r for r in res if r.get("gi") is not None}

    overlays = []
    tmap = {t["gi"]: t for t in tasks}
    for gi, r in dec.items():
        t = tmap.get(gi)
        if not t:
            continue
        comp = r.get("comp")
        if comp == "NameLabel" and r.get("name"):
            props = {"name": r["name"], "sub": r.get("sub", ""), "accent": ACCENT}
        else:
            comp = "KineticPhrase"
            ph = r.get("phrase") or (t["vo"][:40])
            props = {"phrase": ph, "accent": ACCENT}
        overlays.append({"id": f"gap_{int(t['start'])}", "composition": comp, "type": "phrase",
                         "start": t["start"], "props": props})
    print(f"к рендеру: {len(overlays)}")
    if not overlays:
        return 0
    render_overlays(overlays, OUTDIR, overwrite=True)

    # доукладка на V8 (без чистки)
    import pymiere
    from pymiere.wrappers import time_from_seconds
    from services.premiere_template.timeline_ops import import_media
    seq = pymiere.objects.app.project.activeSequence
    v8 = seq.videoTracks[7]
    placed = 0
    for o in overlays:
        mov = OUTDIR / f"{o['id']}.mov"
        if not mov.exists():
            continue
        item = import_media(mov)
        if item is None:
            continue
        try:
            v8.overwriteClip(item, time_from_seconds(round(o["start"], 2)))
            placed += 1
            print(f"  ✓ {mmss(o['start'])} {o['composition']}")
        except Exception as e:
            print(f"  ✗ {o['id']}: {str(e)[:50]}")
    pymiere.objects.app.project.save()
    print(f"\nзаполнено дыр: {placed}/{len(overlays)}; проект сохранён")
    return 0


if __name__ == "__main__":
    sys.exit(main())
