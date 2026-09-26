"""Директор bespoke-графики «Айсберг Индии»: LLM подбирает ОДИН тематический компонент для сцен
нужных тем (Варанаси/Патала/Рупкунд/форты/храм-дверь/тхаги) + пропсы СТРОГО по фактам из vo,
рендерит под длину слота, ставит базовым медиа в манифест. Плотность: cap на компонент.
  ../webik-pipeline/.venv/Scripts/python.exe tests/gfx_director_india.py
Env: GFX_LIMIT, GFX_ONLY (список sid), GFX_CAP (макс сцен на компонент, деф 2)."""
import json, os, subprocess, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
FPS = 30
CARD = {"level_card", "topic_card"}

SYSTEM = ("Ты — арт-директор документалки про мистическую/тёмную сторону Индии. Для сцены выбираешь ОДИН "
          "bespoke-компонент графики ТОЛЬКО если он ТОЧНО соответствует теме сцены, иначе component=SKIP. "
          "Пропсы заполняй фактами ТОЛЬКО из текста сцены (vo): цифры/суммы/имена/годы строго из vo, ничего "
          "не выдумывай. Компоненты узко-тематические — не ставь их не по теме.")

RULES = """Компоненты (ставь СТРОГО по смыслу, иначе SKIP; факты только из vo):
- "GangesGhats": ТОЛЬКО про Варанаси / погребальные гхаты / кремации на Ганге / город смерти.
  props: {kicker:"ВАРАНАСИ", title: короткий заголовок КАПСОМ (из смысла vo), caption: 1 фраза из vo}.
- "NagaUnderworld": ТОЛЬКО про Паталу / нагов / подземный мир змеелюдей / индуистскую космологию низших миров.
  props: {kicker:"ПАТАЛА", title: КАПСОМ, caption}.
- "SkeletonLake": ТОЛЬКО про Рупкунд / озеро скелетов / ДНК-загадку / град. props:
  {kicker:"РУПКУНД", title: КАПСОМ, eras?: [{label:"I в. н.э.",note:"..."},{label:"IX в.",note:"..."},{label:"XIX в.",note:"..."}] (если vo про 3 эпохи), caption}.
- "FortCurse": ТОЛЬКО про форт Бхангарх ИЛИ деревню Кулдхара / проклятое заброшенное место / запрет входа.
  props: {kicker:"ФОРТ БХАНГАРХ"|"КУЛДХАРА", title: КАПСОМ, sign?: текст запрета (если про табличку ASI), caption}.
- "VaultDoorB": ТОЛЬКО про храм Падманабхасвами / запертую Дверь B / сокровища храма. props:
  {kicker:"ПАДМАНАБХАСВАМИ", title: КАПСОМ, valueText?:"$22 000 000 000" (если сумма в vo), doorLabel?:"ДВЕРЬ B — ЗАПЕЧАТАНА", caption}.
- "ThugStrangler": ТОЛЬКО про тхагов / культ душителей Кали / удушение путников. props:
  {kicker:"ТХАГИ", title: КАПСОМ, victims?: число жертв (из vo, напр. 50000), victimLabel?:"жертв за столетия", era?:"XIII–XIX вв.", caption}.
- "SKIP": во всех остальных случаях (нормальный видеоряд, тема не совпадает).

Верни ТОЛЬКО JSON-массив: [{"id","component","props"}]. props — валидный объект под компонент. Числа — числами."""

VALID = {"GangesGhats", "NagaUnderworld", "SkeletonLake", "FortCurse", "VaultDoorB", "ThugStrangler"}


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0


def slot_durations():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    order = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
    dur = {}
    for i, (st, sid) in enumerate(order):
        nx = order[i + 1][0] if i + 1 < len(order) else st + 4
        dur[sid] = max(1.5, nx - st)
    return dur


def render(comp, props, out, frames):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_gfx_{out.stem}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    ok = out.exists() and out.stat().st_size > 20000
    if not ok:
        print(f"    ✗ render {comp}: {(r.stderr or r.stdout)[-160:]}")
    return ok


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))

    # кандидаты: все НЕ-карточные сцены (LLM сам SKIP-нет нерелевантные)
    cand = [sid for sid, s in scenes.items() if (s.get("visual") or {}).get("type") not in CARD]
    only = [x.strip() for x in os.environ.get("GFX_ONLY", "").split(",") if x.strip()]
    if only: cand = [s for s in only if s in scenes]
    lim = int(os.environ.get("GFX_LIMIT", "0"))
    if lim: cand = cand[:lim]
    print(f"кандидатов к графике: {len(cand)}", flush=True)

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    assigns = {}
    B = 24
    for i in range(0, len(cand), B):
        chunk = cand[i:i + B]
        lines = [f'{{"id":"{s}","topic":"{id2t.get(scenes[s].get("topic_id"),"")}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:220]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=5000, temperature=0.3, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("assignments") or []
            for r in res:
                if r.get("id") and r.get("component") in VALID:
                    assigns[r["id"]] = r
        except Exception as e:
            print(f"  батч упал: {str(e)[:70]}")
        print(f"  {min(i+B,len(cand))}/{len(cand)}", flush=True)

    # density cap: не более GFX_CAP сцен на компонент (берём по порядку появления)
    cap = int(os.environ.get("GFX_CAP", "2"))
    order = [s for s in cand if s in assigns]
    per = collections.Counter()
    keep = {}
    for sid in order:
        comp = assigns[sid]["component"]
        if per[comp] < cap:
            keep[sid] = assigns[sid]; per[comp] += 1
    print(f"\nназначено (после cap={cap}): {dict(collections.Counter(a['component'] for a in keep.values()))}", flush=True)
    for sid, a in keep.items():
        print(f"    {sid} [{id2t.get(scenes[sid].get('topic_id'),'?')[:28]}] → {a['component']}", flush=True)

    # СНАЧАЛА сохраняем план (чтобы не терять при сбое рендера)
    apath = PROJECT / "_gfx_assigns.json"
    save = dict(keep)
    if only and apath.exists():
        prev = json.loads(apath.read_text(encoding="utf-8")); prev.update(keep); save = prev
    apath.write_text(json.dumps(save, ensure_ascii=False, indent=1), encoding="utf-8")

    dur = slot_durations()
    placed = fail = 0
    for sid, a in keep.items():
        frames = int(round(dur.get(sid, 4.0) * FPS)) + 15
        out = GFX / f"{sid}_gfx.mp4"
        if render(a["component"], a.get("props", {}), out, max(80, frames)):
            man[sid] = {"path": (Path("assets/gfx") / out.name).as_posix().replace("/", "\\"), "query": f"gfx {a['component']}", "kind": "video", "source": "gfx-india"}
            placed += 1; print(f"    ✓ {sid} {a['component']} ({placed})", flush=True)
        else:
            fail += 1

    (PROJECT / "assets" / "images" / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: графики {placed}, ошибок {fail} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
