"""ДОБАВИТЬ 6 НОВЫХ bespoke-компонентов на ЖИВОЙ таймлайн (ES-overwrite на V3, БЕЗ пересборки —
иначе сотрутся маскот/приколы/музыка). LLM назначает компонент по теме сцены + пропсы из vo,
рендер, нормализация под длину клипа, overwrite на V3. Premiere открыт.
  ../webik-pipeline/.venv/Scripts/python.exe tests/gfx_place_new_india.py"""
import json, os, subprocess, sys, collections
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"; GFX.mkdir(parents=True, exist_ok=True)
FPS = 30
V3 = 2
CARD = {"level_card", "topic_card"}

SYSTEM = ("Ты — арт-директор документалки про мистическую Индию. Выбираешь ОДИН bespoke-компонент ТОЛЬКО "
          "если он ТОЧНО по теме сцены, иначе SKIP. Пропсы — фактами из vo (числа/имена строго из vo).")
RULES = """Компоненты (СТРОГО по теме, иначе SKIP; факты только из vo):
- "KumbhaMela": ТОЛЬКО про Кумбха-мелу / крупнейшее собрание паломников / миллионы у реки. props:
  {kicker:"КУМБХА-МЕЛА", title: КАПСОМ, countText: число паломников из vo (напр "120 000 000"), countLabel, caption}.
- "RatTemple": ТОЛЬКО про храм Карни Мата / священных крыс. props:
  {kicker:"ХРАМ КАРНИ МАТА", title: КАПСОМ, countText: число крыс из vo (напр "25 000"), countLabel, caption}.
- "TwinVillage": ТОЛЬКО про деревню Кодинхи / близнецов / генетическую аномалию. props:
  {kicker:"КОДИНХИ", title: КАПСОМ, countText: число пар из vo (напр "400"), countLabel, multiplier: (напр "×6 нормы"), caption}.
- "BirdFall": ТОЛЬКО про Джатингу / падающих птиц. props: {kicker:"ДЖАТИНГА", title: КАПСОМ, strip: размеры полосы если в vo, caption}.
- "GuruDossier": ТОЛЬКО про гуру-преступников / приговор святому-мошеннику (Асарам, Рам Рахим). props:
  {kicker:"ГУРУ-ПРЕСТУПНИКИ", name: имя/подпись КАПСОМ, followers: число последователей из vo, verdict: приговор из vo (напр "ПОЖИЗНЕННОЕ ЗАКЛЮЧЕНИЕ"|"20 ЛЕТ"), charge: обвинение, caption}.
- "SentinelIsland": ТОЛЬКО про Северный Сентинел / запретный остров / неконтактное племя. props:
  {kicker:"СЕВЕРНЫЙ СЕНТИНЕЛ", title: КАПСОМ, bufferText: (напр "запретная зона · 5 км буфер"), caption}.
- "SKIP": всё остальное.
Верни ТОЛЬКО JSON-массив [{"id","component","props"}]. Числа — числами/строками как в примерах."""
VALID = {"KumbhaMela", "RatTemple", "TwinVillage", "BirdFall", "GuruDossier", "SentinelIsland"}


def es(js): return pymiere.core.eval_script(js)


def render(comp, props, out, frames):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_gn_{out.stem}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out.exists() and out.stat().st_size > 20000


def bounds(sid):
    r = es('(function(){var t=app.project.activeSequence.videoTracks[2];for(var i=0;i<t.clips.numItems;i++){var c=t.clips[i];'
           f'if(c.name.indexOf("{sid}")>=0&&c.name.indexOf("mascot")<0)return c.start.seconds.toFixed(3)+"|"+c.end.seconds.toFixed(3);}}return "NA";}})()')
    if r == "NA" or "|" not in r: return None
    a, b = r.split("|"); return float(a), float(b)


def norm(src, dst, d):
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{d:.3f}", "-an",
                        "-vf", "scale=1920:1080,setsar=1,fps=30", "-r", "30", "-c:v", "libx264", "-crf", "20",
                        "-pix_fmt", "yuv420p", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 30000


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    outline = json.loads((PROJECT / "outline.json").read_text(encoding="utf-8"))
    id2t = {t["id"]: t["title"] for L in outline["levels"] for t in L["topics"]}
    cand = [sid for sid, s in scenes.items() if (s.get("visual") or {}).get("type") not in CARD]

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    assigns = {}; B = 24
    for i in range(0, len(cand), B):
        chunk = cand[i:i + B]
        lines = [f'{{"id":"{s}","topic":"{id2t.get(scenes[s].get("topic_id"),"")}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:220]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=4000, temperature=0.3, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or []
            for r in res:
                if r.get("id") and r.get("component") in VALID: assigns[r["id"]] = r
        except Exception as e:
            print(f"  батч упал: {str(e)[:60]}")
        print(f"  {min(i+B,len(cand))}/{len(cand)}", flush=True)

    cap = int(os.environ.get("GFX_CAP", "2"))
    per = collections.Counter(); keep = {}
    for sid in [s for s in cand if s in assigns]:
        comp = assigns[sid]["component"]
        if per[comp] < cap: keep[sid] = assigns[sid]; per[comp] += 1
    print(f"\nназначено: {dict(collections.Counter(a['component'] for a in keep.values()))}", flush=True)

    placed = 0
    for sid, a in keep.items():
        bd = bounds(sid)
        if not bd:
            print(f"  {sid}: нет клипа на V3 — пропуск"); continue
        st, en = bd; dur = en - st
        out = GFX / f"{sid}_new.mp4"
        if not render(a["component"], a.get("props", {}), out, int(round(dur * FPS)) + 12):
            print(f"  {sid}: render fail"); continue
        norм = GFX / f"{sid}_new_n.mp4"
        if not norm(out, norм, dur):
            print(f"  {sid}: norm fail"); continue
        path = str(norм.resolve()).replace("\\", "/")
        tag = f"{sid}_new_n"
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("{tag}")>=0){{item=root.children[i];break;}}}}'
              'if(!item)return "NOITEM";'
              f'var tr=proj.activeSequence.videoTracks[2];tr.overwriteClip(item,{st});return "OK";}})()')
        r = es(js)
        print(f"  {sid} {a['component']} @{int(st)//60:02d}:{int(st)%60:02d} => {r}", flush=True)
        if r == "OK": placed += 1
    es('(function(){var t=app.project.activeSequence.videoTracks[2],n=0;for(var j=t.clips.numItems-1;j>=0;j--){var c=t.clips[j];if((c.end.seconds-c.start.seconds)<0.15){c.remove(false,false);n++;}}app.project.save();return "tiny="+n;})()')
    print(f"\nГОТОВО: новых график уложено {placed}/{len(keep)} на V3, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
