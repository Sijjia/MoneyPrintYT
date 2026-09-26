"""Реальные архивные фото под достоверность: LLM находит сцены, где упомянута КОНКРЕТНАЯ реальная
сущность (человек/место/событие/организация/продукт), даёт точный английский запрос в Wikimedia Commons →
качаем реальное CC/PD-фото → Ken-Burns mp4 → обновляем манифест. Абстрактное/вымышленное → SKIP.
  ../webik-pipeline/.venv/Scripts/python.exe tests/reddit_real_media.py
Env: RM_LIMIT (N сцен для теста)."""
import json, os, subprocess, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from services.stocks.wikimedia import WikimediaClient
import base64, json as _json, urllib.request as _ur


def _env_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    return ""


def vision_relevant(photo: Path, vo: str, q: str) -> bool:
    """Реальное ли и релевантное ли фото под сцену (отсекаем случайные Commons-хиты для мемов/копирайта)."""
    try:
        b = base64.b64encode(photo.read_bytes()).decode()
        body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [
            {"type": "text", "text": (f"Сцена документалки про Reddit. Закадр: «{vo[:180]}». Искали: «{q}». "
             "На фото ИМЕННО эта реальная сущность/место/человек/событие и оно уместно как иллюстрация? "
             'Ответь строго JSON: {"ok": true|false}. ok=false если это случайная/нерелевантная картинка, '
             "гравюра/рисунок вместо реального фото, логотип вместо объекта, или не та сущность.")},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b}"}}]}]}
        req = _ur.Request("https://openrouter.ai/api/v1/chat/completions",
                          data=_json.dumps(body).encode(),
                          headers={"Authorization": f"Bearer {_env_key()}", "Content-Type": "application/json"})
        r = _json.loads(_ur.urlopen(req, timeout=40).read())
        txt = r["choices"][0]["message"]["content"]
        m = txt[txt.find("{"): txt.rfind("}") + 1]
        return bool(_json.loads(m).get("ok"))
    except Exception:
        return True  # не смогли проверить — не блокируем

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
PHOTOS = PROJECT / "assets" / "real_photos"; PHOTOS.mkdir(parents=True, exist_ok=True)
OUT = PROJECT / "assets" / "archive_clips"; OUT.mkdir(parents=True, exist_ok=True)
MANIFEST = PROJECT / "assets" / "images" / "manifest.json"
FPS = 30

SYSTEM = ("Ты — архивный ресёрчер документалки про Reddit. Тебе дают сцены (id + закадр). Для сцены, где "
          "упомянута КОНКРЕТНАЯ РЕАЛЬНАЯ сущность, которую можно найти как настоящее фото в Wikimedia Commons "
          "(реальный человек по имени, конкретное место/здание, историческое событие, организация, продукт/"
          "компания, здание университета и т.п.), верни точный АНГЛИЙСКИЙ поисковый запрос Commons (имя/термин "
          "как в энциклопедии). Если сцена про абстракцию, вымысел (nosleep/крипипаста/Backrooms), эмоцию, "
          "обобщение, интерфейс или что-то НЕнаходимое реальным фото — component=SKIP.")

RULES = """Верни ТОЛЬКО JSON-массив: [{"id","q"}] где q — английский запрос Wikimedia Commons ИЛИ "SKIP".
Примеры хороших q: "Nelson Mandela prison", "Aaron Swartz", "Steve Huffman Reddit", "Alexis Ohanian",
"GameStop store", "Boston Marathon 2013", "Brown University campus", "Y Combinator", "Reddit logo".
НЕ выдумывай сущностей, бери ТОЛЬКО явно упомянутое в закадре. Вымысел/абстракцию — "SKIP"."""


