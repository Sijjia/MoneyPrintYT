"""Директор bespoke-графики Roblox: для слабых (QC-забракованных) сцен LLM подбирает компонент
(AccountHijack/StolenCounter/BeamingTrade/NewsAlert/LaunderFlow/RobloxTimeline) + пропсы СТРОГО по
фактам из текста сцены (без выдумки), рендерит под длину слота и ставит базовым медиа в манифест.
  ../webik-pipeline/.venv/Scripts/python.exe tests/gfx_director_roblox.py
Env: GFX_LIMIT (для теста N сцен), GFX_ONLY_BAD=1 (только still_bad из QC; иначе все флаг-нутые)."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-05_aysberg-robloks-temnaya-skrytaya-storona-realnye-intsidenty-"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"
GFX.mkdir(parents=True, exist_ok=True)
FPS = 30
CARD = {"level_card", "topic_card"}

SYSTEM = ("Ты — арт-директор документалки про тёмную сторону Roblox. Для сцены выбираешь ОДИН bespoke-"
          "компонент графики и заполняешь его пропсы, используя ТОЛЬКО факты из текста сцены (vo). "
          "НИЧЕГО не выдумывай: цифры, суммы, имена, годы бери строго из vo; если конкретной цифры в vo "
          "нет — не ставь её. Если ни один компонент не подходит по смыслу — верни component=SKIP.")

RULES = """Компоненты и их пропсы:
- "AccountHijack": экран угона аккаунта (взлом, кража cookie, обход 2FA, фишинг). props:
  {caption: короткая RU-фраза (суть сцены), target?: ник/аккаунт, mode: "hijack"|"cookie"|"phish"}.
- "StolenCounter": КРУПНАЯ цифра (украдено/угнано/штраф/сумма). props:
  {value: ЧИСЛО (только если оно есть в vo!), prefix?: "$"|"", suffix?: " аккаунтов"|" R$"|"", label: "УГНАНО"/"УКРАДЕНО"/"ШТРАФ" и т.п., sub?: пояснение, caption: фраза}.
- "BeamingTrade": краденый предмет → реальные деньги. props:
  {itemName: название предмета (из vo, напр. "Sparkle Time Fedora","Dominus"), itemSub?: "LIMITED", price: строка "$13 605" (из vo!), caption}.
- "NewsAlert": новостная плашка (аресты/иски/расследования). props:
  {kicker: "АРЕСТ"/"СУД"/"СРОЧНО"/"РАССЛЕДОВАНИЕ", headline: заголовок КАПСОМ (из vo), outlet?: источник (BleepingComputer/Bloomberg/Forbes/Vice), location?: место, caption}.
- "LaunderFlow": схема отмыва денег через Robux. props: {caption}. (этапы стандартные)
- "RobloxTimeline": хронология истории Roblox. props: {events?: [{year,label}...] из vo, title?: "ХРОНОЛОГИЯ ROBLOX", caption}.
- "SKIP": если ничего не подходит.

Верни ТОЛЬКО JSON-массив: [{"id","component","props"}]. props — валидный объект под выбранный компонент.
Числовой value — именно число (610000), без пробелов/букв. price — строка как в vo."""


def probe(p):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                       capture_output=True, text=True)
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


VALID = {"AccountHijack", "StolenCounter", "BeamingTrade", "NewsAlert", "LaunderFlow", "RobloxTimeline"}


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    qcfix = json.loads((PROJECT / "_qcfix_result.json").read_text(encoding="utf-8"))
    bad = qcfix.get("still_bad", [])
    bad = [s for s in bad if s in scenes and (scenes[s].get("visual") or {}).get("type") not in CARD]
    lim = int(os.environ.get("GFX_LIMIT", "0"))
    if lim: bad = bad[:lim]
    print(f"слабых сцен к графике: {len(bad)}", flush=True)

    # директор (батчами)
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    assigns = {}
    B = 22
    for i in range(0, len(bad), B):
        chunk = bad[i:i + B]
        lines = [f'{{"id":"{s}","topic":"{id2t.get(scenes[s].get("topic_id"),"")}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:220]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=6000, temperature=0.3, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("assignments") or []
            for r in res:
                if r.get("id"): assigns[r["id"]] = r
        except Exception as e:
            print(f"  директор-батч упал: {str(e)[:60]}")
        print(f"  {min(i+B,len(bad))}/{len(bad)}", flush=True)

    import collections
    c = collections.Counter(a.get("component") for a in assigns.values())
    print(f"\nраспределение: {dict(c)}", flush=True)

    dur = slot_durations()
    placed = skipped = fail = 0
    for sid, a in assigns.items():
        comp = a.get("component")
        if comp not in VALID:
            skipped += 1; continue
        frames = int(round(dur.get(sid, 3.0) * FPS)) + 15   # +0.5с, чтобы pretrim просто обрезал (без slow-mo)
        out = GFX / f"{sid}_gfx.mp4"
        if render(comp, a.get("props", {}), out, max(60, frames)):
            man[sid] = {"path": str(out), "query": f"gfx {comp}", "kind": "video", "source": "gfx-roblox"}
            placed += 1
            if placed % 6 == 0: print(f"    ...отрендерено {placed}", flush=True)
        else:
            fail += 1

    (PROJECT / "assets" / "images" / "manifest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (PROJECT / "_gfx_assigns.json").write_text(json.dumps(assigns, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: графики {placed}, SKIP {skipped}, ошибок {fail} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
