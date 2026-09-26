"""Сборка «Айсберг религиозного террора» template-based (копия Апокалипсиса).

Адаптация tests/assemble_iceberg_test.py под полноразмерный проект:
  - пути → наш проект, ZONE_END = полная длина озвучки
  - медиа берём из assets/images/manifest.json (video_stock / parallax / youtube)
  - тема-плашки печатной машинкой из voiceover анонсов
  - уровни: родная плашка «1 УРОВЕНЬ» из шаблона в первый слот (L2-L4 Айдар копирует руками)

Запуск (Premiere + панель pymiere открыты):
  ../webik-pipeline/.venv/Scripts/python.exe tests/assemble_religioznyj.py
"""
from __future__ import annotations
import json, glob, os, shutil, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pymiere.core  # noqa: E402
from pymiere import objects as p  # noqa: E402

# переиспользуем проверенные хелперы из общего модуля (только то, что реально нужно;
# фейды теперь свои batch-ом ниже, плашку уровня не ставим — см. шаги [7]/[2b])
from tests.assemble_iceberg_test import (  # noqa: E402
    log, set_clip_volume, find_clip_by_timeline_start, trim_sfx,
    health_check, FADE_SEC, TW_LEAD_IN, TW_CPS,
    TYPING_SFX_SRC, TYPING_SFX_VOLUME, TYPING_SFX_TAIL,
    render_topic_card_typewriter,
)
from services.premiere_template.media_swap import ensure_premiere_open, current_project_path, save_project  # noqa: E402
from services.premiere_template.timeline_ops import (  # noqa: E402
    clear_track_es, clear_zone_es, clear_past_es, remove_clip_at_es,
    import_media, place_clip, _throttle,
)

PROJECT_DIR = Path(sorted(glob.glob(str(
    Path(__file__).resolve().parent.parent / "projects" / "2026-08-25_aysberg-dreamworks*")))[0])
COPY_PRPROJ = PROJECT_DIR / "project_template.prproj"
TEMPLATE_PRPROJ = Path(r"C:\Users\aidar\OneDrive\Документы\Adobe\Premiere Pro\25.0\13 видео-Айсберги-Апокалипсис.prproj")
VOICE_PATH = PROJECT_DIR / "assets" / "voice" / "full.mp3"
PARALLAX_DIR = PROJECT_DIR / "assets" / "parallax"
TRIMMED_DIR = PROJECT_DIR / "assets" / "video_stock" / "_trimmed"
CARDS_DIR = PROJECT_DIR / "assets" / "level_cards"
SFX_DIR = PROJECT_DIR / "assets" / "sfx"
SCENES_PATH = PROJECT_DIR / "scenes.json"
ALIGNMENT_PATH = PROJECT_DIR / "assets" / "alignment.json"
MANIFEST_PATH = PROJECT_DIR / "assets" / "images" / "manifest.json"

# Мини-прогон: собираем только сцены с level <= MINI_LIMIT_LEVEL (intro=0, L1=1).
# -1 (или env MINI_LIMIT_LEVEL=-1) = полный ролик, все 200 сцен.
MINI_LIMIT_LEVEL = int(os.environ.get("MINI_LIMIT_LEVEL", "1"))

ZONE_VIDEO_TRACKS_TO_CLEAR = [1, 2, 3]  # V2-V4
PARALLAX_VIDEO_TRACK_IDX = 2   # V3 — основной видеослой
TOPIC_CARD_TRACK_IDX = 3       # V4 — тема печатной машинкой
A3_MUSIC_DELETE_TRACK_IDX = 2  # A3
TYPING_SFX_TRACK_IDX = 3       # A4


def pretrim_fill(src: Path, dst: Path, dur: float) -> bool:
    """Режет src РОВНО под dur, зацикливая если исходник короче слота (нет дырок).
    Звук выкидываем (-an) — на V3 он всё равно мьютится."""
    import subprocess
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 100_000:
        return True
    cmd = ["ffmpeg", "-y", "-stream_loop", "-1", "-i", str(src),
           "-t", f"{dur:.3f}", "-an",
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
           "-pix_fmt", "yuv420p", str(dst)]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            log(f"    [ffmpeg-fail] {src.name}: {r.stderr[-200:]}")
            return False
    except Exception as e:
        log(f"    [ffmpeg-err] {src.name}: {e}")
        return False
    return dst.exists() and dst.stat().st_size > 0


