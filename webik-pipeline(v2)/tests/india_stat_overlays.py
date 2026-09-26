"""«Цифры ПОВЕРХ медиа»: LLM находит сцены с конкретным числом/годом/статой, рендерит ПРОЗРАЧНЫЙ
StatPop (ProRes 4444 alpha) и ES-накладывает на V7 над футажом (тело V3 не трогаем). Разнообразие
с маскот+цифрой. Premiere открыт. Env: STAT_LIMIT, STAT_CAP."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
from services.llm.claude import ClaudeService

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
REMOTION = ROOT / "remotion"
OUT = PROJECT / "assets" / "stat_overlays"; OUT.mkdir(parents=True, exist_ok=True)
FPS = 30
CARD = {"level_card", "topic_card"}

# сцены, где уже ЕСТЬ число-графика/маскот — не дублируем цифры
def busy_scenes():
    b = set()
    ga = PROJECT / "_gfx_assigns.json"
    if ga.exists():
        b |= set(json.loads(ga.read_text(encoding="utf-8")).keys())
    for p in (PROJECT / "assets" / "gfx").glob("*_new*.mp4"):
        b.add(p.name.split("_new")[0])
    for p in (PROJECT / "assets" / "gfx").glob("mascot_*.mp4"):
        b.add(p.name.replace("mascot_", "").replace(".mp4", ""))
    return b

SYSTEM = ("Ты находишь сцены документалки про Индию, где в закадре звучит КОНКРЕТНОЕ ВПЕЧАТЛЯЮЩЕЕ ЧИСЛО/ГОД/"
          "СТАТИСТИКА, которое круто показать БОЛЬШОЙ анимированной цифрой поверх кадра. Только яркие числа "
          "(годы, суммы, количества, проценты), не мелочь. Значение бери СТРОГО из vo.")
RULES = ('Верни ТОЛЬКО JSON-массив [{"id","value","label","suffix"}]: value — число как цифры (напр "1632" '
         'для года, "22000000000" для суммы, "500" для лет), label — КОРОТКАЯ подпись КАПСОМ (2-4 слова), '
         'suffix — опц. ("₽","%","млрд","лет","года" — если уместно; иначе ""). Только реально впечатляющие '
         'числа, максимум 1 на сцену. Если в сцене нет яркого числа — не включай её.')


def es(js): return pymiere.core.eval_script(js)


def bounds(sid):
    r = es('(function(){var t=app.project.activeSequence.videoTracks[2];for(var i=0;i<t.clips.numItems;i++){var c=t.clips[i];'
           f'if(c.name.indexOf("{sid}")>=0)return c.start.seconds.toFixed(3)+"|"+c.end.seconds.toFixed(3);}}return "NA";}})()')
    if "|" not in r: return None
    a, b = r.split("|"); return float(a), float(b)


def render_alpha(props, out, frames):
    props = dict(props); props["durationInFrames"] = frames
    pf = REMOTION / f"_st_{out.stem}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render StatPop "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=prores --prores-profile=4444 '
                       f'--pixel-format=yuva444p10le --image-format=png --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    ok = out.exists() and out.stat().st_size > 20000
    if not ok: print(f"    render fail: {(r.stderr or r.stdout)[-160:]}")
    return ok


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    busy = busy_scenes()
    cand = [sid for sid, s in scenes.items() if (s.get("visual") or {}).get("type") not in CARD and sid not in busy]
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    assigns = {}; B = 26
    for i in range(0, len(cand), B):
        chunk = cand[i:i + B]
        lines = [f'{{"id":"{s}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:200]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=3500, temperature=0.2, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or []
            for r in res:
                if r.get("id") and r.get("value"): assigns[r["id"]] = r
        except Exception as e:
            print(f"  батч упал: {str(e)[:60]}")
        print(f"  {min(i+B,len(cand))}/{len(cand)}", flush=True)

    cap = int(os.environ.get("STAT_CAP", "14"))
    picks = list(assigns.items())[:cap]
    lim = int(os.environ.get("STAT_LIMIT", "0"))
    if lim: picks = picks[:lim]
    print(f"\nчисел-оверлеев к постановке: {len(picks)}", flush=True)

    placed = 0
    for sid, a in picks:
        bd = bounds(sid)
        if not bd:
            print(f"  {sid}: нет клипа на V3 — пропуск"); continue
        st, en = bd; dur = min(en - st, 5.5)
        mov = OUT / f"stat_{sid}.mov"
        props = {"value": str(a["value"]), "label": a.get("label", ""), "suffix": a.get("suffix", ""), "accent": "#d24a2a"}
        if not render_alpha(props, mov, int(round(dur * FPS)) + 8):
            continue
        path = str(mov.resolve()).replace("\\", "/")
        js = ('(function(){var proj=app.project;'
              f'proj.importFiles(["{path}"], true, proj.rootItem, false);'
              'var root=proj.rootItem,item=null;'
              f'for(var i=root.children.numItems-1;i>=0;i--){{if(root.children[i].name.indexOf("stat_{sid}")>=0){{item=root.children[i];break;}}}}'
              'if(!item)return "NOITEM";'
              f'var tr=proj.activeSequence.videoTracks[6];tr.overwriteClip(item,{st});return "OK";}})()')
        r = es(js)
        print(f"  {sid} «{a['value']} {a.get('label','')[:22]}» @{int(st)//60:02d}:{int(st)%60:02d} => {r}", flush=True)
        if r == "OK": placed += 1
    es('app.project.save();')
    print(f"\nГОТОВО: цифр-оверлеев поверх медиа {placed}/{len(picks)}, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
