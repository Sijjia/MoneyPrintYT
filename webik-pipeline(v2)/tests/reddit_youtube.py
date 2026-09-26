"""Реальные YouTube-моменты по контексту (Backrooms, двойники, r/place и т.п.): по JSON-заданию
{scene:{q, win?}} ищет ролик, качает окно, НОРМАЛИЗУЕТ (кроп летербокса → заполнение 1920x1080),
кладёт в манифест. Вставки берём из public-контента (документалка/комментарий).
  YT_JOBS=<path.json> ../webik-pipeline/.venv/Scripts/python.exe tests/reddit_youtube.py"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.stocks.youtube_search import search_candidates
from services.stocks.youtube_clipper import fetch_clip
import base64, urllib.request as _ur
from services.llm.claude import ClaudeService


def _key():
    for l in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if l.startswith("OPENROUTER_API_KEY="):
            return l.split("=", 1)[1].strip()
    return ""


def rank_candidates(cands, topic):
    """LLM упорядочивает кандидатов по релевантности теме (по названиям)."""
    if len(cands) <= 1:
        return cands
    lst = [{"i": i, "title": (c.get("title") or "")[:90], "dur": c.get("duration")} for i, c in enumerate(cands)]
    try:
        llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
        r = llm.call_json(
            f'Тема сцены документалки: «{topic}». Ниже ролики-кандидаты с YouTube. Верни ТОЛЬКО JSON '
            f'{{"order":[i,...]}} — индексы от НАИБОЛЕЕ подходящего визуала под тему к наименее. '
            f'Отбрось явные новостные выпуски, реакшены, обзоры с говорящей головой.\n' + json.dumps(lst, ensure_ascii=False),
            max_tokens=300, temperature=0.1)
        order = r.get("order") if isinstance(r, dict) else None
        if order:
            return [cands[i] for i in order if 0 <= i < len(cands)] + [c for j, c in enumerate(cands) if j not in order]
    except Exception:
        pass
    return cands


def verify_frame(mp4: Path, topic: str) -> bool:
    """Vision: кадр по теме И без крупного титра/ватермарки/новостной плашки (проверяем МНОГО кадров,
    чтобы поймать мелькающий текст/логотипы)."""
    for t in (0.6, 1.5, 2.5, 3.5, 4.5, 5.5):
        f = mp4.parent / "_vf.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", str(t), "-i", str(mp4), "-frames:v", "1", "-vf", "scale=640:-1", str(f)], capture_output=True)
        if not f.exists():
            continue
        b = base64.b64encode(f.read_bytes()).decode()
        body = {"model": "google/gemini-2.5-flash", "messages": [{"role": "user", "content": [
            {"type": "text", "text": (f"Тема: «{topic}». Этот кадр РЕЛЕВАНТЕН теме как иллюстрация И на нём НЕТ "
             "крупного наложенного титра/названия/субтитров/новостной плашки/ватермарки? "
             'Ответь JSON {"ok": true|false}. ok=false если тема не та ИЛИ есть наложенный текст/плашка.')},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b}"}}]}]}
        try:
            req = _ur.Request("https://openrouter.ai/api/v1/chat/completions", data=json.dumps(body).encode(),
                              headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"})
            r = json.loads(_ur.urlopen(req, timeout=40).read())
            txt = r["choices"][0]["message"]["content"]; m = txt[txt.find("{"): txt.rfind("}") + 1]
            if not json.loads(m).get("ok"):
                return False
        except Exception:
            return True
    return True

PROJECT = ROOT / "projects" / "2026-09-13_aysberg-reddit-strannaya-i-trevozhnaya-storona"
YT = PROJECT / "assets" / "youtube_clips"
NORM = PROJECT / "assets" / "youtube_norm"; NORM.mkdir(parents=True, exist_ok=True)
MANIFEST = PROJECT / "assets" / "images" / "manifest.json"


def slot_dur():
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    order = sorted([(al[s["id"]]["start"], s["id"]) for s in sc if s["id"] in al])
    d = {}
    for i, (st, sid) in enumerate(order):
        d[sid] = max(2.0, (order[i+1][0] if i+1 < len(order) else st+4) - st)
    return d


def normalize(src: Path, dst: Path, dur: float) -> bool:
    # заполнить 1920x1080 (убрать летербокс), лёгкий зум чтобы срезать вотермарки по краям, +фейды
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1728:972,"
          "scale=1920:1080,eq=saturation=0.95:contrast=1.04,setsar=1,fps=30,"
          f"fade=t=in:st=0:d=0.3,fade=t=out:st={max(0.3,dur-0.4):.2f}:d=0.4")
    r = subprocess.run(["ffmpeg", "-y", "-i", str(src), "-t", f"{dur+0.4:.2f}", "-an",
                        "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def main() -> int:
    jobs = json.loads(Path(os.environ["YT_JOBS"]).read_text(encoding="utf-8"))
    man = json.loads(MANIFEST.read_text(encoding="utf-8"))
    dur = slot_dur()
    ok = fail = 0
    for sid, job in jobs.items():
        q = job["q"]; win = job.get("win"); topic = job.get("topic", q)
        cands = search_candidates(q, n=8)
        good = [c for c in cands if 30 < (c.get("duration") or 0) < 900]
        good = rank_candidates(good, topic)                     # LLM-ранжирование по релевантности
        d = min(dur.get(sid, 5.0), 8.0)
        placed = False
        for c in good[:4]:                                      # пробуем топ-4, пока не пройдёт vision
            st = (win[0] if win else 25.0)
            raw = fetch_clip(c["url"], st, st + d + 0.6, PROJECT, f"{sid}_raw", q)
            if not raw:
                continue
            norm = NORM / f"{sid}.mp4"
            if not normalize(Path(raw["path"]), norm, d):
                continue
            if not verify_frame(norm, topic):                  # vision: та ли тема + нет титра
                print(f"    {sid}: «{(c.get('title') or '')[:40]}» vision-отказ, следующий", flush=True)
                continue
            man[sid] = {"path": str(norm.resolve()), "query": f"yt: {q}", "kind": "video", "source": "youtube-real"}
            ok += 1; placed = True
            print(f"  ✓ {sid} [{q}] → «{(c.get('title') or '')[:40]}»", flush=True); break
        if not placed:
            fail += 1; print(f"  {sid} [{q}] — подходящего клипа не нашлось", flush=True)
    MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО YT: {ok}, ошибок {fail} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
