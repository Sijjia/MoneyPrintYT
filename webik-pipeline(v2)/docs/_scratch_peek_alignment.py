"""Peek at alignment.json structure for gribov."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

P = r"C:\Users\aidar\OneDrive\Рабочий стол\automotization-youtube\webik-pipeline\projects\2026-05-12_aysberg-gribov\assets\alignment.json"
al = json.load(open(P, encoding="utf-8"))
print("keys:", list(al.keys()))
print()
print("duration:", al["duration"])
print()
scenes = al["scenes"]
print(f"scenes container is {type(scenes).__name__}, len={len(scenes)}")
if isinstance(scenes, dict):
    for k, v in list(scenes.items())[:5]:
        print(f"  {k}: {v}")
else:
    for s in scenes[:5]:
        print(f"  {s}")
print()
print("paused_at_levels:", al.get("paused_at_levels"))
print()
sentences = al.get("sentences", [])
print(f"sentences: {len(sentences)}")
for s in sentences[:3]:
    print(f"  {s}")
