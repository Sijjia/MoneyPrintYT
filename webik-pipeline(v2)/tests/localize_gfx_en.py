"""EN-локализация bespoke-графики Reddit: переводит текст-props из _gfx_assigns RU→EN, ре-рендерит
каждый компонент на EN-тайминге → assets/gfx, правит EN-манифест. Плейсмент — отдельным ES-скриптом.
Рендерит только компоненты из VALID; DocuFrame достраивает imgSrc/kicker/source."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

EN = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona_EN"
REMOTION = ROOT / "remotion"
GFX = EN / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
MANIFEST = EN / "assets" / "images" / "manifest.json"
GA = EN / "_gfx_assigns.json"
FPS = 30
VALID = {"RedditThread", "HexCipher", "LiminalSpace", "ARGSignal", "EvidenceFrame", "DocuFrame", "NewsAlert"}

SYSTEM = ("You localize on-screen motion-graphics text for a dark documentary about Reddit's strange side "
          "(US English). Translate Russian display strings to concise, punchy English for overlays. Keep the "
          "same JSON keys. Keep subreddit names (r/nosleep, r/A858...), proper nouns, film/site names, and any "
          "numbers/dates as-is. Short stamps/labels/kickers stay SHORT & UPPERCASE (РАЗОБЛАЧЕНО->EXPOSED, "
          "АРХИВ->ARCHIVE, ФАКТ->FACT, СЛУХ->RUMOR, ИСТЕРИЯ->HYSTERIA, РЕАЛЬНЫЙ ТРЕД->REAL THREAD). Reddit thread "
          "titles/bodies read naturally. Never leave Cyrillic. Do not add keys except an EN 'kicker' for DocuFrame.")
RULES = ('For each scene below return the SAME props object but with every Russian text value translated to '
         'English (keep keys, keep subreddit/proper nouns/numbers). For component "DocuFrame" ALSO add a short '
         'uppercase English "kicker" (<=14 chars) fitting the scene. Return ONLY a JSON object: '
         '{scene_id: {..translated props..}}. Scenes (id | component | props | context):')


def slot_dur():
    al = json.loads((EN / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    sc = json.loads((EN / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    order = sorted([(al[s["id"]]["start"], s["id"]) for s in sc if s["id"] in al])
    d = {}
    for i, (st, sid) in enumerate(order):
        d[sid] = max(2.0, (order[i + 1][0] if i + 1 < len(order) else st + 4) - st)
    return d


def render(comp, props, out, frames):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_en_{out.stem}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    if out.exists():
        out.unlink()
    subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out.exists() and out.stat().st_size > 20000


def main() -> int:
    assigns = json.loads(GA.read_text(encoding="utf-8"))
    scenes = {s["id"]: s for s in json.loads((EN / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dur = slot_dur()
    targets = [(sid, a) for sid, a in assigns.items() if a.get("component") in VALID]
    print(f"bespoke к локализации: {len(targets)}", flush=True)

    # --- перевод props батчами ---
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    tr = {}
    B = 12
    for i in range(0, len(targets), B):
        chunk = targets[i:i + B]
        lines = []
        for sid, a in chunk:
            vo = (scenes.get(sid, {}).get("voiceover") or "")[:120]
            lines.append(f'{sid} | {a["component"]} | {json.dumps(a.get("props", {}), ensure_ascii=False)} | {vo}')
        try:
            res = llm.call_json(RULES + "\n" + "\n".join(lines), max_tokens=6000, temperature=0.2, system=SYSTEM)
            if isinstance(res, dict):
                tr.update(res)
            print(f"  перевод батч {i//B+1}: +{len(res) if isinstance(res,dict) else 0}", flush=True)
        except Exception as e:
            print(f"  батч {i//B+1} упал: {str(e)[:60]}", flush=True)

    # --- рендер ---
    ok = fail = 0
    for k, (sid, a) in enumerate(sorted(targets)):
        comp = a["component"]
        props = dict(tr.get(sid) or a.get("props", {}))
        if comp == "DocuFrame":
            q = man.get(sid, {}).get("query", "")
            src = "Wikipedia" if q.startswith("web:") else ("Wikimedia Commons" if "Commons" in q else "Archive")
            props = {"imgSrc": f"real/{sid}.jpg", "kicker": (props.get("kicker") or "ARCHIVE")[:14],
                     "title": props.get("title") or q.split(":", 1)[-1].strip(),
                     "source": src, "kenburns": ["in", "out", "left", "right"][k % 4]}
        frames = max(60, int(round(dur.get(sid, 3.0) * FPS)))
        out = GFX / f"{sid}_gfx.mp4"
        if render(comp, props, out, frames):
            man[sid] = {"path": str(out.resolve()), "query": f"en-gfx: {comp}", "kind": "video",
                        "source": ("docuframe" if comp == "DocuFrame" else "gfx-reddit")}
            ok += 1
            if ok % 8 == 0:
                print(f"  ...отрендерено {ok}", flush=True)
        else:
            fail += 1; print(f"  ✗ {sid} {comp} render fail", flush=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО EN-графика: отрендерено {ok}, ошибок {fail} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
