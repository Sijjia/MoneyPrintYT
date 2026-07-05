"""Inspect alignment at 25-28s + neighbours to find the 'choppy' moment Aidar hears."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

P = r"C:\Users\aidar\OneDrive\Рабочий стол\automotization-youtube\webik-pipeline\projects\2026-05-12_aysberg-gribov\assets\alignment.json"
al = json.load(open(P, encoding="utf-8"))

print("=== words spanning 22..30s ===")
for w in al["words"]:
    if w["end"] >= 22 and w["start"] <= 30:
        print(f"  {w['start']:>6.2f} → {w['end']:>6.2f}  ({w['end']-w['start']:.2f}s gap_after_prev=?)  {w['word']!r}")

print("\n=== sentences containing 22..30s ===")
for s in al["sentences"]:
    if s["end"] >= 22 and s["start"] <= 30:
        print(f"  {s['start']:>6.2f} → {s['end']:>6.2f}  ({s['end']-s['start']:.2f}s)  {s['text']!r}")

print("\n=== scenes covering 22..30s ===")
for sid, sc in al["scenes"].items():
    if sc["end"] >= 22 and sc["start"] <= 30:
        print(f"  {sid}  {sc['start']:>6.2f} → {sc['end']:>6.2f}  ({sc['end']-sc['start']:.2f}s)")
        print(f"     actual words: {sc['actual'][:15]}")

# Calculate gaps between consecutive words (silences in TTS output)
print("\n=== gaps between words (only >0.3s) anywhere in file ===")
prev = None
for w in al["words"]:
    if prev is not None:
        gap = w["start"] - prev["end"]
        if gap > 0.3:
            print(f"  gap {gap:.2f}s after {prev['word']!r} @ {prev['end']:.2f}, before {w['word']!r} @ {w['start']:.2f}")
    prev = w
