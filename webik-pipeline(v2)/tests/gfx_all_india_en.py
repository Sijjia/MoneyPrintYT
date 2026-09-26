"""EN bespoke-графика «Iceberg of India» (Debik): LLM-арт-директор на АНГЛ читает EN scenes.json,
подбирает ОДИН из 12 компонентов по теме (props на английском, факты из vo), рендерит под EN-слот,
ES-overwrite на живой EN V3 в EN-тайминге. Скипает сцены портретов/enum/karni (их кладём отдельно).
  ../webik-pipeline/.venv/Scripts/python.exe tests/gfx_all_india_en.py
Env: GFX_CAP (деф 2), GFX_ONLY."""
import json, os, subprocess, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany_EN"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
FPS = 30
CARD = {"level_card", "topic_card"}
EXCLUDE = {"scene_019", "scene_023", "scene_166", "scene_169", "scene_184", "scene_239",  # портреты
           "scene_048", "scene_077"}  # enum / karni — кладём отдельно

SYSTEM = ("You are the art director of a documentary about the mystical and dark side of India. For a scene "
          "pick ONE bespoke graphic component ONLY if it EXACTLY matches the scene topic, otherwise component=SKIP. "
          "Fill props with facts ONLY from the scene text (vo): numbers/sums/names/years strictly from vo, invent nothing. "
          "All on-screen text props must be ENGLISH. Components are narrow-topic — never place off-topic.")

RULES = """Components (place STRICTLY on-topic, else SKIP; facts only from vo; ALL text ENGLISH):
- "GangesGhats": ONLY Varanasi / cremation ghats / the Ganges city of death.
  props: {kicker:"VARANASI", title: SHORT ALLCAPS headline, caption: one phrase from vo}.
- "NagaUnderworld": ONLY Patala / Naga serpent-people / Hindu underworld cosmology.
  props: {kicker:"PATALA", title: ALLCAPS, caption}.
- "SkeletonLake": ONLY Roopkund / Skeleton Lake / the DNA mystery / hail. props:
  {kicker:"ROOPKUND", title: ALLCAPS, eras?: [{label:"1st c. CE",note:"..."},{label:"9th c.",note:"..."},{label:"19th c.",note:"..."}] (only if vo mentions 3 eras), caption}.
- "FortCurse": ONLY Bhangarh Fort OR Kuldhara village / cursed abandoned place / entry ban.
  props: {kicker:"BHANGARH FORT"|"KULDHARA", title: ALLCAPS, sign?: ban text (if ASI sign in vo), caption}.
- "VaultDoorB": ONLY Padmanabhaswamy Temple / the sealed Vault B / temple treasure. props:
  {kicker:"PADMANABHASWAMY", title: ALLCAPS, valueText?:"$22,000,000,000" (if a sum in vo), doorLabel?:"VAULT B — SEALED", caption}.
- "ThugStrangler": ONLY Thugs / the Thuggee stranglers of Kali / strangling travelers. props:
  {kicker:"THUGGEE", title: ALLCAPS, victims?: number of victims (from vo, e.g. 50000), victimLabel?:"victims over centuries", era?:"13th-19th c.", caption}.
- "KumbhaMela": ONLY Kumbh Mela / largest gathering of pilgrims / millions at the river. props:
  {kicker:"KUMBH MELA", title: ALLCAPS, countText: pilgrim number from vo (e.g. "120,000,000"), countLabel, caption}.
- "RatTemple": ONLY Karni Mata temple / sacred rats. props:
  {kicker:"KARNI MATA TEMPLE", title: ALLCAPS, countText: rat number from vo (e.g. "25,000"), countLabel, caption}.
- "TwinVillage": ONLY Kodinhi / twins / genetic anomaly. props:
  {kicker:"KODINHI", title: ALLCAPS, countText: pairs from vo (e.g. "400"), countLabel, multiplier: (e.g. "×6 the norm"), caption}.
- "BirdFall": ONLY Jatinga / falling birds. props: {kicker:"JATINGA", title: ALLCAPS, strip: strip dimensions if in vo, caption}.
- "GuruDossier": ONLY criminal gurus / a convicted holy fraud (Asaram, Ram Rahim). props:
  {kicker:"CRIMINAL GURUS", name: name/label ALLCAPS, followers: follower count from vo, verdict: sentence from vo (e.g. "LIFE IMPRISONMENT"|"20 YEARS"), charge: the charge, caption}.
- "SentinelIsland": ONLY North Sentinel / the forbidden island / uncontacted tribe. props:
  {kicker:"NORTH SENTINEL", title: ALLCAPS, bufferText: (e.g. "exclusion zone · 5 km buffer"), caption}.
- "SKIP": everything else.
Return ONLY a JSON array: [{"id","component","props"}]. props valid per component. Numbers as numbers/strings as shown."""

