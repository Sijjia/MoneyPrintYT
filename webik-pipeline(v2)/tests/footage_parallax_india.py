"""Замена СТАТИЧНЫХ крутящихся фото (parallax/wikimedia) на РЕАЛЬНЫЙ ФУТАЖ (Айдар: «не статичные
картинки, а реальные кадры Индии — люди в Ганге и т.д.»). LLM даёт англ. footage-запрос по vo,
тянем реальный YouTube (yt-dlp) → Pexels-фолбэк → loose vision-QC. Обновляем manifest (source=footage-real,
сбрасываем parallax). Пути относительные. Env: FOOT_LIMIT, FOOT_ONLY."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.llm.claude import ClaudeService
import tests.media_vision_qc as vqc
from tests.source_media_dw import fetch_movie
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
FOOT = PROJECT / "assets" / "_footage"; FOOT.mkdir(parents=True, exist_ok=True)
CACHE = PROJECT / "assets" / "_pexels_cache"; CACHE.mkdir(parents=True, exist_ok=True)
MAN = PROJECT / "assets" / "images" / "manifest.json"
px = PexelsVideosClient()

SYSTEM = ("Ты подбираешь поисковый запрос для РЕАЛЬНОГО ВИДЕО-ФУТАЖА под сцену документалки об Индии. "
          "Верни короткий АНГЛИЙСКИЙ запрос (3-7 слов) под РЕАЛЬНЫЕ кадры из Индии по смыслу закадра: "
          "конкретные, снимабельные вещи (люди, места, ритуалы, природа, толпы), НЕ абстракции. Пример: "
          "'hindu pilgrims bathing ganges varanasi', 'indian street crowd market', 'himalayan mountains snow'.")
RULES = ('Для каждой сцены дай англ. footage-запрос под реальные кадры Индии. Верни ТОЛЬКО JSON-массив '
         '[{"id","q"}]. Ничего кроме массива.')


def norm(src, dst, d=8.0):
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
          "eq=saturation=1.0:contrast=1.04,setsar=1,fps=30")
    r = subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{d:.2f}", "-an",
                        "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20", "-pix_fmt", "yuv420p", str(dst)],
                       capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def qc_one(sid, path, vo):
    shadow = {sid: {"path": str(Path(path).relative_to(PROJECT)).replace("\\", "/"), "kind": "video"}}
    img = vqc.frame_of(sid, shadow)
    if not img:
        return False
    try:
        for v in vqc.vision_call([{"id": sid, "vo": vo, "img": img}]):
            return bool(v.get("ok"))
    except Exception:
        return True  # QC недоступен — не блокируем реальный футаж
    return False


def main() -> int:
    man = json.loads(MAN.read_text(encoding="utf-8"))
    scenes = {s["id"]: s for s in json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]}
    vo = {k: (v.get("voiceover") or "").strip() for k, v in scenes.items()}

    targets = [k for k, v in man.items() if v.get("parallax") or v.get("source") in ("wikimedia", "wikipedia-person")]
    only = [x.strip() for x in os.environ.get("FOOT_ONLY", "").split(",") if x.strip()]
    if only: targets = [s for s in only if s in man]
    lim = int(os.environ.get("FOOT_LIMIT", "0"))
    if lim: targets = targets[:lim]
    print(f"статичных фото к замене на футаж: {len(targets)}", flush=True)

    # 1) LLM footage-запросы
    llm = ClaudeService(model="anthropic/claude-sonnet-4.5")
    q = {}
    B = 30
    for i in range(0, len(targets), B):
        chunk = targets[i:i + B]
        lines = [f'{{"id":"{s}","vo":"{vo.get(s,"").replace(chr(34)," ")[:180]}"}}' for s in chunk]
        try:
            res = llm.call_json(RULES + "\n\nСЦЕНЫ:\n" + "\n".join(lines), max_tokens=3000, temperature=0.3, system=SYSTEM)
            if isinstance(res, dict): res = res.get("items") or []
            for r in res:
                if r.get("id"): q[r["id"]] = (r.get("q") or "").strip()
        except Exception as e:
            print(f"  llm батч упал: {str(e)[:60]}")
        print(f"  запросы {min(i+B,len(targets))}/{len(targets)}", flush=True)

    # 2) фетч: yt-dlp реальный → pexels фолбэк → loose QC
    tmp = Path(tempfile.mkdtemp())
    done = 0
    for i, sid in enumerate(targets):
        query = q.get(sid) or (vo.get(sid, "")[:50] + " india")
        got = None; accept = False
        out = FOOT / f"{sid}.mp4"
        # 1) PEXELS первым — чистый реальный футаж без говорящих голов/влогеров
        for idx in (0, 1, 2):
            try:
                p = px.search_and_download(query, CACHE / f"foot_{sid}_{idx}.mp4", index=idx, min_duration=4)
                if p and Path(p).exists() and norm(Path(p), out):
                    if qc_one(sid, out, vo.get(sid, "")):
                        got = out; accept = True; break
                    if got is None:
                        got = out  # запас, если ничего лучше не найдём
            except Exception as e:
                print(f"    {sid} pexels err {str(e)[:40]}")
        # 2) yt-dlp фолбэк ТОЛЬКО если pexels не прошёл QC (для специфичных реальных событий)
        if not accept:
            yout = FOOT / f"{sid}_yt.mp4"
            try:
                if fetch_movie(query + " india", yout, i, tmp) and qc_one(sid, yout, vo.get(sid, "")):
                    import shutil as _sh; _sh.move(str(yout), str(out)); got = out; accept = True
            except Exception as e:
                print(f"    {sid} yt err {str(e)[:40]}")
        if got and got.exists():
            rel = (Path("assets/_footage") / f"{sid}.mp4").as_posix().replace("/", "\\")
            man[sid] = {"path": rel, "query": f"footage {query}", "kind": "video", "source": "footage-real"}
            done += 1
            if done % 8 == 0: print(f"    ...заменено {done}", flush=True)
    MAN.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\nГОТОВО: заменено на футаж {done}/{len(targets)} | манифест обновлён", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
