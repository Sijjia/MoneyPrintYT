"""Assemble iceberg-4-levels-test v2 — video stocks + pause-snapped cuts + Dip to Black on boundaries.

Steps:
  0. Pre-trim body stocks via ffmpeg to exact scene durations (so last clip ends at VO end naturally)
  1. Close any open project, re-copy fresh Apocalypse template, open copy
  2. Clear A1 (40 Апокалипсис.mp3 subclips), place new full.mp3 at 0
  3. In zone 0-ZONE_END: clear V1, V2, V3, V4 (Apocalypse footage / MOGRT)
  4. Place 13 clips on V3 (5 trimmed stocks + 8 parallax)
  5. Cleanup past ZONE_END
  6. Mute audio on V3 clips (video stocks bring their own audio)
  7. Apply Dip to Black opacity fades on 8 boundaries
  8. Remove A3 long music clip
  9. Save

Logging: every print writes a line to LOG_PATH with immediate flush so we can see live progress.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- Live-flushing logger (so we see progress even on hang) -----------------
LOG_PATH = Path(os.environ.get("TEMP", ".")) / "assemble_iceberg_live.log"
_log_file = open(LOG_PATH, "w", encoding="utf-8", buffering=1)  # line-buffered

def log(msg: str = "") -> None:
    line = msg if msg.endswith("\n") else msg + "\n"
    print(line, end="", flush=True)
    _log_file.write(line)
    _log_file.flush()


import pymiere.core  # noqa: E402
from pymiere import objects as p  # noqa: E402

from services.premiere_template.media_swap import (  # noqa: E402
    ensure_premiere_open,
    current_project_path,
    save_project,
)
from services.premiere_template.timeline_ops import (  # noqa: E402
    clear_track_es,
    clear_zone_es,
    clear_past_es,
    remove_clip_at_es,
    import_media,
    place_clip,
    _throttle,
)
from services.text.apocalypse_card import (  # noqa: E402
    render_topic_card_typewriter,
    LEAD_IN_SEC as TW_LEAD_IN,
    TYPE_CPS as TW_CPS,
)


PROJECT_DIR = Path(
    r"C:\Users\aidar\OneDrive\Рабочий стол\automotization-youtube"
    r"\webik-pipeline(v2)\projects\iceberg-4-levels-test"
)
COPY_PRPROJ = PROJECT_DIR / "iceberg-4-levels-test.prproj"
TEMPLATE_PRPROJ = Path(
    r"C:\Users\aidar\OneDrive\Документы\Adobe\Premiere Pro\25.0"
    r"\13 видео-Айсберги-Апокалипсис.prproj"
)
VOICE_PATH = PROJECT_DIR / "assets" / "voice" / "full.mp3"
PARALLAX_DIR = PROJECT_DIR / "assets" / "parallax"
VIDEO_STOCK_DIR = PROJECT_DIR / "assets" / "video_stock"
CARDS_DIR = PROJECT_DIR / "assets" / "level_cards"
SFX_DIR = PROJECT_DIR / "assets" / "sfx"
SCENES_PATH = PROJECT_DIR / "scenes.json"
ALIGNMENT_PATH = PROJECT_DIR / "assets" / "alignment.json"

ZONE_END = 100.0
ZONE_VIDEO_TRACKS_TO_CLEAR = [1, 2, 3]  # V2-V4 (V1 несёт только родную L1)
PARALLAX_VIDEO_TRACK_IDX = 2  # V3
TOPIC_CARD_TRACK_IDX = 3      # V4 — наши .mov плашки тем (печатная машинка)
A3_MUSIC_DELETE_TRACK_IDX = 2  # A3
TICKS = 254016000000

# Тихий звук печатной машинки под темами (тот же, что в Апокалипсисе на A2).
# Кириллица+скобки в имени ломают поиск клипа в бине Premiere → копируем в проект
# под ASCII-именем (typing.wav) и импортируем его.
TYPING_SFX_SRC = Path(
    r"E:\YouTube Webik\Sound\Old Sport SFX Pack\Клавиатура - мышь\клавиатура (печать).wav"
)
TYPING_SFX_TRACK_IDX = 3   # A4 — отдельная дорожка под звук машинки (голос на A1 не трогаем)
TYPING_SFX_VOLUME = 0.12   # ≈ -18 dB — тихо, фоном
TYPING_SFX_TAIL = 0.20     # хвост звука после последней буквы (сек)
TYPING_SFX_FADE = 0.12     # затухание звука в конце (сек)

FADE_SEC = 0.833  # Apocalypse template uses 0.833s = 25 frames @ 30fps for V2-V4

# ПЛАШКИ:
#  - Уровни: родная плашка Апокалипсиса «1 УРОВЕНЬ» (13 комп/3 текста) — она в
#    шаблоне ЕДИНСТВЕННАЯ «чистая» и единственная, что рендерится правильно.
#    Скриптом её не размножить (у графики нет projectItem, copy-команд в API нет),
#    поэтому кладём ТОЛЬКО L1 в первый слот; остальные 3 слота Айдар копипастит
#    руками (Ctrl+C/Ctrl+V) и правит цифры. Родные L2-L4 (14/4) рендерятся чёрными.
#  - Темы: наши .mov (Share Tech Mono, печатная машинка) на V4 — надёжно и видно.
L1_CARD_SRC = 46.43  # старт «1 УРОВЕНЬ» во фреш-копии шаблона (V1)

# Scenes (by id) where the OUTGOING boundary is a fade (Dip to Black at .end)
# i.e. between this scene and the next there's a level or topic transition.
# 003→004, 006→007, 009→010, 012→013 = within-topic hard cuts.
FADE_OUT_SCENES = {
    "scene_001",  # intro → L1 announce (level boundary)
    "scene_002",  # L1 announce → T1.1 announce (topic boundary)
    "scene_004",  # T1.1 body → L2 announce (level boundary)
    "scene_005",  # L2 announce → T2.1 announce (topic boundary)
    "scene_007",  # T2.1 body → L3 announce (level boundary)
    "scene_008",  # L3 announce → T3.1 announce (topic boundary)
    "scene_010",  # T3.1 body → L4 announce (level boundary)
    "scene_011",  # L4 announce → T4.1 announce (topic boundary)
    "scene_013",  # last scene → fade to black at end
}

# Scenes where the INCOMING boundary needs fade-in (mirror set + scene_001 opens from black)
FADE_IN_SCENES = {
    "scene_001",  # opens from black
    "scene_002",
    "scene_003",
    "scene_005",
    "scene_006",
    "scene_008",
    "scene_009",
    "scene_011",
    "scene_012",
}


# ---- inline helpers from v1 services/premiere/effects.py -------------------

def _find_component(clip, name: str):
    for comp in clip.components:
        if comp.displayName.lower() == name.lower():
            return comp
    return None


def _find_property(component, name: str):
    for prop in component.properties:
        if prop.displayName.lower() == name.lower():
            return prop
    return None


def apply_dip_to_black_fade(clip, fade_in_sec=0.0, fade_out_sec=0.0) -> bool:
    """Set Opacity keyframes for fade-in (0→100%) and/or fade-out (100→0%).

    fade_*_sec = 0 → that side is skipped (clip stays at 100%).
    Times are clip-local (relative to inPoint).
    """
    opacity_comp = _find_component(clip, "Opacity")
    if opacity_comp is None:
        return False
    opacity_prop = _find_property(opacity_comp, "Opacity")
    if opacity_prop is None or not opacity_prop.areKeyframesSupported():
        return False
    if not opacity_prop.isTimeVarying():
        opacity_prop.setTimeVarying(True)

    in_sec = clip.inPoint.seconds
    out_sec = clip.outPoint.seconds
    clip_dur = max(0.0, out_sec - in_sec)
    if clip_dur <= 0:
        return False
    max_half = clip_dur / 4.0
    fi = min(fade_in_sec, max_half) if fade_in_sec > 0 else 0.0
    fo = min(fade_out_sec, max_half) if fade_out_sec > 0 else 0.0

    try:
        opacity_prop.removeKeyRange(in_sec, out_sec, True)
    except Exception:
        pass

    if fi > 0:
        opacity_prop.addKey(in_sec)
        opacity_prop.setValueAtKey(in_sec, 0.0, True)
        opacity_prop.addKey(in_sec + fi)
        opacity_prop.setValueAtKey(in_sec + fi, 100.0, True)
    else:
        opacity_prop.addKey(in_sec)
        opacity_prop.setValueAtKey(in_sec, 100.0, True)

    if fo > 0:
        opacity_prop.addKey(out_sec - fo)
        opacity_prop.setValueAtKey(out_sec - fo, 100.0, True)
        opacity_prop.addKey(out_sec)
        opacity_prop.setValueAtKey(out_sec, 0.0, True)
    else:
        opacity_prop.addKey(out_sec)
        opacity_prop.setValueAtKey(out_sec, 100.0, True)
    return True


def mute_linked_audio(clip) -> int:
    """Set Volume.Level=0 on linked audio clip(s). Returns count muted."""
    try:
        linked = clip.getLinkedItems()
    except Exception:
        return 0
    if linked is None:
        return 0
    muted = 0
    n = linked.numItems if hasattr(linked, "numItems") else len(linked)
    for i in range(n):
        try:
            lc = linked[i]
            vol_comp = _find_component(lc, "Volume")
            if vol_comp is None:
                continue
            level_prop = _find_property(vol_comp, "Level")
            if level_prop is None:
                continue
            level_prop.setValue(0.0, True)
            muted += 1
        except Exception:
            continue
    return muted


def set_clip_volume(clip, level_factor: float) -> bool:
    """Ставит Volume.Level на аудиоклипе (1.0 = 0 dB). Returns True если применилось."""
    vol_comp = _find_component(clip, "Volume")
    if vol_comp is None:
        return False
    level_prop = _find_property(vol_comp, "Level")
    if level_prop is None:
        return False
    try:
        level_prop.setValue(float(level_factor), True)
        return True
    except Exception:
        return False


def find_clip_by_timeline_start(track, start_sec: float, tol: float = 0.1):
    for i in range(track.clips.numItems):
        clip = track.clips[i]
        if abs(clip.start.seconds - start_sec) < tol:
            return clip
    return None


# ---- timeline helpers ------------------------------------------------------

def clip_start_sec(clip) -> float:
    return float(clip.start.seconds)


def clear_zone(track, zone_end: float, label: str) -> int:
    n = track.clips.numItems
    removed = 0
    for i in range(n - 1, -1, -1):
        clip = track.clips[i]
        try:
            if clip_start_sec(clip) < zone_end - 1e-3:
                clip.remove(False, False)
                removed += 1
        except Exception as e:
            log(f"  [warn] {label} clip {i}: {e}")
        _throttle()
    return removed


def clear_past(track, zone_end: float, label: str) -> int:
    n = track.clips.numItems
    removed = 0
    for i in range(n - 1, -1, -1):
        clip = track.clips[i]
        try:
            if clip_start_sec(clip) >= zone_end - 1e-3:
                clip.remove(False, False)
                removed += 1
        except Exception as e:
            log(f"  [warn] {label} clip {i}: {e}")
        _throttle()
    return removed


def remove_clip_at(track, target_sec: float, tol: float = 1e-3) -> bool:
    for i in range(track.clips.numItems - 1, -1, -1):
        clip = track.clips[i]
        try:
            if abs(clip_start_sec(clip) - target_sec) < tol:
                clip.remove(False, False)
                return True
        except Exception:
            pass
        _throttle()
    return False


def reset_copy_from_template() -> None:
    cur = current_project_path()
    if cur is not None:
        log(f"    closing open project: {cur.name}")
        p.app.project.closeDocument(False)
        time.sleep(1.0)
    log(f"    overwriting copy from fresh template")
    shutil.copy2(TEMPLATE_PRPROJ, COPY_PRPROJ)
    time.sleep(0.5)
    log(f"    opening fresh copy")
    p.app.openDocument(str(COPY_PRPROJ))
    time.sleep(1.5)
    # Sanity: свежий шаблон Апокалипсиса имеет 40 субклипов VO на A1 и графики на V1.
    # Если открылась старая сборка (copy2 не подменил / Premiere открыл кэш) — стоп.
    try:
        n_a1 = int(pymiere.core.eval_script(
            "app.project.activeSequence.audioTracks[0].clips.numItems;"
        ))
    except Exception as e:
        raise RuntimeError(f"reset: не смог проверить открытый проект: {e}")
    if n_a1 < 30:
        raise RuntimeError(
            f"reset FAILED: открыт НЕ свежий шаблон (A1={n_a1}, ожидалось ~40). "
            f"Закрой проект в Premiere вручную и перезапусти."
        )
    log(f"    sanity OK: A1={n_a1} субклипов (свежий шаблон)")


# ---- ffmpeg pretrim --------------------------------------------------------

TRIMMED_DIR = VIDEO_STOCK_DIR / "_trimmed"


def trim_sfx(src: Path, dst: Path, duration_sec: float, fade_out: float = TYPING_SFX_FADE) -> bool:
    """Обрезает src до duration_sec с затуханием в конце. → pcm wav."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    fade_st = max(0.0, duration_sec - fade_out)
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-t", f"{duration_sec:.3f}",
        "-af", f"afade=t=out:st={fade_st:.3f}:d={fade_out:.3f}",
        "-c:a", "pcm_s16le",
        str(dst),
    ]
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            log(f"    [sfx-trim-fail] {src.name}: {r.stderr[-200:]}")
            return False
    except Exception as e:
        log(f"    [sfx-trim-err] {e}")
        return False
    return dst.exists() and dst.stat().st_size > 0


