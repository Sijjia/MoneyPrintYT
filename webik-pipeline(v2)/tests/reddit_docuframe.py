"""DocuFrame-графика на РЕАЛЬНЫХ фото: для списка сцен тянем настоящее фото (Wikimedia, vision-гейт),
LLM даёт короткий заголовок+кикер, рендерим кинематографичный DocuFrame → манифест. Где фото нет —
возвращаем сцену на обычный футаж (video_stock/qcfix). Premiere закрыт (только рендер+манифест).
  GFX_SCENES=scene_032,scene_034,... ../webik-pipeline/.venv/Scripts/python.exe tests/reddit_docuframe.py
Без GFX_SCENES берёт: все бывшие NewsAlert + существующие wikimedia-real (апгрейд подачи)."""
import json, os, shutil, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from services.stocks.wikimedia import WikimediaClient
from tests.reddit_real_media import vision_relevant, kenburns, slot_dur

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
REMOTION = ROOT / "remotion"
PUBREAL = REMOTION / "public" / "real"; PUBREAL.mkdir(parents=True, exist_ok=True)
PHOTOS = PROJECT / "assets" / "real_photos"; PHOTOS.mkdir(parents=True, exist_ok=True)
GFX = PROJECT / "assets" / "gfx"
MANIFEST = PROJECT / "assets" / "images" / "manifest.json"
FPS = 30

SYS = ("Ты — архивный редактор документалки про Reddit. По закадру сцены дай: en-запрос в Wikimedia Commons "
       "для РЕАЛЬНОГО фото упомянутой конкретной сущности (человек/место/событие/организация), короткий "
       "русский заголовок (2-5 слов, что на фото) и кикер (1 слово: АРХИВ/ГОД/РАЗОБЛАЧЕНО/ФАКТ или год). "
       "Если реального фото по сцене быть не может (вымысел/абстракция/мем) — q='SKIP'.")
RULE = ('Верни ТОЛЬКО JSON-массив [{"id","q","title","kicker"}]. q — en-запрос Commons или "SKIP". '
        'title — рус. подпись. kicker — короткий тег. Ничего не выдумывай, бери из закадра.')


def revert_footage(man, sid):
    for cand, src in [(PROJECT/"assets/_qcfix"/f"{sid}.mp4", "qcfix-hd"),
                      (PROJECT/"assets/video_stock"/f"{sid}.mp4", "pexels-video")]:
        if cand.exists():
            man[sid] = {"path": str(cand.resolve()), "query": "footage", "kind": "video", "source": src}
            return True
    g = list((PROJECT/"assets/parallax").glob(f"{sid}__*.mp4"))
    if g:
        man[sid] = {"path": str(g[0].resolve()), "query": "footage", "kind": "video", "source": "parallax"}
        return True
    return False


def render_docu(sid, img_public, kicker, title, source, frames, kb):
    props = {"imgSrc": img_public, "kicker": kicker, "title": title, "source": source,
             "kenburns": kb, "durationInFrames": frames}
    pf = REMOTION / f"_docu_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_gfx.mp4"
    r = subprocess.run(f'npx remotion render DocuFrame "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out if (out.exists() and out.stat().st_size > 20000) else None


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT/"scenes.json").read_text(encoding="utf-8"))["scenes"]}
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assigns = json.loads((PROJECT/"_gfx_assigns.json").read_text(encoding="utf-8"))
    env = [x.strip() for x in os.environ.get("GFX_SCENES", "").split(",") if x.strip()]
    if env:
        targets = env
    else:
        news = [sid for sid, a in assigns.items() if a.get("component") == "NewsAlert"]
        real = [sid for sid, v in man.items() if v.get("source") == "wikimedia-real"]
        targets = sorted(set(news + real))
    targets = [t for t in targets if t in scenes]
    print(f"сцен под DocuFrame: {len(targets)}", flush=True)

    # LLM: запрос+заголовок+кикер
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    meta = {}
    B = 20
    for i in range(0, len(targets), B):
        chunk = targets[i:i+B]
        lines = [f'{{"id":"{s}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:200]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULE + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=3000, temperature=0.2, system=SYS)
            if isinstance(res, dict): res = res.get("items") or []
            for r in res:
                if r.get("id"): meta[r["id"]] = r
        except Exception as e:
            print(f"  LLM батч упал: {str(e)[:60]}")
    wm = WikimediaClient()
    dur = slot_dur()
    docu = foot = 0
    prev_real = json.loads((PROJECT/"_real_media.json").read_text(encoding="utf-8")) if (PROJECT/"_real_media.json").exists() else {}
    for k, sid in enumerate(targets):
        m = meta.get(sid, {})
        q = m.get("q", "SKIP")
        title = (m.get("title") or "").strip()
        kicker = (m.get("kicker") or "АРХИВ").strip()[:14]
        photo = PHOTOS / f"{sid}.jpg"
        had_real = photo.exists()   # фото уже добыто ранее (реальная сущность подтверждена)
        vo = scenes[sid].get("voiceover", "")
        # НОВЫЕ сцены (нет фото) и LLM дал запрос — пробуем добыть
        if not had_real and q and q != "SKIP":
            try:
                imgs = wm.search_images(q, limit=6, min_width=800)
                if imgs:
                    qwords = {w.lower() for w in q.split() if len(w) > 2}
                    best = max(imgs, key=lambda im: sum(1 for w in qwords if w in (im.get("title") or "").lower())
                               - (2 if any(b in (im.get("title") or "").lower() for b in ("memorial","statue","plaque","stamp","mural")) else 0))
                    url = best.get("thumburl") or best.get("url")
                    req = urllib.request.Request(url, headers={"User-Agent": "webik-research/1.0"})
                    photo.write_bytes(urllib.request.urlopen(req, timeout=30).read())
                    if not vision_relevant(photo, vo, q):
                        photo.unlink(missing_ok=True)
            except Exception:
                pass
        # если фото есть (старое ИЛИ ново-добытое) — ВСЕГДА DocuFrame (не терять достоверное)
        if photo.exists():
            if not title:   # LLM не дал заголовок — берём из прошлого запроса
                oldq = prev_real.get(sid, "") or q if q != "SKIP" else prev_real.get(sid, "")
                title = (oldq or "Архивный кадр").replace("real: ", "")
            shutil.copy2(photo, PUBREAL / f"{sid}.jpg")
            frames = max(60, int(round(dur.get(sid, 4.0) * FPS)) + 15)
            kb = ["in", "out", "left", "right"][k % 4]
            out = render_docu(sid, f"real/{sid}.jpg", kicker, title, "Wikimedia Commons", frames, kb)
            if out:
                man[sid] = {"path": str(out), "query": f"docu: {title}", "kind": "video", "source": "docuframe"}
                assigns[sid] = {"id": sid, "component": "DocuFrame", "props": {"title": title}}
                docu += 1
                print(f"  ✓ {sid} DocuFrame «{title}»", flush=True); continue
        # реального фото нет → футаж
        if revert_footage(man, sid):
            assigns.pop(sid, None); foot += 1
            print(f"  · {sid} → футаж (реального фото нет)", flush=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (PROJECT/"_gfx_assigns.json").write_text(json.dumps(assigns, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: DocuFrame {docu}, на футаж {foot} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
