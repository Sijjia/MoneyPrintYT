"""Финальная генерация голоса ролика через Lumean с фиксами Айдара:
- произношение (ударения, services/tts/pronunciation.py)
- уровень → сразу тема (подытог уже вырезан)
- пауза РОВНО 1.5с после названия темы (реальная тишина по alignment)
Результат: assets/voice/full.mp3 (+ full.align.json со сдвинутым таймингом).
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS
from services.tts.pronunciation import apply_pronunciation

PROJECT = Path(__file__).resolve().parent.parent / "projects" / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
VOICE = PROJECT / "assets" / "voice"
TOPIC_PAUSE = 1.5


def norm(s: str) -> str:
    return re.sub(r"[^а-яёa-z0-9]", "", s.replace("́", "").lower())


def main() -> int:
    sc = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))
    items = sc if isinstance(sc, list) else sc["scenes"]

    # 1. текст + произношение + список названий тем (для пауз)
    parts, prev, topic_titles = [], None, []
    for s in items:
        vo = (s.get("voiceover") or "").strip()
        if not vo:
            continue
        lvl = s.get("level", 0)
        if prev is not None and lvl != prev:
            parts.append("[пауза 2с]")
        parts.append(vo)
        prev = lvl
        if s.get("visual", {}).get("type") == "topic_card":
            topic_titles.append([norm(w) for w in vo.split() if norm(w)])
    full = apply_pronunciation(" ".join(parts))
    (PROJECT / "_full_vo.txt").write_text(full, encoding="utf-8")
    print(f"текст {len(full)} симв., тем для паузы: {len(topic_titles)}")

    # 2. генерация
    raw = VOICE / "_lumean_raw.mp3"
    LumeanTTS().synthesize(full, raw, save_alignment=True)
    align = json.loads((raw.with_suffix(".align.json")).read_text(encoding="utf-8"))
    words = align["words"]

    # 3. найти конец каждого названия темы в alignment
    nwords = [norm(w["word"]) for w in words]
    cut_points = []
    for title in topic_titles:
        if len(title) < 2:
            continue
        # ищем консекутивную последовательность title в nwords
        for i in range(len(nwords) - len(title) + 1):
            if nwords[i:i + len(title)] == title:
                cut_points.append(words[i + len(title) - 1]["end"])
                break
        else:
            # мягкий матч: первое+последнее слово рядом
            first, last = title[0], title[-1]
            for i in range(len(nwords) - 1):
                if nwords[i] == first:
                    for j in range(i + 1, min(i + len(title) + 3, len(nwords))):
                        if nwords[j] == last:
                            cut_points.append(words[j]["end"])
                            break
                    break
    cut_points = sorted(set(round(c, 3) for c in cut_points))
    print(f"вставляю паузу 1.5с в {len(cut_points)} точках (тем {len(topic_titles)})")

    # 4. режем аудио и вставляем тишину
    tmp = Path(tempfile.gettempdir())
    subprocess.run(["ffmpeg", "-y", "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
                    "-t", str(TOPIC_PAUSE), "-q:a", "9", str(tmp / "_sil.mp3")], capture_output=True)
    segs, listf = [], []
    prev_t = 0.0
    for k, c in enumerate(cut_points):
        seg = tmp / f"_seg_{k}.mp3"
        subprocess.run(["ffmpeg", "-y", "-ss", str(prev_t), "-to", str(c), "-i", str(raw),
                        "-c", "copy", str(seg)], capture_output=True)
        listf.append(seg); listf.append(tmp / "_sil.mp3"); prev_t = c
    tail = tmp / "_seg_tail.mp3"
    subprocess.run(["ffmpeg", "-y", "-ss", str(prev_t), "-i", str(raw), "-c", "copy", str(tail)], capture_output=True)
    listf.append(tail)
    lst = tmp / "_concat.txt"
    lst.write_text("".join(f"file '{p.as_posix()}'\n" for p in listf), encoding="utf-8")
    out = VOICE / "full.mp3"
    subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out)], capture_output=True)

    # 5. сдвиг alignment на вставленные паузы
    shifted = []
    for w in words:
        add = TOPIC_PAUSE * sum(1 for c in cut_points if c <= w["start"])
        shifted.append({"word": w["word"], "start": round(w["start"] + add, 3), "end": round(w["end"] + add, 3)})
    dur = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(out)], capture_output=True, text=True).stdout.strip()
    (VOICE / "full.align.json").write_text(json.dumps(
        {"duration_seconds": float(dur or 0), "words": shifted}, ensure_ascii=False), encoding="utf-8")
    print(f"ГОТОВО: full.mp3 {dur}s ({len(shifted)} слов, +{len(cut_points)} пауз по 1.5с)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
