"""Перцептивный детектор визуальных повторов на V3: извлекает по несколько кадров из
КАЖДОГО клипа тела (то, что реально видно), считает average-hash и группирует близкие
(Hamming <= порог). Ловит повтор даже если один исходник нарезан на разные файлы.
Пишет _visrep_as.json {groups:[[sid,...]]}. Env: VISREP_THRESH (по умолч. 6)."""
import json, os, subprocess, sys, tempfile
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from PIL import Image

PROJECT = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c"
TRIMMED = PROJECT / "assets" / "video_stock" / "_trimmed"
THRESH = int(os.environ.get("VISREP_THRESH", "6"))
TMP = Path(tempfile.mkdtemp())


def ahash(img_path):
    try:
        im = Image.open(img_path).convert("L").resize((8, 8), Image.LANCZOS)
        px = list(im.getdata())
        avg = sum(px) / len(px)
        bits = 0
        for i, p in enumerate(px):
            if p >= avg:
                bits |= (1 << i)
        return bits
    except Exception:
        return None


def frames_hash(mp4, sid, n=3):
    """n кадров равномерно → список aHash (устойчивее к статик-интро/концовкам)."""
    dur = 2.0
    try:
        r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                            "-of", "csv=p=0", str(mp4)], capture_output=True, text=True)
        dur = float(r.stdout.strip())
    except Exception:
        pass
    hs = []
    for k in range(n):
        t = dur * (k + 1) / (n + 1)
        out = TMP / f"{sid}_{k}.jpg"
        subprocess.run(["ffmpeg", "-y", "-ss", f"{max(0.1, t):.2f}", "-i", str(mp4),
                        "-frames:v", "1", "-vf", "scale=64:64", str(out)], capture_output=True)
        if out.exists():
            hh = ahash(out)
            if hh is not None:
                hs.append(hh)
    return hs


def ham(a, b):
    return bin(a ^ b).count("1")


def main() -> int:
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    man = json.loads((PROJECT / "assets" / "images" / "manifest.json").read_text(encoding="utf-8"))
    CARD = {"level_card", "topic_card"}
    body = [s["id"] for s in scenes if (s.get("visual") or {}).get("type") not in CARD and s["id"] in man]
    body.sort(key=lambda sid: al.get(sid, {}).get("start", 0))

    sig = {}
    for k, sid in enumerate(body):
        mp4 = None                                # приоритет: свежайший подменённый (_dd2 > _dd > база)
        for cand in (TRIMMED / f"{sid}_dd2.mp4", TRIMMED / f"{sid}_dd.mp4", TRIMMED / f"{sid}.mp4"):
            if cand.exists():
                mp4 = cand; break
        if mp4 is None:
            mp4 = Path(man[sid]["path"])          # фолбэк на исходник
        if not mp4.exists():
            continue
        hs = frames_hash(mp4, sid)
        if hs:
            sig[sid] = hs
        if (k + 1) % 40 == 0:
            print(f"  ...{k+1}/{len(body)}", flush=True)

    # группируем: два клипа = повтор, если ЛЮБАЯ пара их кадров близка
    def similar(a, b):
        return any(ham(x, y) <= THRESH for x in sig[a] for y in sig[b])

    order = [s for s in body if s in sig]
    parent = {s: s for s in order}
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for i in range(len(order)):
        for j in range(i + 1, len(order)):
            a, b = order[i], order[j]
            if find(a) != find(b) and similar(a, b):
                parent[find(b)] = find(a)

    groups = defaultdict(list)
    for s in order:
        groups[find(s)].append(s)
    reps = [sorted(v, key=lambda sid: al.get(sid, {}).get("start", 0)) for v in groups.values() if len(v) > 1]
    reps.sort(key=lambda g: al.get(g[0], {}).get("start", 0))

    def tc(sid):
        st = al.get(sid, {}).get("start", 0); return f"{int(st//60)}:{int(st%60):02d}"
    print(f"\nклипов проверено: {len(order)} | групп-повторов: {len(reps)} | "
          f"клипов в повторах: {sum(len(g) for g in reps)}\n")
    for g in reps:
        print(f"  x{len(g)}: " + ", ".join(f"{tc(s)} {s}" for s in g))
    (PROJECT / "_visrep_as.json").write_text(json.dumps({"groups": reps}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
