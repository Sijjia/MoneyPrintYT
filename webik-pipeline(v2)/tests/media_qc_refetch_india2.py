"""Добивочный раунд для «Айсберг Индии»: оставшиеся после Pexels-перекачки бракованные сцены
(специфичные субъекты — храмы/аскеты/форты/реальные события) тянем РЕАЛЬНЫМ YouTube-архивом
(yt-dlp) по better_query + повторный QC (2 попытки, варьируем стартовый оффсет). Применяет в
manifest только принятое QC (относительный путь). Env: QC_ROUNDS."""
import json, os, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.media_vision_qc as vqc
from tests.source_media_dw import fetch_movie

PROJECT = vqc.PROJECT
QCFIX2 = PROJECT / "assets" / "_qcfix2"; QCFIX2.mkdir(parents=True, exist_ok=True)
MAN_PATH = PROJECT / "assets" / "images" / "manifest.json"


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
            print(f"  re-QC err: {str(e)[:70]}", flush=True)
    return verd


def main() -> int:
    qc = json.loads((PROJECT / "_media_qc.json").read_text(encoding="utf-8"))
    res = json.loads((PROJECT / "_qcfix_result.json").read_text(encoding="utf-8"))
    still = list(res.get("still_bad", []))
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    vo = {s["id"]: (s.get("voiceover") or "").strip() for s in scenes}
    man = json.loads(MAN_PATH.read_text(encoding="utf-8"))
    print(f"добиваем YouTube-архивом: {len(still)}", flush=True)

    tmp = Path(tempfile.mkdtemp())
    rounds = int(os.environ.get("QC_ROUNDS", "2"))
    good = {}
    todo = list(still)
    for rnd in range(1, rounds + 1):
        if not todo: break
        print(f"\n--- YT РАУНД {rnd}: {len(todo)} ---", flush=True)
        shadow, got = {}, []
        for i, sid in enumerate(todo):
            q = (qc[sid].get("better_query") or "").strip()
            if not q or q == "ok":
                q = vo.get(sid, "")[:60]
            q = f"{q} india"
            out = QCFIX2 / f"{sid}.mp4"
            try:
                ok = fetch_movie(q, out, i + rnd * 5, tmp)
            except Exception as e:
                print(f"    {sid} yt err: {str(e)[:50]}", flush=True); ok = False
            if ok:
                shadow[sid] = {"path": str(out.relative_to(PROJECT)).replace("\\", "/"), "kind": "video"}
                got.append(sid)
        verd = reqc(got, shadow, vo)
        newly = [s for s in got if verd.get(s, {}).get("ok")]
        for s in newly: good[s] = shadow[s]
        todo = [s for s in todo if s not in good]
        print(f"  YT раунд {rnd}: скачано {len(got)}, принято QC {len(newly)}, осталось {len(todo)}", flush=True)

    for sid, entry in good.items():
        man[sid] = {"path": entry["path"].replace("/", "\\"), "query": qc[sid].get("better_query", ""),
                    "kind": "video", "source": "youtube-qcfix"}
    MAN_PATH.write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n=== YT ИТОГ ===")
    print(f"добивали: {len(still)} | ИСПРАВЛЕНО+применено: {len(good)} | осталось: {len(todo)}")
    for s in todo[:30]:
        print(f"  осталось: {s} [{qc[s].get('issue')}] {(qc[s].get('reason') or '')[:45]}")
    (PROJECT / "_qcfix2_result.json").write_text(json.dumps(
        {"fixed_yt": list(good), "still_bad": todo}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