def pretrim_stock(src: Path, dst: Path, duration_sec: float) -> bool:
    """Re-encode src trimmed to exactly duration_sec. Uses ffmpeg copy if possible."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists() and dst.stat().st_size > 100_000:
        return True
    # Use -c copy first (fast), fall back to re-encode if it fails to start clean
    cmd = [
        "ffmpeg", "-y", "-i", str(src),
        "-t", f"{duration_sec:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        str(dst),
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            log(f"    [ffmpeg-fail] {src.name}: {result.stderr[-300:]}")
            return False
    except subprocess.TimeoutExpired:
        log(f"    [ffmpeg-timeout] {src.name}")
        return False
    return dst.exists() and dst.stat().st_size > 0


# ---- scene plan ------------------------------------------------------------

def build_scene_plan(scenes_list, scene_timings, vo_total_sec, topic_titles=None):
    """For each scene, compute timeline start (snapped to mid-pause)
    and choose media:
      - stock_photo  -> trimmed video stock (fallback parallax)
      - level_card   -> «N УРОВЕНЬ» card .mov  (Apocalypse style, over black)
      - topic_card   -> topic title card .mov  (Apocalypse style, over black)
      - else         -> parallax image
    """
    topic_titles = topic_titles or {}
    plan = []
    sorted_scenes = sorted(
        [(s["id"], s, scene_timings[s["id"]]) for s in scenes_list if s["id"] in scene_timings],
        key=lambda t: t[2]["start"],
    )

    # Cuts at midpoint of pause; first cut = 0.0; ends are filled later.
    cuts = []
    for i, (sid, scene, tim) in enumerate(sorted_scenes):
        if i == 0:
            cut_start = 0.0
        else:
            prev_end = sorted_scenes[i - 1][2]["end"]
            cur_start = tim["start"]
            cut_start = (prev_end + cur_start) / 2.0
        cuts.append(cut_start)

    for i, (sid, scene, tim) in enumerate(sorted_scenes):
        start = cuts[i]
        next_start = cuts[i + 1] if i + 1 < len(cuts) else vo_total_sec
        target_dur = next_start - start  # exact timeline duration of this scene
        vtype = scene["visual"]["type"]
        is_body = vtype == "stock_photo"
        is_level_card = vtype == "level_card"
        is_topic_card = vtype == "topic_card"
        is_card = is_level_card or is_topic_card
        card_level = int(scene.get("level", 0))
        card_kind = "level" if is_level_card else ("topic" if is_topic_card else None)
        card_text = None
        if is_card:
            # Уровни: родная L1 на V1 (place_l1_card), слоты 2-4 — вручную.
            # Темы: наш .mov (печатная машинка) на V4. На V3 ничего → чёрный фон.
            card_text = f"{card_level} УРОВЕНЬ" if is_level_card else topic_titles.get(sid, "")
            media = None
            src_for_pretrim = None
        elif is_body:
            src = VIDEO_STOCK_DIR / f"{sid}.mp4"
            trimmed = TRIMMED_DIR / f"{sid}.mp4"
            if src.exists():
                media = trimmed  # will be created in pretrim step
                src_for_pretrim = src
            else:
                media = next(PARALLAX_DIR.glob(f"{sid}__*.mp4"), None)
                src_for_pretrim = None
        else:
            media = next(PARALLAX_DIR.glob(f"{sid}__*.mp4"), None)
            src_for_pretrim = None
        plan.append({
            "id": sid,
            "section": scene.get("section"),
            "level": scene.get("level"),
            "media": media,
            "src_for_pretrim": src_for_pretrim,
            "target_dur": target_dur,
            "is_body": is_body,
            "is_card": is_card,
            "card_kind": card_kind,
            "card_level": card_level,
            "card_text": card_text,
            "start": start,
            "next_start": next_start,
            # Body-клипы на V3 окружены чёрным (announce-слоты) → fade in+out с обеих сторон.
            # Карты на V1 свой fade несут сами, V3-кейфреймы им не нужны.
            "fade_in": 0.0 if is_card else FADE_SEC,
            "fade_out": 0.0 if is_card else FADE_SEC,
        })
    return plan


def health_check(label: str) -> bool:
    """Lightweight pymiere ping. Returns False if Premiere is unresponsive."""
    try:
        _ = p.app.version
        return True
    except Exception as e:
        log(f"  [HEALTH FAIL @ {label}] {e}")
        return False


def place_l1_card(plan, zone_clear_end: float = 100.0) -> None:
    """Переносит ОДНУ родную плашку «N УРОВЕНЬ» в первый level-слот (V1) и чистит
    ВСЮ остальную родную графику/медиа V1 в зоне [0, zone_clear_end). Слоты уровней
    2-4 остаются пустыми — Айдар копипастит туда L1 руками и правит цифры.

    ВАЖНО (баг-фикс): сначала опознаём клип уровня по офсету L1_CARD_SRC, потом
    удаляем ВСЕ прочие V1-клипы в зоне (в т.ч. родные тема-плашки Апокалипсиса типа
    «ФЕНОМЕН 2012 ГОДА» рядом с нашим слотом — раньше они попадали в защитное окно
    и оставались, сталкиваясь с нашей плашкой), и только затем двигаем уровень в слот.
    """
    level_cards = sorted(
        [e for e in plan if e["is_card"] and e["card_kind"] == "level"],
        key=lambda e: e["start"],
    )
    if not level_cards:
        log("    [warn] в плане нет level-плашек")
        return
    l1 = level_cards[0]
    ts, te = l1["start"], l1["next_start"]
    js = """
    function place(){
      var T=%d; var L=[];
      var v1=app.project.activeSequence.videoTracks[0];
      var src=%f, ts=%f, te=%f, zlim=%f;
      // 1) опознать клип уровня по исходному офсету
      var lvlStart=-1;
      for (var i=0;i<v1.clips.numItems;i++){
        if (v1.clips[i].name=='Graphic' && Math.abs(v1.clips[i].start.seconds-src)<0.4){ lvlStart=v1.clips[i].start.seconds; break; }
      }
      if(lvlStart<0){ return 'MISS L1 src='+src; }
      // 2) удалить ВСЕ прочие клипы V1 в зоне [0,zlim), кроме клипа уровня
      var removed=0;
      for (var i=v1.clips.numItems-1;i>=0;i--){
        var s=v1.clips[i].start.seconds;
        if (s>=zlim) continue;
        if (Math.abs(s-lvlStart)<0.05) continue;   // это наш клип уровня — не трогаем
        try{ v1.clips[i].remove(false,false); removed++; }catch(e){}
      }
      L.push('removed '+removed+' native V1 clips in zone (<'+zlim.toFixed(0)+'s)');
      // 3) переставить клип уровня в наш слот (регион теперь пуст)
      var c=null;
      for (var i=0;i<v1.clips.numItems;i++){ if(Math.abs(v1.clips[i].start.seconds-lvlStart)<0.1){c=v1.clips[i];break;} }
      if(!c){ return L.join('\\n')+'\\nLOST_LEVEL_CLIP'; }
      var tries=0;
      while (Math.abs(c.start.seconds-ts)>0.4 && tries<6){
        var off=ts-c.start.seconds;
        try { c.move((off*T).toString()); } catch(e){ L.push('MOVE_ERR: '+e.message); break; }
        tries++;
      }
      // НЕ обрезаем: у родной MOGRT-плашки уровня своя анимация (влёт→hold→вылет,
      // натурально ~5.3с). Обрезка через c.end ломала рендер (dur≠out-in) → текст
      // мигал и пропадал. Оставляем натуральную длину — хвост перекроет плашка темы.
      var okm = (Math.abs(c.start.seconds-ts)<=0.4) ? 'OK' : 'FAIL';
      L.push('L1 placed -> '+c.start.seconds.toFixed(2)+'-'+c.end.seconds.toFixed(2)+' (natural) tries='+tries+' '+okm);
      return L.join('\\n');
    }
    place();
    """ % (TICKS, L1_CARD_SRC, ts, te, zone_clear_end)
    out = pymiere.core.eval_script(js)
    for line in out.splitlines():
        log(f"    {line}")


def main() -> int:
    log(f"=== LIVE LOG: {LOG_PATH} ===")
    for path in (COPY_PRPROJ, VOICE_PATH, ALIGNMENT_PATH, SCENES_PATH):
        if not path.exists():
            log(f"ERROR missing: {path}")
            return 1

    scenes_data = json.loads(SCENES_PATH.read_text(encoding="utf-8"))
    alignment = json.loads(ALIGNMENT_PATH.read_text(encoding="utf-8"))
    scene_timings = alignment["scenes"]
    vo_total = float(alignment["duration"])

    topic_titles = {
        t["scene_start"]: t["title"]
        for t in scenes_data.get("topics_index", [])
        if t.get("scene_start")
    }
    plan = build_scene_plan(scenes_data["scenes"], scene_timings, vo_total, topic_titles)
    log(f"[0] scene plan ({len(plan)} entries):")
    for e in plan:
        kind = {"level": "LCARD", "topic": "TCARD"}.get(e["card_kind"], "VIDEO" if e["is_body"] else "PRLLX")
        media_name = e["card_text"] if e["is_card"] else (e["media"].name if e["media"] else "MISSING")
        log(f"    {e['id']}  L{e['level']}  {kind}  {e['start']:6.2f}-{e['next_start']:6.2f}s  "
            f"dur={e['target_dur']:5.2f}  fi={e['fade_in']:.2f} fo={e['fade_out']:.2f}  {media_name}")

    # --- Step 0: pretrim body stocks via ffmpeg (no Premiere needed) --------
    log(f"\n[A] ffmpeg pretrim body stocks → {TRIMMED_DIR}")
    TRIMMED_DIR.mkdir(parents=True, exist_ok=True)
    for entry in plan:
        if entry["src_for_pretrim"] is None:
            continue
        src = entry["src_for_pretrim"]
        dst = entry["media"]
        dur = entry["target_dur"]
        ok = pretrim_stock(src, dst, dur)
        log(f"    {entry['id']}  {src.name} → {dst.name}  dur={dur:.2f}s  ok={ok}")
        if not ok and dst.exists() is False:
            # fallback to original (will overrun, but won't crash)
            entry["media"] = src
            log(f"    [fallback] {entry['id']} using untrimmed source")

    # --- Step 0b: рендер плашек тем (.mov, Share Tech Mono, печатная машинка) -
    # Уникальный тег прогона: Premiere держит .mov прошлой сборки залоченными
    # (media cache) → ffmpeg не перезапишет. Пишем в новые имена, старые чистим.
    run_tag = str(int(time.time()))
    log(f"\n[A2] rendering topic typewriter cards → {CARDS_DIR} (tag={run_tag})")
    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    SFX_DIR.mkdir(parents=True, exist_ok=True)
    for old in list(CARDS_DIR.glob("topic_*_tw*.mov")) + list(SFX_DIR.glob("typing_*.wav")):
        try:
            old.unlink()
        except Exception:
            pass  # залочен Premiere — оставляем, имя всё равно уникальное
    for entry in plan:
        if not (entry["is_card"] and entry["card_kind"] == "topic"):
            continue
        title = (entry["card_text"] or "").strip()
        if not title:
            log(f"    [skip] {entry['id']}: пустой заголовок темы")
            continue
        out_mov = CARDS_DIR / f"topic_{entry['id']}_tw_{run_tag}.mov"
        entry["topic_mov"] = None
        entry["sfx_wav"] = None
        entry["sfx_start"] = entry["start"] + TW_LEAD_IN  # звук стартует, когда начинается печать
        # ffmpeg pipe иногда рвётся при быстрых последовательных запусках (Errno 22) → ретрай
        for attempt in range(1, 4):
            try:
                _, dur = render_topic_card_typewriter(title, out_mov, total_target=entry["target_dur"])
                entry["topic_mov"] = out_mov
                log(f"    {entry['id']}  «{title}»  → {out_mov.name}  dur={dur:.2f}s"
                    + (f"  (попытка {attempt})" if attempt > 1 else ""))
                break
            except Exception as e:
                log(f"    [retry {attempt}/3] {entry['id']} topic render: {e}")
                time.sleep(0.5)
        if entry["topic_mov"] is None:
            log(f"    [FAIL] {entry['id']} topic render не удался после 3 попыток")
            continue
        # SFX печатной машинки, обрезанный под длительность набора (звук стихает с буквами)
        if TYPING_SFX_SRC.exists():
            type_dur = len(title.upper()) / max(1.0, TW_CPS)
            sfx_dur = type_dur + TYPING_SFX_TAIL
            sfx_dst = SFX_DIR / f"typing_{entry['id']}_{run_tag}.wav"
            if trim_sfx(TYPING_SFX_SRC, sfx_dst, sfx_dur):
                entry["sfx_wav"] = sfx_dst
                log(f"      sfx → {sfx_dst.name}  dur={sfx_dur:.2f}s")

    # Connect to Premiere
    log(f"\n[B] connecting to Premiere")
    try:
        ensure_premiere_open(None)
    except Exception as e:
        log(f"ERROR connecting to Premiere: {e}")
        return 1
    if not health_check("after-connect"):
        return 1

    log(f"\n[1] reset copy to fresh template")
    reset_copy_from_template()
    if not health_check("after-reset"):
        return 1

    seq = p.app.project.activeSequence
    if seq is None:
        log("ERROR: no active sequence")
        return 1
    n_v = getattr(seq.videoTracks, "numTracks", None) or len(list(seq.videoTracks))
    n_a = getattr(seq.audioTracks, "numTracks", None) or len(list(seq.audioTracks))
    log(f"    sequence: {seq.name}, V={n_v}, A={n_a}")

    # --- Step 1: A1 voice ----------------------------------------------------
    log(f"\n[2] A1 voice swap")
    a1 = seq.audioTracks[0]
    n_cleared = clear_track_es("audioTracks", 0)
    log(f"    cleared A1: {n_cleared} clips (ES bulk)")
    voice_item = import_media(VOICE_PATH)
    if voice_item is None:
        log(f"    ERROR: failed to import {VOICE_PATH.name}")
        return 1
    place_clip(a1, voice_item, 0.0)
    log(f"    placed full.mp3 at 0.0s")
    if not health_check("after-A1"):
        return 1

    # --- Step 1b: родная плашка «1 УРОВЕНЬ» в первый слот (до чистки V1) -------
    log(f"\n[2b] родная плашка L1 → первый level-слот (V1); слоты 2-4 копипастишь сам")
    place_l1_card(plan)
    if not health_check("after-l1-card"):
        return 1

    # --- Step 2: clear video zone (ExtendScript bulk per track) -------------
    log(f"\n[3] clearing video zone 0-{ZONE_END}s on V2-V4 (V1 уже разложен)")
    for idx in ZONE_VIDEO_TRACKS_TO_CLEAR:
        removed = clear_zone_es("videoTracks", idx, ZONE_END)
        log(f"    V{idx+1}: removed {removed} clips (ES bulk)")
    if not health_check("after-clear-zone"):
        return 1

    # --- Step 3: place clips on V3 -------------------------------------------
    log(f"\n[4] placing {len(plan)} clips on V3")
    v3 = seq.videoTracks[PARALLAX_VIDEO_TRACK_IDX]
    for entry in plan:
        if entry["media"] is None:
            log(f"    [skip] {entry['id']}: no media")
            continue
        item = import_media(entry["media"])
        if item is None:
            log(f"    [fail] {entry['id']}: import_media returned None")
            continue
        _throttle()
        place_clip(v3, item, entry["start"])
        log(f"    {entry['id']}  @{entry['start']:6.2f}s  {entry['media'].name}")
        time.sleep(0.1)
    if not health_check("after-place"):
        return 1

    # --- Step 3b: place topic typewriter .mov on V4 -------------------------
    log(f"\n[4b] placing topic cards on V{TOPIC_CARD_TRACK_IDX+1}")
    v_topic = seq.videoTracks[TOPIC_CARD_TRACK_IDX]
    for entry in plan:
        mov = entry.get("topic_mov")
        if not mov:
            continue
        item = import_media(mov)
        if item is None:
            log(f"    [fail] {entry['id']}: import topic mov None")
            continue
        _throttle()
        place_clip(v_topic, item, entry["start"])
        log(f"    {entry['id']}  @{entry['start']:6.2f}s  {mov.name}")
        time.sleep(0.1)
    if not health_check("after-topics"):
        return 1

    # --- Step 3c: звук печатной машинки под темами (A4), синхрон с набором ---
    log(f"\n[4c] звук печатной машинки на A{TYPING_SFX_TRACK_IDX+1} под темами (синхрон с печатью)")
    a_sfx = seq.audioTracks[TYPING_SFX_TRACK_IDX]
    for entry in plan:
        wav = entry.get("sfx_wav")
        if not wav:
            continue
        sfx_item = import_media(wav)
        if sfx_item is None:
            log(f"    [fail] {entry['id']}: import SFX None")
            continue
        _throttle()
        place_clip(a_sfx, sfx_item, entry["sfx_start"])
        clip = find_clip_by_timeline_start(a_sfx, entry["sfx_start"], tol=0.5)
        vol_ok = set_clip_volume(clip, TYPING_SFX_VOLUME) if clip is not None else False
        log(f"    {entry['id']}  @{entry['sfx_start']:6.2f}s  {wav.name}  vol={TYPING_SFX_VOLUME}  ok={vol_ok}")
    if not health_check("after-typing-sfx"):
        return 1

    # --- Step 4: cleanup past ZONE_END (ExtendScript bulk per track) --------
    log(f"\n[5] cleanup past {ZONE_END}s on all tracks (ES bulk)")
    for i in range(n_v):
        removed = clear_past_es("videoTracks", i, ZONE_END)
        if removed:
            log(f"    V{i+1}: removed {removed}")
    for i in range(n_a):
        removed = clear_past_es("audioTracks", i, ZONE_END)
        if removed:
            log(f"    A{i+1}: removed {removed}")
    if not health_check("after-cleanup"):
        return 1

    # --- Step 5: mute audio on V3 clips (video stocks have audio) -----------
    log(f"\n[6] mute linked audio on V3 clips")
    muted_total = 0
    for entry in plan:
        clip = find_clip_by_timeline_start(v3, entry["start"], tol=0.5)
        if clip is None:
            continue
        muted = mute_linked_audio(clip)
        muted_total += muted
        _throttle()
    log(f"    muted {muted_total} linked audio clips")
    if not health_check("after-mute"):
        return 1

    # --- Step 6: apply opacity fades on V3 ----------------------------------
    log(f"\n[7] apply Dip to Black opacity fades on V3")
    for entry in plan:
        if entry["is_card"]:
            continue  # карты на V1 (свой fade), V3-кейфреймов нет
        clip = find_clip_by_timeline_start(v3, entry["start"], tol=0.5)
        if clip is None:
            log(f"    [warn] {entry['id']}: clip not found at {entry['start']:.2f}s")
            continue
        ok = apply_dip_to_black_fade(clip, fade_in_sec=entry["fade_in"], fade_out_sec=entry["fade_out"])
        marker = ""
        if entry["fade_in"] > 0:
            marker += "↑"
        if entry["fade_out"] > 0:
            marker += "↓"
        log(f"    {entry['id']}: fade {marker or '—'}  ok={ok}")
        _throttle()
    if not health_check("after-fades"):
        return 1

    # --- Step 7: remove A3 long music clip (ES) -----------------------------
    if remove_clip_at_es("audioTracks", A3_MUSIC_DELETE_TRACK_IDX, 0.0):
        log(f"\n[8] A3: removed music clip starting at 0.0s")

    # --- Step 8.5: архивные YouTube-накладки, привязанные к сценам -----------
    # No-op если в manifest нет youtube-auto клипов. Полностью guarded — никогда
    # не валит сборку.
    try:
        from services.premiere.archive_clip_placer import place_archive_clips
        _mani_path = PROJECT_DIR / "assets" / "images" / "manifest.json"
        if _mani_path.exists():
            _manifest = json.loads(_mani_path.read_text(encoding="utf-8"))
            _n_arch = place_archive_clips(seq, _manifest, scene_timings, PROJECT_DIR)
            if _n_arch:
                log(f"\n[8.5] archive cutaways placed: {_n_arch}")
    except Exception as _e:
        log(f"[8.5] archive placement skipped: {_e}")

    # --- Save ---------------------------------------------------------------
    log(f"\n[9] saving project")
    save_project()
    log(f"\nDONE — open {COPY_PRPROJ.name} and play from start.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
