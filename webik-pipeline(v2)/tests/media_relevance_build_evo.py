"""ФАЗА 1 (без Premiere): пересборка релевантного медиа для «Айсберг эволюции».
LLM проходит по сценам со СТОК-видео (pexels/youtube) → для КОНКРЕТНЫХ сцен даёт
режим (montage/single/keep) + англ. запросы + подпись. Тянем реальные фото
(Wikimedia, дедуп), рендерим PhotoMontage (2-4) или PhotoZoom (1) ровно в слот.
Пишем swap_plan.json {sid: path}. Свап — media_relevance_swap_evo.py.
Резюмируемо: готовые клипы пропускаются."""
import hashlib, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
from services.stocks.wikimedia import WikimediaClient
from services.stocks.wikipedia_photo import WikipediaPhotoClient

PROJECT = ROOT / "projects" / "2026-08-18_aysberg-evolyutsii-temnaya-i-zapretnaya-storona-evolyutsii-o"
PUB = ROOT / "remotion" / "public" / "photos"
OUT = PROJECT / "assets" / "relmedia"
REMOTION = ROOT / "remotion"
PLAN = PROJECT / "swap_plan.json"
CAND_SRC = {"pexels-video", "youtube-auto"}
CHUNK = 36
ACCENT = "#1fa48a"
for d in (OUT, PUB):
    d.mkdir(parents=True, exist_ok=True)

SYSTEM = ("Ты — режиссёр документального видео про эволюцию. Подбираешь РЕАЛЬНОЕ медиа "
          "строго ПО СМЫСЛУ закадра. Сток-видео не по теме — зло.")
RULES = """Для КАЖДОЙ сцены реши, какое РЕАЛЬНОЕ фото нужно под её закадр. Верни JSON-массив
объектов {id, mode, n, queries, caption}:
- mode="montage" — сцена перечисляет/охватывает НЕСКОЛЬКО объектов, или это ключевой момент,
  где 2-4 реальных фото смотрятся круче (напр. вид ископаемого: реконструкция+череп+место).
  n=2..4, queries=столько же КОНКРЕТНЫХ англ. запросов (реальные фото на Wikimedia).
- mode="single" — один явный субъект (человек/место/один объект). n=1, queries=[1 запрос].
- mode="keep" — закадр АБСТРАКТНЫЙ/атмосферный (эмоции, общие рассуждения), реальное фото не нужно —
  оставляем как есть. queries=[].
caption — короткая подпись по-русски (2-4 слова) для монтажа, иначе "".
Запросы — на английском, конкретные, находимые как РЕАЛЬНЫЕ фото (люди/виды/места/предметы/
исторические снимки/музейные реконструкции). НЕ абстракции. Пример: "Homo floresiensis skull",
"Svante Paabo geneticist", "Aktion T4 memorial Berlin", "silver fox domestication experiment".
Верни ТОЛЬКО JSON-массив."""


def md5f(p):
    try: return hashlib.md5(Path(p).read_bytes()).hexdigest()[:12]
    except Exception: return None


def render(comp, outp, props):
    pf = REMOTION / f"_rel_{outp.stem}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(outp, REMOTION)}" '
                       f'--props="{os.path.relpath(pf, REMOTION)}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    return r.returncode == 0


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    by_id = {s["id"]: s for s in scenes}
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    cand = [s for s in scenes if man.get(s["id"], {}).get("source") in CAND_SRC
            and s["id"] in al and (s.get("voiceover") or "").strip()]
    print(f"кандидатов (сток): {len(cand)}")

    plan = json.loads(PLAN.read_text(encoding="utf-8")) if PLAN.exists() else {}
    llm = ClaudeService(model="google/gemini-2.5-flash")
    wm = WikimediaClient(); wp = WikipediaPhotoClient()
    tmp = Path(tempfile.mkdtemp())
    stats = {"montage": 0, "single": 0, "keep": 0, "fail": 0}

    # 1) классификация чанками
    decisions = {}
    for i in range(0, len(cand), CHUNK):
        ch = cand[i:i + CHUNK]
        lines = [f'{{"id":"{s["id"]}","vo":"{(s.get("voiceover") or "").replace(chr(34)," ")[:200]}"}}' for s in ch]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=8000, temperature=0.3, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or res.get("scenes") or []
            for r in res:
                if r.get("id"): decisions[r["id"]] = r
        except Exception as e:
            print(f"  чанк {i//CHUNK+1} LLM упал: {str(e)[:60]}")
        print(f"  классиф. {min(i+CHUNK,len(cand))}/{len(cand)}")

    # 2) фетч + рендер
    for k, s in enumerate(cand):
        sid = s["id"]
        if sid in plan:  # уже готово
            continue
        d = decisions.get(sid)
        if not d or d.get("mode") == "keep":
            stats["keep"] += 1; continue
        a = al[sid]; dur = max(2.0, round(a["end"] - a["start"], 1)); frames = max(60, int((dur + 0.4) * 30))
        queries = [q for q in (d.get("queries") or []) if q][:4]
        if not queries:
            stats["keep"] += 1; continue
        # фетч уникальных фото
        imgs = []; seen = set()
        want = 4 if d.get("mode") == "montage" else 1
        for q in queries:
            if len(imgs) >= max(want, int(d.get("n", want) or want)): break
            o = tmp / f"{sid}_{len(imgs)}.jpg"
            try:
                if wm.search_and_download(q, o) and o.stat().st_size > 6000:
                    h = md5f(o)
                    if h and h not in seen:
                        seen.add(h)
                        pub = PUB / f"{sid}_r{len(imgs)}.jpg"; shutil.copy(o, pub)
                        imgs.append(f"photos/{sid}_r{len(imgs)}.jpg")
            except Exception:
                pass
        if not imgs:
            stats["fail"] += 1; print(f"  ✗ {sid}: фото не нашлись"); continue
        if len(imgs) >= 2 and d.get("mode") == "montage":
            outp = OUT / f"{sid}_mz.mp4"
            ok = render("PhotoMontage", outp, {"images": imgs, "caption": (d.get("caption") or "")[:40],
                                               "accent": ACCENT, "durationInFrames": frames})
            if ok: plan[sid] = str(outp); stats["montage"] += 1; print(f"  ✓M {sid} ({len(imgs)} фото)")
            else: stats["fail"] += 1
        else:
            outp = OUT / f"{sid}_rz.mp4"
            ok = render("PhotoZoom", outp, {"img": imgs[0], "dir": "in" if k % 2 else "out", "durationInFrames": frames})
            if ok: plan[sid] = str(outp); stats["single"] += 1; print(f"  ✓S {sid}")
            else: stats["fail"] += 1
        if (stats["montage"] + stats["single"]) % 10 == 0:
            PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    PLAN.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nИТОГ: montage={stats['montage']} single={stats['single']} keep={stats['keep']} fail={stats['fail']}")
    print(f"план → {PLAN} ({len(plan)} свапов)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
