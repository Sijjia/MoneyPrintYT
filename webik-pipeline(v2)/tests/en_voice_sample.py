"""Короткие EN-сэмплы диктора для Debik: 3 кандидата (Elliott/Steven/Wayne), eleven_v3, language_code=en.
Пишет sample_<label>.mp3 в проект EN → Айдар слушает и выбирает."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.tts.lumean import LumeanTTS

OUT = Path(__file__).resolve().parent.parent / "projects" / "_en_voice_samples"
OUT.mkdir(parents=True, exist_ok=True)

CANDIDATES = {
    "Elliott": "642gSURPsKb4OdCDpkPc",   # deep English narrative, documentaries
    "Steven": "VMCgCMbBs53ElBxVD4VB",    # deep low-baritone/bass documentary
    "Wayne": "RV8OR7AC0uhWHZnVnmI5",     # deep masculine American baritone
}
SAMPLE = ("DreamWorks. The studio behind Shrek, Kung Fu Panda, and How to Train Your Dragon — "
          "films that shaped a generation. [long pause] But behind the magic lies a darker story. "
          "Buried films. Ruthless decisions. And secrets the studio hoped you would never see.")


def make_en_template(lm, vid, name):
    vs = dict(lm.voice_settings); vs.pop("similarity_boost", None); vs["stability"] = 0.5  # v3: кратно 0.5
    tts = {"mode": "mode_v1", "model_id": "eleven_v3", "voice_id": vid,
           "language_code": "en", "voice_settings": vs}
    body = {"service_key": "elevenlabs", "name": name, "config": {"tts_settings": tts}}
    r = lm._post("/templates", body)
    return (r.get("data") or {}).get("id") or r.get("id")


def main() -> int:
    base = LumeanTTS()
    for label, vid in CANDIDATES.items():
        dst = OUT / f"sample_{label}.mp3"
        if dst.exists() and dst.stat().st_size > 20000:
            print(f"[кэш] {dst.name}"); continue
        try:
            tid = make_en_template(base, vid, f"Debik-EN-{label}")
            lm = LumeanTTS(template_uuid=tid)
            lm.synthesize(SAMPLE, dst, save_alignment=False)
            print(f"  ✓ {label}: {dst.name} (template {tid})", flush=True)
        except Exception as e:
            print(f"  ✗ {label}: {str(e)[:120]}", flush=True)
    print(f"\nсэмплы в {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