def reset_copy_from_template() -> None:
    cur = current_project_path()
    if cur is not None:
        log(f"    closing open project: {cur.name}")
        p.app.project.closeDocument(False); time.sleep(1.0)
    log("    overwriting copy from fresh template")
    shutil.copy2(TEMPLATE_PRPROJ, COPY_PRPROJ); time.sleep(0.5)
    log("    opening fresh copy")
    p.app.openDocument(str(COPY_PRPROJ)); time.sleep(1.5)
    try:
        n_a1 = int(pymiere.core.eval_script("app.project.activeSequence.audioTracks[0].clips.numItems;"))
    except Exception as e:
        raise RuntimeError(f"reset: не смог проверить проект: {e}")
    if n_a1 < 30:
        raise RuntimeError(f"reset FAILED: открыт НЕ свежий шаблон (A1={n_a1}, ждали ~40). Закрой проект вручную.")
    log(f"    sanity OK: A1={n_a1} субклипов (свежий шаблон)")


def build_scene_plan(scenes_list, scene_timings, vo_total_sec, manifest):
    sorted_scenes = sorted(
        [(s["id"], s, scene_timings[s["id"]]) for s in scenes_list if s["id"] in scene_timings],
        key=lambda t: t[2]["start"])
    cuts = []
    for i, (sid, scene, tim) in enumerate(sorted_scenes):
        cuts.append(0.0 if i == 0 else (sorted_scenes[i-1][2]["end"] + tim["start"]) / 2.0)

    plan = []
    for i, (sid, scene, tim) in enumerate(sorted_scenes):
        start = cuts[i]
        next_start = cuts[i+1] if i+1 < len(cuts) else vo_total_sec
        target_dur = max(0.4, next_start - start)
        vtype = scene["visual"]["type"]
        is_level_card = vtype == "level_card"
        is_topic_card = vtype == "topic_card"
        is_card = is_level_card or is_topic_card
        card_level = int(scene.get("level", 0))
        card_kind = "level" if is_level_card else ("topic" if is_topic_card else None)
        card_text = media = src_for_pretrim = None

        if is_card:
            card_text = (f"{card_level} УРОВЕНЬ" if is_level_card
                         else (scene.get("voiceover", "") or "").strip().rstrip("."))
        else:
            entry = manifest.get(sid, {})
            mp = entry.get("path")
            full = (PROJECT_DIR / mp) if mp else None
            if full and full.suffix.lower() in (".mp4", ".mov"):
                media = TRIMMED_DIR / f"{sid}.mp4"      # создастся в pretrim
                src_for_pretrim = full
            elif full and full.exists():                # картинка → parallax mp4, иначе как есть
                media = next(PARALLAX_DIR.glob(f"{sid}__*.mp4"), None) or full
            else:
                media = next(PARALLAX_DIR.glob(f"{sid}__*.mp4"), None)

        plan.append({
            "id": sid, "section": scene.get("section"), "level": card_level,
            "media": media, "src_for_pretrim": src_for_pretrim, "target_dur": target_dur,
            "is_card": is_card, "card_kind": card_kind, "card_level": card_level,
            "card_text": card_text, "start": start, "next_start": next_start,
            "fade_in": 0.0 if is_card else FADE_SEC, "fade_out": 0.0 if is_card else FADE_SEC,
        })
    return plan


