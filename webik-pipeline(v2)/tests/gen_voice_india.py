"""Голос v3 НЕПРЕРЫВНЫЙ режим для «Айсберг Индии» (клон gen_voice_reddit).
ВЕСЬ сценарий → один заказ Lumean, бесшовно + пословный alignment. Паузы тегами.
Пишет assets/voice/full.mp3, full.align.json, assets/alignment.json.
Fallback VOICE_MODE=level. Добавлен индийский пред-словарь произношения (india_pre)."""
import json, os, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.tts.lumean import LumeanTTS
from services.stt.aligner import _map_scenes_to_whisper_words
from tests.ru_pronounce_reddit import normalize as ru_norm   # латиница→кириллица и пр.

PROJECT = ROOT / "projects" / "2026-09-22_aysberg-indii-misticheskaya-i-zagadochnaya-storona-strany"
VOICE = PROJECT / "assets" / "voice"
SEGDIR = VOICE / "_segs"
TEMPLATE = "01a0e9bc-a29d-7128-84b5-355e67b11a7e"  # Webik-v4 (eleven_v4 + ru, тот же диктор M1CSR3PJ...) — Айдар: v3 в утиль

LVL_PAUSE = " {{pause=1.6}} "
TOPIC_PAUSE = " {{pause=0.5}} "
GAP = 0.4

# Индийские замены произношения ДО ru_norm (Lumean криво читает эти латинские/аббрев. токены)
_INDIA_SUBS = [
    (re.compile(r"\bNASA\b"), "НАСА"),
    (re.compile(r"«?thug»?", re.I), "«таг»"),
    (re.compile(r"хранилища\s+B\b"), "хранилища Би"),
    (re.compile(r"\bB\b"), "Би"),
    (re.compile(r"\bПО\b"), "программы"),
    (re.compile(r"\bXXI\b"), "двадцать первого"),
    (re.compile(r"\bWebik\b", re.I), "Вебик"),
    (re.compile(r"\bTelegram\b", re.I), "Телеграм"),
]


def india_norm(text: str) -> str:
    for pat, repl in _INDIA_SUBS:
        text = pat.sub(repl, text)
    return ru_norm(text)


def dur_of(p: Path) -> float:
    r = subprocess.run(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{p}"',
                       shell=True, capture_output=True, text=True)
    try:
        v = float(r.stdout.strip())
        if v > 0: return v
    except Exception:
        pass
    aj = p.with_suffix(".align.json")
    if aj.exists():
        try:
            return float(json.loads(aj.read_text(encoding="utf-8")).get("duration_seconds", 0) or 0)
        except Exception:
            pass
    return 0.0


def _piece(s, prev_sec):
    vo = (s.get("voiceover") or "").strip()
    if not vo:
        return None
    sec = s.get("section") or ""
    if sec == "level_announce":
        return vo + LVL_PAUSE
    if sec == "topic_announce" and prev_sec not in (None, "level_announce"):
        return TOPIC_PAUSE + vo
    return vo


def build_full_text(scenes):
    parts, ids, prev = [], [], None
    for s in scenes:
        p = _piece(s, prev)
        if p is None:
            continue
        parts.append(p); ids.append(s["id"]); prev = s.get("section") or ""
    return " ".join(parts), ids


def build_level_blocks(scenes):
    blocks, cur = [], {"label": "hook", "sc": []}
    for s in scenes:
        sec = s.get("section") or ""
        if sec == "level_announce":
            if cur["sc"]: blocks.append(cur)
            cur = {"label": f"level_{s.get('level')}", "sc": [s]}
        elif sec in ("outro", "cta", "conclusion"):
            if cur["label"] != "outro":
                if cur["sc"]: blocks.append(cur)
                cur = {"label": "outro", "sc": []}
            cur["sc"].append(s)
        else:
            cur["sc"].append(s)
    if cur["sc"]: blocks.append(cur)
    out = []
    for b in blocks:
        parts, ids, prev = [], [], None
        for s in b["sc"]:
            p = _piece(s, prev)
            if p is None:
                continue
            parts.append(p); ids.append(s["id"]); prev = s.get("section") or ""
        if parts:
            out.append((b["label"], " ".join(parts), ids))
    return out


