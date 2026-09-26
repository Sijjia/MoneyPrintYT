"""Достоверные картинки named-сущностей через Wikipedia-СТАТЬИ (даёт правильную иконичную картинку,
включая fair-use мемы: This Man, Momo, Backrooms). LLM → название статьи → лучшая картинка страницы →
vision-гейт → DocuFrame. Где картинки нет — сцена остаётся как есть (не трогаем).
  GFX_SCENES=scene_018,scene_029,... ../webik-pipeline/.venv/Scripts/python.exe tests/reddit_web_media.py
Без GFX_SCENES — LLM сам находит все named-сцены по всему сценарию."""
import json, os, shutil, subprocess, sys, time, urllib.request, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from tests.reddit_real_media import vision_relevant, slot_dur

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
REMOTION = ROOT / "remotion"
PUBREAL = REMOTION / "public" / "real"; PUBREAL.mkdir(parents=True, exist_ok=True)
PHOTOS = PROJECT / "assets" / "real_photos"; PHOTOS.mkdir(parents=True, exist_ok=True)
GFX = PROJECT / "assets" / "gfx"
MANIFEST = PROJECT / "assets" / "images" / "manifest.json"
FPS = 30
UA = {"User-Agent": "webik-research/1.0 (documentary)"}
WIKI = "https://en.wikipedia.org/w/api.php?"
BAD_FILE = ("logo", "icon", "commons-logo", "wiktionary", "wikiquote", "ambox", "question_book",
            "edit-clear", "wikimedia", "disambig", "padlock", "symbol", "flag_of", "map_of")

SYS = ("Ты — строгий архивный редактор документалки про Reddit. Верни Wikipedia-статью ТОЛЬКО если в закадре "
       "НАЗВАНА КОНКРЕТНАЯ сущность, которую ЗРИТЕЛЬ ЗАХОЧЕТ УВИДЕТЬ как реальное фото: (1) реальный человек "
       "по ИМЕНИ (напр. Нельсон Мандела, Фиона Брум, Кэйсукэ Айсо, Коул Спраус); (2) КОНКРЕТНЫЙ иконичный "
       "образ/мем/арт (This Man, Momo, Backrooms, Чумной доктор 11B-X-1371, Cicada 3301, обложки Berenstain); "
       "(3) КОНКРЕТНОЕ место/здание/событие (Белый дом, Бостонский марафон); (4) конкретная организация/газета "
       "с узнаваемым логотипом, ЕСЛИ она прямо в фокусе сцены. СТРОГО SKIP если: сцена про 'Reddit'/'интернет'/"
       "'сабреддит' вообще, про абстракцию/эмоцию/пересказ, про ВЫМЫШЛЕННУЮ историю (nosleep/крипипаста без "
       "конкретного реального образа). Лучше SKIP, чем натянуть. Один общий 'Reddit' — это SKIP.")
RULE = ('Верни ТОЛЬКО JSON [{"id","wiki","title","kicker"}]. wiki — точное название en.wikipedia-статьи '
        'КОНКРЕТНОЙ названной сущности, ИЛИ "SKIP". НЕ возвращай "Reddit"/"Internet"/"Subreddit"/"4chan" как '
        'ответ для обычных сцен — только если сцена ПРЯМО про сам этот сайт как объект. Ничего не выдумывай.')


def _get(params):
    url = WIKI + urllib.parse.urlencode(params)
    for _ in range(4):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=25).read())
        except urllib.error.HTTPError as e:
            if e.code == 429: time.sleep(3); continue
            return {}
        except Exception:
            time.sleep(1)
    return {}


def article_images(title):
    """URL-кандидаты картинок статьи: сначала pageimage (свободная), потом все файлы страницы."""
    urls = []
    r = _get({"action": "query", "titles": title, "prop": "pageimages", "format": "json",
              "pithumbsize": "1200", "redirects": "1"})
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        t = p.get("thumbnail", {}).get("source")
        if t: urls.append(t.split("?")[0])
    time.sleep(0.6)
    r = _get({"action": "query", "titles": title, "prop": "images", "format": "json",
              "imlimit": "30", "redirects": "1"})
    files = []
    for p in (r.get("query", {}).get("pages", {}) or {}).values():
        for im in p.get("images", []):
            ft = im["title"]
            low = ft.lower()
            if any(low.endswith(e) for e in (".jpg", ".jpeg", ".png")) and not any(b in low for b in BAD_FILE):
                files.append(ft)
    for ft in files[:6]:
        time.sleep(0.5)
        r = _get({"action": "query", "titles": ft, "prop": "imageinfo", "iiprop": "url",
                  "iiurlwidth": "1100", "format": "json"})
        for p in (r.get("query", {}).get("pages", {}) or {}).values():
            ii = p.get("imageinfo", [])
            if ii:
                u = (ii[0].get("thumburl") or ii[0].get("url") or "").split("?")[0]
                if u: urls.append(u)
    # уникализируем, сохраняя порядок
    seen, out = set(), []
    for u in urls:
        if u not in seen: seen.add(u); out.append(u)
    return out