def apply_fades_batch_es(track_idx: int, specs: list) -> str:
    """Dip-to-black фейды (opacity keyframes) для МНОГИХ клипов V-дорожки за ОДИН
    eval_script — весь цикл внутри JS, без python round-trip'ов (старый путь через
    объектную модель pymiere давал ~4с/клип + O(n²) поиск → десятки минут/вис).

    specs: [{'start': timeline_sec, 'fi': fade_in_sec, 'fo': fade_out_sec}, ...].
    """
    import json as _json
    arr = _json.dumps([[float(s["start"]), float(s["fi"]), float(s["fo"])] for s in specs])
    js = """
    function fadeAll(){
      var seq=app.project.activeSequence;
      var trk=seq.videoTracks[%d];
      var specs=%s;
      var TOL=0.5, done=0, miss=0, noop=0;
      // индекс клипов по началу — один проход
      var clips=[];
      for(var i=0;i<trk.clips.numItems;i++) clips.push(trk.clips[i]);
      for(var s=0;s<specs.length;s++){
        var tstart=specs[s][0], fi=specs[s][1], fo=specs[s][2];
        var c=null;
        for(var i=0;i<clips.length;i++){ if(Math.abs(clips[i].start.seconds-tstart)<TOL){ c=clips[i]; break; } }
        if(!c){ miss++; continue; }
        var opc=null;
        for(var j=0;j<c.components.numItems;j++){ if(c.components[j].displayName.toLowerCase()=='opacity'){opc=c.components[j];break;} }
        if(!opc){ noop++; continue; }
        var op=null;
        for(var k=0;k<opc.properties.numItems;k++){ if(opc.properties[k].displayName.toLowerCase()=='opacity'){op=opc.properties[k];break;} }
        if(!op || !op.areKeyframesSupported()){ noop++; continue; }
        if(!op.isTimeVarying()) op.setTimeVarying(true);
        var ins=c.inPoint.seconds, outs=c.outPoint.seconds, dur=outs-ins;
        if(dur<=0){ noop++; continue; }
        var maxh=dur/4.0;
        if(fi>maxh) fi=maxh; if(fo>maxh) fo=maxh;
        try{ op.removeKeyRange(ins,outs,true); }catch(e){}
        if(fi>0){ op.addKey(ins); op.setValueAtKey(ins,0.0,true); op.addKey(ins+fi); op.setValueAtKey(ins+fi,100.0,true); }
        else { op.addKey(ins); op.setValueAtKey(ins,100.0,true); }
        if(fo>0){ op.addKey(outs-fo); op.setValueAtKey(outs-fo,100.0,true); op.addKey(outs); op.setValueAtKey(outs,0.0,true); }
        else { op.addKey(outs); op.setValueAtKey(outs,100.0,true); }
        done++;
      }
      return 'faded='+done+' miss='+miss+' noop='+noop;
    }
    fadeAll();
    """ % (track_idx, arr)
    return pymiere.core.eval_script(js)


