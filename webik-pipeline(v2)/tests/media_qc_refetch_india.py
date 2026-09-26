"""Авто-перекачка забракованных vision-QC сцен «Айсберг Индии» через PEXELS-видео
(текст-free, монетизация-safe) по better_query + повторный QC (2 раунда). Живое медиа НЕ трогает
до финального применения: пишет в assets/_qcfix, потом обновляет manifest ТОЛЬКО для принятых QC.
Пути в manifest — относительные (см. bug_cross_project_media). Env: QC_LIMIT, QC_ROUNDS."""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.media_vision_qc as vqc            # frame_of, vision_call, BATCH, PROJECT
from services.stocks.pexels_videos import PexelsVideosClient

PROJECT = vqc.PROJECT
QCFIX = PROJECT / "assets" / "_qcfix"; QCFIX.mkdir(parents=True, exist_ok=True)
CACHE = PROJECT / "assets" / "_pexels_cache"; CACHE.mkdir(parents=True, exist_ok=True)
MAN_PATH = PROJECT / "assets" / "images" / "manifest.json"
px = PexelsVideosClient()


def norm(src: Path, dst: Path, d=8.0) -> bool:
    vf = ("scale=1920:1080:force_original_aspect_ratio=increase,crop=1920:1080,"
          "eq=saturation=0.95:contrast=1.04,setsar=1,fps=30")
    r = subprocess.run(["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src), "-t", f"{d:.2f}",
                        "-an", "-vf", vf, "-r", "30", "-c:v", "libx264", "-crf", "20",
                        "-pix_fmt", "yuv420p", str(dst)], capture_output=True, text=True)
    return r.returncode == 0 and dst.exists() and dst.stat().st_size > 40000


def fetch_pexels(sid, query, rnd) -> Path | None:
    q = query if rnd == 1 else f"{query} india cinematic"
    for idx in (rnd - 1, 0, 1):
        try:
            p = px.search_and_download(q, CACHE / f"{sid}_r{rnd}_{idx}.mp4", index=idx, min_duration=4)
            if p and Path(p).exists() and Path(p).stat().st_size > 10000:
                dst = QCFIX / f"{sid}.mp4"
                if dst.exists(): dst.unlink()
                if norm(Path(p), dst):
                    return dst
        except Exception as e:
            print(f"    {sid} pexels err idx{idx}: {str(e)[:40]}", flush=True)
    return None


def reqc(sids, shadow, vo):
    items = []
    for sid in sids:
        img = vqc.frame_of(sid, shadow)
        if img:
            items.append({"id": sid, "vo": vo.get(sid, ""), "img": img})
    verd = {}
    for i in range(0, len(items), vqc.BATCH):
        try:
            for v in vqc.vision_call(items[i:i + vqc.BATCH]):
                if v.get("id"):
                    verd[v["id"]] = v
        except Exception as e:
            print(f"  re-QC батч err: {str(e)[:70]}", flush=True)
    return verd


def main() -> int:
    qc = json.loads((PROJECT / "_media_qc.json").read_text(encoding="utf-8"))
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    vo = {s["id"]: (s.get("voiceover") or "").strip() for s in scenes}
    man = json.loads(MAN_PATH.read_text(encoding="utf-8"))

    bad = [sid for sid, v in qc.items() if not v.get("ok")]
    # опц.: добивать только остаток после yt-раунда (QC_ONLY_STILL=1 → _qcfix2_result.json still_bad)
    if os.environ.get("QC_ONLY_STILL") == "1":
        f2 = PROJECT / "_qcfix2_result.json"
        if f2.exists():
            bad = list(json.loads(f2.read_text(encoding="utf-8")).get("still_bad", []))
    lim = int(os.environ.get("QC_LIMIT", "0"))
    if lim: bad = bad[:lim]
    print(f"к перекачке: {len(bad)}", flush=True)

    rounds = int(os.environ.get("QC_ROUNDS", "2"))
    good = {}                      # sid → shadow media entry (принято QC)
    todo = list(bad)
    for rnd in range(1, rounds + 1):
        if not todo: break
        print(f"\n--- РАУНД {rnd}: перекачиваю {len(todo)} ---", flush=True)
        shadow, got = {}, []
        for sid in todo:
            q = (qc[sid].get("better_query") or "").strip()
            if not q or q == "ok":
                q = (vo.get(sid, "")[:60] + " india")
            f = fetch_pexels(sid, q, rnd)
            if f:
                shadow[sid] = {"path": str(f.relative_to(PROJECT)).replace("\\", "/"), "kind": "video"}
                got.append(sid)
        verd = reqc(got, shadow, vo)
        newly = [s for s in got if verd.get(s, {}).get("ok")]
        for s in newly: good[s] = shadow[s]
        todo = [s for s in todo if s not in good]
        print(f"  раунд {rnd}: перекачано {len(got)}, принято QC {len(newly)}, осталось {len(todo)}", flush=True)

    # применяем принятые → manifest (относительный путь, source qcfix)
    for sid, entry in good.items():
        man[sid] = {"path": entry["path"].replace("/", "\\"), "query": qc[sid].get("better_query", ""),
                    "kind": "video", "source": "pexels-qcfix"}
    MAN_PATH.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n=== ИТОГ ({rounds} раунда) ===")
    print(f"было брака: {len(bad)} | ИСПРАВЛЕНО+применено: {len(good)} | осталось: {len(todo)}")
    for s in todo[:25]:
        print(f"  осталось: {s} [{qc[s].get('issue')}] {(qc[s].get('reason') or '')[:50]}")
    (PROJECT / "_qcfix_result.json").write_text(json.dumps(
        {"fixed": list(good), "still_bad": todo}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