def _write_alignment(scenes, words, total):
    timings = _map_scenes_to_whisper_words(scenes, words)
    (VOICE / "full.align.json").write_text(
        json.dumps({"duration_seconds": round(total, 3), "words": words}, ensure_ascii=False),
        encoding="utf-8")
    (PROJECT / "assets" / "alignment.json").write_text(
        json.dumps({"duration": round(total, 3), "method": "lumean_continuous_v3ru",
                    "words": words, "scenes": timings, "paused_at_levels": True},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    mapped = sum(1 for v in timings.values() if v.get("end", 0) > 0)
    print(f"alignment: {mapped}/{len(scenes)} сцен замаплено → assets/alignment.json")


def run_continuous(scenes, lm):
    text, ids = build_full_text(scenes)
    print(f"НЕПРЕРЫВНЫЙ режим: 1 заказ, {len(ids)} сцен, {len(text)} символов")
    full = VOICE / "full.mp3"
    lm.synthesize(india_norm(text), full, save_alignment=True)
    aj = full.with_suffix(".align.json")
    words = json.loads(aj.read_text(encoding="utf-8")).get("words", []) if aj.exists() else []
    total = dur_of(full)
    print(f"\nfull.mp3: {total:.1f}с ({total/60:.1f} мин), слов: {len(words)}")
    _write_alignment(scenes, words, total)
    return 0


def run_level(scenes, lm):
    SEGDIR.mkdir(parents=True, exist_ok=True)
    blocks = build_level_blocks(scenes)
    print(f"LEVEL режим: {len(blocks)} кусков")
    sil = SEGDIR / "_sil.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=stereo",
                    "-t", str(GAP), "-c:a", "libmp3lame", "-b:a", "192k", str(sil)], capture_output=True)
    mp3s, words, offset = [], [], 0.0
    for i, (label, text, ids) in enumerate(blocks):
        out = SEGDIR / f"seg_{i:02d}.mp3"
        if not (out.exists() and out.stat().st_size > 10000):
            try:
                lm.synthesize(india_norm(text), out, save_alignment=True)
            except Exception as e:
                print(f"  ✗ кусок {i} [{label}]: {str(e)[:80]}"); continue
        d = dur_of(out)
        aj = out.with_suffix(".align.json")
        if aj.exists():
            for x in json.loads(aj.read_text(encoding="utf-8")).get("words", []):
                words.append({"word": x.get("word"),
                              "start": round(float(x.get("start", 0)) + offset, 3),
                              "end": round(float(x.get("end", 0)) + offset, 3)})
        mp3s.append(out)
        offset += d + (GAP if i < len(blocks) - 1 else 0.0)
        print(f"  ✓ {i:02d} [{label[:18]}] {d:.1f}с → offset {offset:.1f}с ({len(ids)} сцен)")
    lst = SEGDIR / "_concat.txt"
    lines = []
    for j, m in enumerate(mp3s):
        lines.append(f"file '{m.resolve().as_posix()}'")
        if j < len(mp3s) - 1: lines.append(f"file '{sil.resolve().as_posix()}'")
    lst.write_text("\n".join(lines), encoding="utf-8")
    full = VOICE / "full.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst),
                    "-c:a", "libmp3lame", "-b:a", "192k", str(full)], capture_output=True)
    total = dur_of(full)
    print(f"\nfull.mp3: {total:.1f}с ({total/60:.1f} мин), слов: {len(words)}")
    _write_alignment(scenes, words, total)
    return 0


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    lm = LumeanTTS(template_uuid=TEMPLATE)
    mode = os.environ.get("VOICE_MODE", "continuous").lower()
    if mode == "level":
        return run_level(scenes, lm)
    try:
        return run_continuous(scenes, lm)
    except Exception as e:
        print(f"⚠ непрерывный режим упал ({str(e)[:120]}) → откат на LEVEL")
        return run_level(scenes, lm)


if __name__ == "__main__":
    sys.exit(main())
