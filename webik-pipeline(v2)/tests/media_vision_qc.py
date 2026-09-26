"""VISION-QC медиа: вытаскивает кадр из КАЖДОГО медиа сцены и показывает его LLM вместе с закадром —
ловит несоответствия (мусор/ватермарка/тайтл-слейт/не та сцена/абстрактный сток/не по теме).
Пишет _media_qc.json {id, ok, issue, reason, better_query}. Универсально (PROJECT в env/арг)."""
import base64, json, os, subprocess, sys, tempfile, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image

PROJECT = Path(os.environ.get("QC_PROJECT",
    ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"))
CARD = {"level_card", "topic_card"}
MODEL = os.environ.get("QC_MODEL", "google/gemini-2.5-flash")
BATCH = 8
TMP = Path(tempfile.mkdtemp())


def api_key():
    for line in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        if line.startswith("OPENROUTER_API_KEY="):
            return line.split("=", 1)[1].strip()
    raise RuntimeError("нет OPENROUTER_API_KEY")


def frame_of(sid, man) -> Path | None:
    """кадр 512px из медиа сцены (видео → середина, картинка → сама)."""
    m = man.get(sid, {})
    p = Path(m.get("path", ""))
    if not p.exists():                      # путь в манифесте относителен проекту
        alt = PROJECT / m.get("path", "")
        if alt.exists():
            p = alt
        else:
            return None
    out = TMP / f"{sid}.jpg"
    if m.get("kind") == "video" or p.suffix.lower() == ".mp4":
        dur = 0.0
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                           capture_output=True, text=True)
        try: dur = float(r.stdout.strip())
        except: dur = 2.0
        subprocess.run(["ffmpeg", "-y", "-ss", f"{max(0.3, dur*0.5):.2f}", "-i", str(p), "-frames:v", "1",
                        "-vf", "scale=512:-1", str(out)], capture_output=True)
    else:
        try:
            im = Image.open(p).convert("RGB"); im.thumbnail((512, 512)); im.save(out, quality=85)
        except Exception:
            return None
    return out if out.exists() and out.stat().st_size > 2000 else None


def data_url(p: Path):
    return "data:image/jpeg;base64," + base64.b64encode(p.read_bytes()).decode()


def vision_call(batch):
    theme = os.environ.get("QC_THEME", "документального айсберг-ролика")
    content = [{"type": "text", "text": (
        f"Ты — редактор {theme}. "
        "Для каждой сцены дан ЗАКАДР (vo) и КАДР её текущего медиа (в порядке ниже). Оцени, подходит ли "
        "медиа к смыслу закадра. Плохо = мусор/логотип стока/ватермарка (MovieClips, Filmora, KineMaster и т.п.)/"
        "тайтл-слейт с текстом вместо кадра/скриншот сайта или новостной статьи/не та сцена/шоу/фильм/"
        "абстрактный сток не по теме/кадр не про то, о чём речь. Хорошо = реальный кадр из нужного "
        "шоу/фильма/события или уместное тематическое фото/видео."
        + (" МЯГКО: если кадр из ПРАВИЛЬНОГО шоу/по теме — считай ХОРОШО, даже если это не тот самый "
           "точный момент (для документалки общий кадр нужного шоу подходит). Брак только: ватермарка, "
           "мусор/скриншот сайта, тайтл-слейт, СОВСЕМ другое шоу/тема." if os.environ.get("QC_LOOSE") == "1" else "")
        + "\n\nВерни ТОЛЬКО JSON-массив: "
        "{\"id\",\"ok\":true/false,\"issue\":\"ok|watermark|junk|text_slate|wrong_scene|generic_stock|off_topic\","
        "\"reason\":\"кратко\",\"better_query\":\"точный англ. поиск нужного кадра (если ok=false)\"}\n\nСЦЕНЫ:")}]
    for it in batch:
        content.append({"type": "text", "text": f'[{it["id"]}] vo: {it["vo"][:200]}'})
        content.append({"type": "image_url", "image_url": {"url": data_url(it["img"])}})
    body = {"model": MODEL, "messages": [{"role": "user", "content": content}]}
    req = urllib.request.Request("https://openrouter.ai/api/v1/chat/completions",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key()}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        txt = json.load(r)["choices"][0]["message"]["content"]
    s = txt.find("["); e = txt.rfind("]")
    return json.loads(txt[s:e+1]) if s >= 0 else []


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    items = []
    for s in scenes:
        sid = s["id"]
        if (s.get("visual") or {}).get("type") in CARD or sid not in man:
            continue
        img = frame_of(sid, man)
        if not img:
            continue
        items.append({"id": sid, "vo": (s.get("voiceover") or "").strip(), "img": img})
    print(f"кадров на проверку: {len(items)}", flush=True)

    verdicts = {}
    for i in range(0, len(items), BATCH):
        b = items[i:i + BATCH]
        try:
            for v in vision_call(b):
                if v.get("id"): verdicts[v["id"]] = v
            bad = sum(1 for v in verdicts.values() if not v.get("ok"))
            print(f"  батч {i//BATCH+1}/{(len(items)+BATCH-1)//BATCH}: проверено {len(verdicts)}, плохих {bad}", flush=True)
        except Exception as e:
            print(f"  ✗ батч {i//BATCH+1}: {str(e)[:100]}", flush=True)

    suspects = [v for v in verdicts.values() if not v.get("ok")]
    def tc(sid):
        st = al.get(sid, {}).get("start", 0); return f"{int(st//60)}:{int(st%60):02d}"
    suspects.sort(key=lambda v: al.get(v["id"], {}).get("start", 0))
    (PROJECT / "_media_qc.json").write_text(json.dumps(verdicts, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"\n=== ПОДОЗРИТЕЛЬНЫХ: {len(suspects)}/{len(verdicts)} ===")
    for v in suspects:
        print(f"  {tc(v['id'])} {v['id']} [{v.get('issue')}] {v.get('reason','')[:60]} → {v.get('better_query','')[:50]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