VALID = {"GangesGhats", "NagaUnderworld", "SkeletonLake", "FortCurse", "VaultDoorB", "ThugStrangler",
         "KumbhaMela", "RatTemple", "TwinVillage", "BirdFall", "GuruDossier", "SentinelIsland"}


def es(js): return pymiere.core.eval_script(js)


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
    pf = REMOTION / f"_ge_{out.stem}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    ok = out.exists() and out.stat().st_size > 20000
    if not ok: print(f"    render {comp} FAIL: {(r.stderr or r.stdout)[-160:]}")
    return ok


def place(tag, path, st, slot):
    # нормализация под слот + фейды
    norm = GFX / f"{tag}_n.mp4"
    vf = f"scale=1920:1080,setsar=1,fps=30,fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,slot-0.4):.2f}:d=0.4"
    subprocess.run(["ffmpeg","-y","-i",str(path),"-t",f"{slot:.3f}","-an","-vf",vf,"-r","30","-c:v","libx264","-crf","19","-pix_fmt","yuv420p",str(norm)], capture_output=True)
    p = str(norm.resolve()).replace("\\","/")
    js = ('(function(){var proj=app.project;'
          f'proj.importFiles(["{p}"], true, proj.rootItem, false);var root=proj.rootItem,item=null;'
          f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{tag}_n")>=0){{item=root.children[i];break;}}}}'
          f'if(!item)return "NOITEM";var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
    return es(js)


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]

    cand = [sid for sid, s in scenes.items()
            if (s.get("visual") or {}).get("type") not in CARD and sid not in EXCLUDE]
    only = [x.strip() for x in os.environ.get("GFX_ONLY", "").split(",") if x.strip()]
    if only: cand = [s for s in only if s in scenes]
    print(f"кандидатов: {len(cand)}", flush=True)

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    assigns = {}; B = 24
    for i in range(0, len(cand), B):
        chunk = cand[i:i + B]
        lines = [f'{{"id":"{s}","topic":"{id2t.get(scenes[s].get("topic_id"),"")}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:220]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nSCENES:\n" + "\n".join(lines), max_tokens=5000, temperature=0.3, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("assignments") or []
            for r in res:
                if r.get("id") and r.get("component") in VALID: assigns[r["id"]] = r
        except Exception as e:
            print(f"  батч упал: {str(e)[:70]}")
        print(f"  {min(i+B,len(cand))}/{len(cand)}", flush=True)

    cap = int(os.environ.get("GFX_CAP", "2"))
    order = [s for s in cand if s in assigns]
    per = collections.Counter(); keep = {}
    for sid in order:
        comp = assigns[sid]["component"]
        if per[comp] < cap: keep[sid] = assigns[sid]; per[comp] += 1
    print(f"\nназначено (cap={cap}): {dict(collections.Counter(a['component'] for a in keep.values()))}", flush=True)
    (PROJECT / "_gfx_assigns.json").write_text(json.dumps(keep, ensure_ascii=False, indent=1), encoding="utf-8")

    dur = slot_durations()
    placed = fail = 0
    for sid, a in sorted(keep.items(), key=lambda kv: al.get(kv[0], {}).get("start", 0)):
        if sid not in al: continue
        st = al[sid]["start"]; slot = dur.get(sid, 4.0)
        frames = int(round(slot * FPS)) + 15
        out = GFX / f"{sid}_engfx.mp4"
        if not render(a["component"], a.get("props", {}), out, max(80, frames)):
            fail += 1; continue
        r = place(f"{sid}_engfx", out, st, slot)
        if r == "OK":
            placed += 1; print(f"  ✓ {sid} {a['component']} @{int(st)//60:02d}:{int(st)%60:02d} ({placed})", flush=True)
        else:
            fail += 1; print(f"  ✗ {sid} place={r}", flush=True)
    es('app.project.save();')
    print(f"\nГОТОВО: EN-графики {placed}, ошибок {fail}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
