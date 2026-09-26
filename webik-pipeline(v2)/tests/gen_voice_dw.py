"""Голос v3 по УТВЕРЖДЁННОЙ схеме (Айдар одобрил demo voice_E):
сегменты из scenes.json (хук; каждая тема = level_announce[если есть]+topic_announce+тело;
аутро), каждый сегмент — ОТДЕЛЬНЫЙ заказ Lumean на v3+ru шаблоне, паузы {{pause=2.0}}
вокруг анонсов, между сегментами 2с тишины. Склейка + пересборка alignment со сдвигами.
Пишет assets/voice/full.mp3, assets/voice/full.align.json, assets/alignment.json."""
import json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from services.tts.lumean import LumeanTTS
from services.stt.aligner import _map_scenes_to_whisper_words

PROJECT = ROOT / "projects" / "2026-08-25_aysberg-dreamworks-lost-media-i-temnaya-skrytaya-storona-stu"
VOICE = PROJECT / "assets" / "voice"
SEGDIR = VOICE / "_segs"
TEMPLATE = "01a038b6-0be6-7091-b6cd-6b090d4b0f3c"  # v3 + ru (утверждён)
GAP = 2.0  # тишина между темами
PAUSE_TAG = " {{pause=2.0}} "


def dur_of(p: Path) -> float:
    r = subprocess.run(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{p}"',
                       shell=True, capture_output=True, text=True)
    try:
        v = float(r.stdout.strip())
        if v > 0: return v
    except Exception:
        pass
    # запасной путь: duration_seconds из align сегмента
    aj = p.with_suffix(".align.json")
    if aj.exists():
        try:
            return float(json.loads(aj.read_text(encoding="utf-8")).get("duration_seconds", 0) or 0)
        except Exception:
            pass
    return 0.0


def build_segments(scenes):
    """→ [(label, text, [scene_ids])] по схеме хук/темы/аутро."""
    segs = []
    hook = {"label": "hook", "sc": []}
    cur = hook
    pending_level = []
    for s in scenes:
        sec = s.get("section") or ""
        vo = (s.get("voiceover") or "").strip()
        if sec == "intro":
            cur["sc"].append(s)
        elif sec == "level_announce":
            pending_level.append(s)
        elif sec == "topic_announce":
            if cur["sc"]: segs.append(cur)
            cur = {"label": s["id"], "sc": pending_level + [s]}
            pending_level = []
        elif sec in ("topic", "main", "body"):
            cur["sc"].append(s)
        elif sec in ("outro", "cta", "conclusion"):
            if cur["label"] != "outro":
                if cur["sc"]: segs.append(cur)
                cur = {"label": "outro", "sc": []}
            cur["sc"].append(s)
        else:
            cur["sc"].append(s)  # прочее — в текущий
    if cur["sc"]: segs.append(cur)
    # текст сегмента: {{pause}} после level_announce и topic_announce
    out = []
    for seg in segs:
        parts, ids = [], []
        for s in seg["sc"]:
            vo = (s.get("voiceover") or "").strip()
            if not vo: continue
            ids.append(s["id"])
            if (s.get("section") or "") in ("level_announce", "topic_announce"):
                parts.append(vo + PAUSE_TAG)
            else:
                parts.append(vo)
        if parts:
            out.append((seg["label"], " ".join(parts), ids))
    return out


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    SEGDIR.mkdir(parents=True, exist_ok=True)
    segs = build_segments(scenes)
    print(f"сегментов: {len(segs)} (хук + темы + аутро)")

    lm = LumeanTTS(template_uuid=TEMPLATE)
    mp3s, combined_words, offset = [], [], 0.0
    # 2с тишина
    sil = SEGDIR / "_sil.mp3"
    subprocess.run(f'ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo -t {GAP} "{sil}"',
                   shell=True, capture_output=True)

    for i, (label, text, ids) in enumerate(segs):
        out = SEGDIR / f"seg_{i:02d}.mp3"
        if not (out.exists() and out.stat().st_size > 10000):
            try:
                lm.synthesize(text, out, save_alignment=True)
            except Exception as e:
                print(f"  ✗ сегмент {i} [{label}]: {str(e)[:80]}"); continue
        d = dur_of(out)
        # слова сегмента со сдвигом
        aj = out.with_suffix(".align.json")
        if aj.exists():
            w = json.loads(aj.read_text(encoding="utf-8")).get("words", [])
            for x in w:
                combined_words.append({"word": x.get("word"),
                                       "start": round(float(x.get("start", 0)) + offset, 3),
                                       "end": round(float(x.get("end", 0)) + offset, 3)})
        mp3s.append(out)
        offset += d + (GAP if i < len(segs) - 1 else 0.0)
        print(f"  ✓ {i:02d} [{label[:20]}] {d:.1f}с → offset {offset:.1f}с ({len(ids)} сцен)")

    # склейка mp3 + тишина между
    lst = SEGDIR / "_concat.txt"
    lines = []
    for j, m in enumerate(mp3s):
        lines.append(f"file '{m.as_posix()}'")
        if j < len(mp3s) - 1: lines.append(f"file '{sil.as_posix()}'")
    lst.write_text("\n".join(lines), encoding="utf-8")
    full = VOICE / "full.mp3"
    subprocess.run(f'ffmpeg -y -f concat -safe 0 -i "{lst}" -c:a libmp3lame -b:a 192k "{full}"',
                   shell=True, capture_output=True)
    total = dur_of(full)
    print(f"\nfull.mp3: {total:.1f}с ({total/60:.1f} мин), слов: {len(combined_words)}")

    # маппинг сцен → слова
    timings = _map_scenes_to_whisper_words(scenes, combined_words)
    (VOICE / "full.align.json").write_text(
        json.dumps({"duration_seconds": round(total, 3), "words": combined_words}, ensure_ascii=False),
        encoding="utf-8")
    (PROJECT / "assets" / "alignment.json").write_text(
        json.dumps({"duration": round(total, 3), "method": "lumean_pertopic_v3ru",
                    "words": combined_words, "scenes": timings, "paused_at_levels": True},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    mapped = sum(1 for v in timings.values() if v.get("end", 0) > 0)
    print(f"alignment: {mapped}/{len(scenes)} сцен замаплено → assets/alignment.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