def main() -> int:
    for path in (VOICE_PATH, ALIGNMENT_PATH, SCENES_PATH, MANIFEST_PATH, TEMPLATE_PRPROJ):
        if not path.exists():
            log(f"ERROR missing: {path}"); return 1

    scenes_data = json.loads(SCENES_PATH.read_text(encoding="utf-8"))
    alignment = json.loads(ALIGNMENT_PATH.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    scene_timings = alignment["scenes"]
    vo_total = float(alignment["duration"])
    zone_end = vo_total + 5.0

    plan = build_scene_plan(scenes_data["scenes"], scene_timings, vo_total, manifest)

    # [MINI] урезаем план до intro+L1 (level<=MINI_LIMIT_LEVEL); голос A1 играет целиком,
    # видео/карточки кладём только в первую зону, остаток чистит шаг [5].
    if MINI_LIMIT_LEVEL >= 0:
        full_n = len(plan)
        plan = [e for e in plan if int(e["level"]) <= MINI_LIMIT_LEVEL]
        if not plan:
            log("ERROR: MINI limit отфильтровал все сцены"); return 1
        zone_end = plan[-1]["next_start"] + FADE_SEC + 1.0
        log(f"[MINI] level<={MINI_LIMIT_LEVEL}: {len(plan)}/{full_n} сцен, zone_end={zone_end:.1f}s "
            f"(последняя {plan[-1]['id']})")

    n_body = sum(1 for e in plan if not e["is_card"])
    n_topic = sum(1 for e in plan if e["card_kind"] == "topic")
    n_level = sum(1 for e in plan if e["card_kind"] == "level")
    log(f"[0] план: {len(plan)} сцен ({n_body} видео, {n_level} level, {n_topic} topic), "
        f"vo={vo_total:.1f}s, zone_end={zone_end:.1f}s")

    # [A] ffmpeg pretrim: режем ровно под слот + зацикливаем короткие (без дырок)
    log(f"[A] pretrim видео (loop-fill) → {TRIMMED_DIR}")
    if TRIMMED_DIR.exists():
        shutil.rmtree(TRIMMED_DIR, ignore_errors=True)  # перегенерить с loop-fill
    TRIMMED_DIR.mkdir(parents=True, exist_ok=True)
    for e in plan:
        if e["src_for_pretrim"] is None:
            continue
        ok = pretrim_fill(e["src_for_pretrim"], e["media"], e["target_dur"])
        if not ok and not e["media"].exists():
            e["media"] = e["src_for_pretrim"]  # fallback: непорезанный
    log("    pretrim done")

    # [A2] рендер тема-плашек печатной машинкой + звук
    run_tag = str(int(time.time()))
    log(f"[A2] рендер topic-плашек (печатная машинка), tag={run_tag}")
    CARDS_DIR.mkdir(parents=True, exist_ok=True); SFX_DIR.mkdir(parents=True, exist_ok=True)
    for e in plan:
        if not (e["is_card"] and e["card_kind"] == "topic"):
            continue
        title = (e["card_text"] or "").strip()
        e["topic_mov"] = e["sfx_wav"] = None
        e["sfx_start"] = e["start"] + TW_LEAD_IN
        if not title:
            continue
        out_mov = CARDS_DIR / f"topic_{e['id']}_tw_{run_tag}.mov"
        for attempt in range(1, 4):
            try:
                _, dur = render_topic_card_typewriter(title, out_mov, total_target=e["target_dur"])
                e["topic_mov"] = out_mov
                break
            except Exception as ex:
                log(f"    [retry {attempt}/3] {e['id']}: {ex}"); time.sleep(0.5)
        if e["topic_mov"] and TYPING_SFX_SRC.exists():
            sfx_dur = len(title.upper()) / max(1.0, TW_CPS) + TYPING_SFX_TAIL
            sfx_dst = SFX_DIR / f"typing_{e['id']}_{run_tag}.wav"
            if trim_sfx(TYPING_SFX_SRC, sfx_dst, sfx_dur):
                e["sfx_wav"] = sfx_dst
    log("    topic cards done")

    # [B] Premiere
    log("[B] connecting to Premiere")
    ensure_premiere_open(None)
    if not health_check("after-connect"):
        return 1
    log("[1] reset copy → fresh Apocalypse template")
    reset_copy_from_template()
    if not health_check("after-reset"):
        return 1
    seq = p.app.project.activeSequence
    n_v = getattr(seq.videoTracks, "numTracks", None) or len(list(seq.videoTracks))
    n_a = getattr(seq.audioTracks, "numTracks", None) or len(list(seq.audioTracks))
    log(f"    seq={seq.name}, V={n_v}, A={n_a}")

    # [2] голос на A1
    log("[2] A1 voice swap")
    a1 = seq.audioTracks[0]
    clear_track_es("audioTracks", 0)
    voice_item = import_media(VOICE_PATH)
    if voice_item is None:
        log("ERROR import voice"); return 1
    place_clip(a1, voice_item, 0.0)
    if not health_check("after-A1"):
        return 1

    # [2b] Плашку уровня НЕ ставим — решение Айдара 2026-07-06: родной MOGRT уровня
    # имеет встроенный уход в чёрное (blur+opacity keyframes) и скриптом корректно не
    # ставится (мигает/чернеет). Место уровня оставляем ПУСТЫМ — Айдар вставит свою
    # графику вручную для всех 4 уровней. V1 полностью чистим в шаге [3] ниже.

    # [3] чистим ВЕСЬ шаблон Апокалипсиса в зоне: ВСЕ видеодорожки включая V1
    # (плашку уровня не ставим — место пустое под ручную графику Айдара) и все аудио
    # кроме A1 (наш голос). Иначе родной контент Апокалипсиса (графика V1, грейдинг V5,
    # screenshot V6, музыка/sfx A2-A4) лезет ПОВЕРХ/вместо нашего.
    log(f"[3] clear zone 0-{zone_end:.0f}s: ВСЕ V1..V{n_v} + A2..A{n_a}")
    for idx in range(0, n_v):        # V1..Vn (V1 тоже — место уровня оставляем пустым)
        r = clear_zone_es("videoTracks", idx, zone_end)
        log(f"    V{idx+1}: cleared {r}")
    for idx in range(1, n_a):        # A2..An (A1 = наш голос)
        r = clear_zone_es("audioTracks", idx, zone_end)
        log(f"    A{idx+1}: cleared {r}")
    if not health_check("after-clearzone"):
        return 1

    # [4] видео на V3
    log(f"[4] place {n_body} clips on V3")
    v3 = seq.videoTracks[PARALLAX_VIDEO_TRACK_IDX]
    placed = 0
    for e in plan:
        if e["is_card"] or e["media"] is None:
            continue
        item = import_media(e["media"])
        if item is None:
            log(f"    [fail import] {e['id']}"); continue
        _throttle(); place_clip(v3, item, e["start"]); placed += 1
        if placed % 25 == 0:
            log(f"    ...{placed} placed")
            if not health_check(f"place-{placed}"):
                return 1
    log(f"    placed {placed} on V3")

    # [4b] тема-плашки на V4
    log(f"[4b] place topic cards on V{TOPIC_CARD_TRACK_IDX+1}")
    v4 = seq.videoTracks[TOPIC_CARD_TRACK_IDX]
    for e in plan:
        if not e.get("topic_mov"):
            continue
        item = import_media(e["topic_mov"])
        if item is None:
            continue
        _throttle(); place_clip(v4, item, e["start"])
    health_check("after-topics")

    # [4c] звук печатной машинки на A4
    log(f"[4c] typing sfx on A{TYPING_SFX_TRACK_IDX+1}")
    a4 = seq.audioTracks[TYPING_SFX_TRACK_IDX]
    for e in plan:
        if not e.get("sfx_wav"):
            continue
        it = import_media(e["sfx_wav"])
        if it is None:
            continue
        _throttle(); place_clip(a4, it, e["sfx_start"])
        clip = find_clip_by_timeline_start(a4, e["sfx_start"], tol=0.5)
        if clip is not None:
            set_clip_volume(clip, TYPING_SFX_VOLUME)
    health_check("after-typing")

    # [5] чистим всё после zone_end
    log(f"[5] cleanup past {zone_end:.0f}s")
    for i in range(n_v):
        clear_past_es("videoTracks", i, zone_end)
    for i in range(n_a):
        clear_past_es("audioTracks", i, zone_end)
    health_check("after-cleanup")

    # [6] mute-проход УБРАН: pretrim_fill дропает звук стоков через -an, мьютить нечего.
    # (fallback-клипы без pretrim редки; если у какого-то останется звук — глушим руками.)

    # [7] dip-to-black фейды на V3 — ОДНИМ eval_script (batch), быстро и без вислова
    log("[7] dip-to-black fades on V3 (batch)")
    fade_specs = [{"start": e["start"], "fi": e["fade_in"], "fo": e["fade_out"]}
                  for e in plan if not e["is_card"]]
    r = apply_fades_batch_es(PARALLAX_VIDEO_TRACK_IDX, fade_specs)
    log(f"    {r}")
    health_check("after-fades")

    # [8] убираем длинную музыку A3
    remove_clip_at_es("audioTracks", A3_MUSIC_DELETE_TRACK_IDX, 0.0)

    # [8.5] архивные YouTube-накладки под факты (в мини пропускаем — они раскиданы
    # по всему таймлайну scene_timings и налезли бы в пустую зону L2-L4).
    if MINI_LIMIT_LEVEL >= 0:
        log("[8.5] archive cutaways SKIPPED (mini)")
    else:
        try:
            from services.premiere.archive_clip_placer import place_archive_clips
            n_arch = place_archive_clips(seq, manifest, scene_timings, PROJECT_DIR)
            if n_arch:
                log(f"[8.5] archive cutaways: {n_arch}")
        except Exception as ex:
            log(f"[8.5] archive skipped: {ex}")

    # [8.6] динамические оверлеи (StatPop/NameLabel/KineticPhrase). Требуют заранее
    # отрендеренный overlays_rendered.json (tests/detect_overlays.py + render_overlays.py).
    if MINI_LIMIT_LEVEL >= 0:
        log("[8.6] dynamic overlays SKIPPED (mini)")
    else:
        try:
            import json as _json
            man = PROJECT_DIR / "overlays_rendered.json"
            if man.exists():
                from services.premiere.overlay_placer import place_overlays
                ovs = _json.loads(man.read_text(encoding="utf-8")).get("overlays", [])
                n_ov = place_overlays(seq, ovs, PROJECT_DIR)
                log(f"[8.6] dynamic overlays: {n_ov}")
            else:
                log("[8.6] overlays_rendered.json нет — оверлеи пропущены")
        except Exception as ex:
            log(f"[8.6] overlays skipped: {ex}")

    log("[9] save")
    save_project()
    log(f"DONE — {COPY_PRPROJ.name} собран, играй с начала.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