def kenburns(img: Path, dur: float, out: Path) -> bool:
    frames = int((dur + 0.6) * FPS)
    vf = (f"scale=2560:1440:force_original_aspect_ratio=increase,crop=2560:1440,"
          f"zoompan=z='min(zoom+0.0004,1.12)':d={frames}:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1920x1080:fps={FPS},"
          f"eq=saturation=0.7:contrast=1.08:brightness=-0.02,noise=alls=8:allf=t,vignette=PI/5,format=yuv420p")
    r = subprocess.run(["ffmpeg", "-y", "-loop", "1", "-i", str(img), "-t", f"{dur+0.5:.2f}",
                        "-vf", vf, "-r", str(FPS), "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(out)],
                       capture_output=True, text=True)
    return r.returncode == 0 and out.exists() and out.stat().st_size > 20000


def slot_dur():
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    order = sorted([(al[s["id"]]["start"], s["id"]) for s in scenes if s["id"] in al])
    d = {}
    for i, (st, sid) in enumerate(order):
        nx = order[i+1][0] if i+1 < len(order) else st+4
        d[sid] = max(1.5, nx-st)
    return d


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    qc = json.loads((PROJECT / "_media_qc.json").read_text(encoding="utf-8"))
    qc = qc if isinstance(qc, dict) else {v["id"]: v for v in qc}
    CARD = {"level_card", "topic_card"}
    # кандидаты: НЕ карточки, НЕ уже-графика (gfx), приоритет — слабым по QC
    cand = [s for s in scenes if (s.get("visual") or {}).get("type") not in CARD
            and "gfx" not in (man.get(s["id"], {}).get("source") or "")]
    lim = int(os.environ.get("RM_LIMIT", "0"))
    if lim: cand = cand[:lim]
    print(f"кандидатов на реальное фото: {len(cand)}", flush=True)

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    jobs = {}
    B = 25
    for i in range(0, len(cand), B):
        chunk = cand[i:i+B]
        lines = [f'{{"id":"{s["id"]}","vo":"{(s.get("voiceover") or "").replace(chr(34)," ")[:200]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=3000, temperature=0.2, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("results") or []
            for r in res:
                if r.get("id") and r.get("q") and r["q"] != "SKIP":
                    jobs[r["id"]] = r["q"]
        except Exception as e:
            print(f"  LLM батч упал: {str(e)[:60]}")
        print(f"  {min(i+B,len(cand))}/{len(cand)}", flush=True)

    print(f"\nсцен с реальной сущностью: {len(jobs)}", flush=True)
    wm = WikimediaClient()
    dur = slot_dur()
    placed = fail = 0
    for sid, q in jobs.items():
        try:
            imgs = wm.search_images(q, limit=6, min_width=800)
        except Exception as e:
            print(f"  {sid} [{q}] поиск упал: {str(e)[:50]}"); fail += 1; continue
        if not imgs:
            print(f"  {sid} [{q}] — Commons пусто"); fail += 1; continue
        # выбрать наиболее релевантное: макс. пересечение слов запроса с названием файла,
        # штраф за «memorial/statue/plaque/logo» когда ищем человека
        qwords = {w.lower() for w in q.split() if len(w) > 2}
        def score(im):
            t = (im.get("title") or "").lower()
            s = sum(1 for w in qwords if w in t)
            if any(b in t for b in ("memorial", "statue", "plaque", "grave", "stamp", "mural")): s -= 2
            return s
        best = max(imgs, key=score)
        url = best.get("thumburl") or best.get("url")
        photo = PHOTOS / f"{sid}.jpg"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "webik-research/1.0"})
            photo.write_bytes(urllib.request.urlopen(req, timeout=30).read())
        except Exception as e:
            print(f"  {sid} [{q}] качать упал: {str(e)[:50]}"); fail += 1; continue
        vo = next((s.get("voiceover", "") for s in scenes if s["id"] == sid), "")
        if not vision_relevant(photo, vo, q):
            print(f"  {sid} [{q}] ✗ vision: нерелевантно — пропуск (оставляю прежнее)"); fail += 1; continue
        out = OUT / f"{sid}_real.mp4"
        if kenburns(photo, dur.get(sid, 4.0), out):
            man[sid] = {"path": str(out), "query": f"real: {q}", "kind": "video", "source": "wikimedia-real"}
            placed += 1
            if placed % 8 == 0: print(f"    ...реальных {placed}", flush=True)
        else:
            fail += 1
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (PROJECT / "_real_media.json").write_text(json.dumps(jobs, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: реальных фото {placed}, не нашлось {fail} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
