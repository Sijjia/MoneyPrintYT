"""EN bespoke-графика Adult Swim под ТАЙМИНГ EN: ARG-блок (ARGSignal, англ. подписи),
Бостон (BreakingAlert, англ.), маскот 038 + аутро-маскот 275 (липсинк под EN-голос).
Рендерит под EN-длительности и подменяет клипы на ОТКРЫТОМ EN-таймлайне. Premiere открыт с EN.
  ../webik-pipeline/.venv/Scripts/python.exe tests/en_graphics_as.py
"""
import json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import pymiere
import tests.mascot_demo as md

PROJECT = ROOT / "projects" / "2026-08-31_aysberg-adult-swim-temnaya-skrytaya-storona-nochnogo-bloka-c_EN"
REMOTION = ROOT / "remotion"
GFX = PROJECT / "assets" / "gfx"
GFX.mkdir(parents=True, exist_ok=True)
VOICE = PROJECT / "assets" / "voice" / "full.mp3"
tps = 254016000000
FPS = 30
V3_IDX = 2

ARG = {
    "scene_188": ("signal", "Hidden sites. Codes. Messages in the night broadcast.", "as://hidden/delilah_signal"),
    "scene_190": ("decode", "New details every week. The ARG kept gaining momentum.", "decrypt: fragment_47 … ok"),
    "scene_191": ("silence", "Then the project suddenly went dark.", "as://feed status: STALLED"),
    "scene_195": ("static", "No announcements. No explanations.", "query: why? -> (no response)"),
    "scene_196": ("terminated", "The ARG's creators were fired in a restructuring.", "creators -> TERMINATED"),
    "scene_197": ("abandoned", "The project lost its team. It was never finished.", "project: unfinished // team=0"),
}


def cstart(c):
    return c.start.seconds if hasattr(c.start, "seconds") else float(c.start.ticks) / tps


def render(comp, props, out, frames):
    props["durationInFrames"] = frames
    pf = REMOTION / f"_en_{out.stem}.json"
    pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")
    r = subprocess.run(f'npx remotion render {comp} "{os.path.relpath(out, REMOTION).replace(os.sep,"/")}" '
                       f'--props="{os.path.relpath(pf, REMOTION).replace(os.sep,"/")}" --codec=h264 --muted --log=error',
                       cwd=str(REMOTION), shell=True, capture_output=True, text=True)
    pf.unlink(missing_ok=True)
    ok = out.exists() and out.stat().st_size > 20000
    if not ok:
        print(f"  ✗ render {comp} {out.name}: {(r.stderr or r.stdout)[-160:]}")
    return ok


def main() -> int:
    al = json.loads((PROJECT / "assets" / "alignment.json").read_text(encoding="utf-8"))["scenes"]
    seq = pymiere.objects.app.project.activeSequence
    v3 = seq.videoTracks[V3_IDX]
    # старты всех клипов ОДНИМ eval_script (иначе 249 медленных pymiere-обращений виснут);
    # ExtendScript без JSON → возвращаем CSV через join
    csv = pymiere.core.eval_script(
        "(function(){var t=app.project.activeSequence.videoTracks[%d],a=[];"
        "for(var i=0;i<t.clips.numItems;i++)a.push(t.clips[i].start.seconds);return a.join(',');})()" % V3_IDX)
    starts = [float(x) for x in csv.split(",") if x.strip()]
    clip_at = {}
    for i, s in enumerate(starts):
        clip_at.setdefault(round(s, 1), i)

    def find(st):
        for d in (0, 0.1, -0.1, 0.2, -0.2, 0.3, -0.3, 0.4, -0.4):
            idx = clip_at.get(round(st + d, 1))
            if idx is not None:
                return v3.clips[idx]
        return None

    def swap(sid, out):
        c = find(al[sid]["start"])
        if c is None:
            print(f"  ✗ {sid}: клип не найден @ {al[sid]['start']:.1f}"); return False
        try:
            c.projectItem.changeMediaPath(str(out.resolve()), True)
            print(f"  ✓ {sid} ← {out.name}", flush=True); return True
        except Exception as e:
            print(f"  ✗ {sid}: swap {str(e)[:50]}"); return False

    # ARG
    for sid, (mode, cap, code) in ARG.items():
        d = al[sid]["end"] - al[sid]["start"]
        out = GFX / f"{sid}_arg_v2.mp4"   # новое имя → обход медиа-кэша при повторной подмене
        if render("ARGSignal", {"mode": mode, "caption": cap, "code": code, "lang": "en"}, out, max(60, round(d * FPS))):
            swap(sid, out)

    # Бостон 036
    d36 = al["scene_036"]["end"] - al["scene_036"]["start"]
    out36 = GFX / "scene_036_alert_v2.mp4"   # новое имя → обход медиа-кэша
    if render("BreakingAlert", {
        "kicker": "BREAKING", "headline": "BOSTON PARALYZED: SUSPICIOUS DEVICES IN 10 CITIES",
        "cities": 10, "reveal": "It was just an ad for an Adult Swim cartoon.",
        "stamp": "IT WAS JUST AN AD", "showMooninite": True, "lang": "en"}, out36, int(d36 * FPS) + 30):
        swap("scene_036", out36)

    # маскот 038 (липсинк под EN-голос) + улика
    d38 = al["scene_038"]["end"] - al["scene_038"]["start"]
    seg = GFX / "seg_038.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{al['scene_038']['start']:.2f}", "-t", f"{d38:.2f}",
                    "-i", str(VOICE), "-ac", "1", "-ar", "22050", str(seg)], capture_output=True)
    mouth38 = md.mouth_track(seg, d38 + 0.2, FPS)
    comp = []
    T = PROJECT / "assets" / "video_stock" / "_trimmed"
    src34 = T / "scene_034.mp4"
    cf = REMOTION / "public" / "mascot" / "as038en_eco.jpg"
    if src34.exists() and md.grab_frame(src34, cf):
        comp = [{"src": "mascot/as038en_eco.jpg", "x": 0.72, "y": 0.36, "w": 640, "from": 12, "to": len(mouth38) - 6}]
    out38 = GFX / "scene_038_mascot.mp4"
    if render("Mascot", {"mouth": mouth38, "position": "left", "scale": 0.95, "jitter": 0.8,
                         "companions": comp, "caption": "The biggest failure — and a symbol of an era.",
                         "accent": "#e11d1d"}, out38, len(mouth38)):
        swap("scene_038", out38)

    # аутро-маскот 275 (без подписи, липсинк под EN)
    start275 = al["scene_275"]["start"]; end277 = al["scene_277"]["end"]
    d_outro = end277 - start275
    sego = GFX / "seg_outro.wav"
    subprocess.run(["ffmpeg", "-y", "-ss", f"{start275:.2f}", "-t", f"{d_outro:.2f}",
                    "-i", str(VOICE), "-ac", "1", "-ar", "22050", str(sego)], capture_output=True)
    mouthO = md.mouth_track(sego, d_outro + 0.2, FPS)
    outO = GFX / "outro_mascot_nocap.mp4"
    if render("Mascot", {"mouth": mouthO, "position": "center", "scale": 1.06, "jitter": 0.8,
                        "caption": "", "accent": "#1fa48a"}, outO, len(mouthO)):
        from services.premiere_template.timeline_ops import import_media, place_clip
        item = import_media(outO)
        if item is not None:
            place_clip(v3, item, start275)
            print("  ✓ scene_275 аутро-маскот уложен", flush=True)

    pymiere.objects.app.project.save()
    print("EN-графика готова, сохранено", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
