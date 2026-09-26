"""Авто-перекачка забракованных vision-QC сцен по better_query + повторный QC (цикл до чистоты).
movie/stock → yt-dlp реальный кадр, archive → фото (wikimedia). Кладёт в assets/_qcfix (живое медиа НЕ трогает).
Печатает before/after брака. Env: QC_LIMIT (сколько сцен для теста), QC_PROJECT."""
import json, os, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import tests.media_vision_qc as vqc            # frame_of, vision_call, PROJECT, BATCH
from tests.source_media_dw import fetch_movie
from services.stocks.wikimedia import WikimediaClient
from services.stocks.wikipedia_photo import WikipediaPhotoClient

PROJECT = vqc.PROJECT
QCFIX = PROJECT / "assets" / "_qcfix"
QCFIX.mkdir(parents=True, exist_ok=True)


YTDLP_ALL = os.environ.get("QC_YTDLP_ALL") == "1"  # для Adult Swim: всё (вкл. новости) есть на YouTube


def refetch(sid, verdict, bucket, idx, tmp):
    q = (verdict.get("better_query") or "").strip()
    if not q:
        return None
    # yt-dlp первым для всех (или для movie/stock как раньше)
    if YTDLP_ALL or bucket in ("movie", "stock"):
        out = QCFIX / f"{sid}.mp4"
        if fetch_movie(q, out, idx, tmp):
            return {"path": str(out.resolve()), "kind": "video"}
    # archive → фолбэк на фото (реальные люди/статичные события)
    if bucket == "archive":
        out = QCFIX / f"{sid}.jpg"
        try:
            if WikimediaClient().search_and_download(q, out) and out.stat().st_size > 6000:
                return {"path": str(out.resolve()), "kind": "image"}
        except Exception:
            pass
        try:
            name = q.split(" 19")[0].split(" 20")[0].strip()
            if WikipediaPhotoClient().download_photo(name, out) and out.stat().st_size > 6000:
                return {"path": str(out.resolve()), "kind": "image"}
        except Exception:
            pass
    return None


def qc_batch(shadow_man, scenes_vo, ids):
    """re-QC списка sid по shadow-манифесту → {sid: verdict}."""
    items = []
    for sid in ids:
        img = vqc.frame_of(sid, shadow_man)
        if img:
            items.append({"id": sid, "vo": scenes_vo.get(sid, ""), "img": img})
    verd = {}
    for i in range(0, len(items), vqc.BATCH):
        try:
            for v in vqc.vision_call(items[i:i + vqc.BATCH]):
                if v.get("id"):
                    verd[v["id"]] = v
        except Exception as e:
            print(f"  ✗ re-QC батч: {str(e)[:80]}", flush=True)
    return verd


def main() -> int:
    qc = json.loads((PROJECT / "_media_qc.json").read_text(encoding="utf-8"))
    plan = json.loads((PROJECT / "media_plan_dw.json").read_text(encoding="utf-8"))
    scenes = json.loads((PROJECT / "scenes.json").read_text(encoding="utf-8"))["scenes"]
    vo = {s["id"]: (s.get("voiceover") or "").strip() for s in scenes}
    bucket = {sid: (plan.get(sid, {}) or {}).get("bucket", "movie") for sid in qc}

    suspects = [sid for sid, v in qc.items() if not v.get("ok")]
    lim = int(os.environ.get("QC_LIMIT", "0"))
    if lim:
        suspects = suspects[:lim]
    print(f"к перекачке: {len(suspects)}", flush=True)

    tmp = Path(tempfile.mkdtemp())
    rounds = int(os.environ.get("QC_ROUNDS", "3"))
    shadow, good = {}, {}           # sid → media (принятое QC)
    todo = list(suspects)
    for rnd in range(1, rounds + 1):
        if not todo:
            break
        print(f"\n--- РАУНД {rnd}: перекачиваю {len(todo)} ---", flush=True)
        got = []
        for i, sid in enumerate(todo):
            # варьируем запрос по раунду: better_query → fallback из плана → better_query
            v = dict(qc[sid])
            if rnd >= 2:
                fb = (plan.get(sid, {}) or {}).get("fallback")
                if fb and rnd == 2: v["better_query"] = fb
            r = refetch(sid, v, bucket.get(sid, "movie"), i + rnd * 7, tmp)
            if r:
                shadow[sid] = r; got.append(sid)
        verd = qc_batch({s: shadow[s] for s in got}, vo, got)
        newly = [s for s in got if verd.get(s, {}).get("ok")]
        for s in newly: good[s] = shadow[s]
        todo = [s for s in todo if s not in good]
        print(f"  раунд {rnd}: перекачано {len(got)}, принято QC {len(newly)}, осталось брака {len(todo)}", flush=True)

    print(f"\n=== ИТОГ ({rounds} раунда) ===")
    print(f"было брака: {len(suspects)} | ИСПРАВЛЕНО: {len(good)} | осталось (ручками): {len(todo)}")
    for s in todo[:20]:
        print(f"  осталось: {s} [{bucket.get(s)}] {(qc[s].get('reason') or '')[:45]}")
    (PROJECT / "_qcfix_result.json").write_text(json.dumps(
        {"fixed": list(good), "still_bad": todo, "shadow": good}, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