def render_docu(sid, kicker, title, frames, kb):
    props = {"imgSrc": f"real/{sid}.jpg", "kicker": kicker, "title": title,
             "source": "Wikipedia", "kenburns": kb, "durationInFrames": frames}
    pf = REMOTION / f"_docu_{sid}.json"; pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    out = GFX / f"{sid}_gfx.mp4"
    subprocess.run(f'npx remotion render DocuFrame "{os.path.relpath(out,REMOTION).replace(os.sep,"/")}" '
                   f'--props="{os.path.relpath(pf,REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                   cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return out if (out.exists() and out.stat().st_size > 20000) else None


def main() -> int:
    scenes = {s["id"]: s for s in json.loads((PROJECT/"scenes.json").read_text(encoding="utf-8"))["scenes"]}
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assigns = json.loads((PROJECT/"_gfx_assigns.json").read_text(encoding="utf-8"))
    CARD = {"level_card", "topic_card"}
    env = [x.strip() for x in os.environ.get("GFX_SCENES", "").split(",") if x.strip()]
    # не трогаем хорошую bespoke Reddit-графику — только футаж/глитч/docuframe
    KEEP = {"RedditThread", "HexCipher", "ARGSignal", "LiminalSpace", "EvidenceFrame"}
    GENERIC = {"reddit", "internet", "subreddit", "4chan", "social media", "website"}
    if env:
        targets = [t for t in env if t in scenes]
    else:
        targets = [s["id"] for s in scenes.values() if (s.get("visual") or {}).get("type") not in CARD
                   and assigns.get(s["id"], {}).get("component") not in KEEP]
    print(f"кандидатов: {len(targets)}", flush=True)

    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    meta = {}
    B = 22
    for i in range(0, len(targets), B):
        chunk = targets[i:i+B]
        lines = [f'{{"id":"{s}","vo":"{(scenes[s].get("voiceover") or "").replace(chr(34)," ")[:200]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULE + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=3500, temperature=0.2, system=SYS)
            if isinstance(res, dict): res = res.get("items") or []
            for r in res:
                w = (r.get("wiki") or "").strip()
                if r.get("id") and w and w != "SKIP" and w.lower() not in GENERIC:
                    meta[r["id"]] = r
        except Exception as e:
            print(f"  LLM батч упал: {str(e)[:60]}")
    print(f"named-сцен с Wikipedia-статьёй: {len(meta)}", flush=True)

    dur = slot_dur()
    ok = miss = 0
    for k, (sid, m) in enumerate(sorted(meta.items())):
        wiki = m["wiki"]; title = (m.get("title") or "").strip(); kicker = (m.get("kicker") or "АРХИВ").strip()[:14]
        vo = scenes[sid].get("voiceover", "")
        photo = PHOTOS / f"{sid}.jpg"
        chosen = None
        for u in article_images(wiki):
            try:
                photo.write_bytes(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=30).read())
            except Exception:
                continue
            if photo.stat().st_size < 8000:
                continue
            if vision_relevant(photo, vo, f"{wiki} — {title}"):
                chosen = u; break
        if not chosen:
            miss += 1; print(f"  · {sid} [{wiki}] — подходящей картинки нет", flush=True); continue
        shutil.copy2(photo, PUBREAL / f"{sid}.jpg")
        frames = max(60, int(round(dur.get(sid, 4.0) * FPS)) + 15)
        out = render_docu(sid, kicker, title or wiki, frames, ["in", "out", "left", "right"][k % 4])
        if out:
            man[sid] = {"path": str(out), "query": f"web: {wiki}", "kind": "video", "source": "docuframe"}
            assigns[sid] = {"id": sid, "component": "DocuFrame", "props": {"title": title}}
            ok += 1; print(f"  ✓ {sid} «{title}» ({wiki})", flush=True)
        else:
            miss += 1
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    (PROJECT/"_gfx_assigns.json").write_text(json.dumps(assigns, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: DocuFrame(web) {ok}, без картинки {miss} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
