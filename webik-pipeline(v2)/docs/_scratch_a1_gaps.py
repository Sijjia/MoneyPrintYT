"""Check whether A1 segments are butt-joined or have gaps between them."""
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

P = r"C:\Users\aidar\AppData\Local\Temp\track_items.json"
data = json.load(open(P, encoding="utf-8"))
a1 = data["A"]["A1"]
print(f"A1: {len(a1)} clips")
prev_end = 0.0
gaps = []
for i, c in enumerate(a1):
    if c.get("start_sec") is None:
        continue
    gap = c["start_sec"] - prev_end
    gaps.append(gap)
    dur = (c["end_sec"] - c["start_sec"]) if c.get("end_sec") else 0
    print(f"  [{i:>2}] {c['name'][:30]:<30} | start={c['start_sec']:>7.2f}  end={c['end_sec']:>7.2f}  dur={dur:>5.2f}  gap_before={gap:>+6.2f}")
    prev_end = c["end_sec"]

print()
print(f"Total clips: {len(a1)}")
print(f"Gap stats:")
print(f"  butt-joined (gap=0): {sum(1 for g in gaps if abs(g) < 0.01)}")
print(f"  with gap (>0.01s):   {sum(1 for g in gaps if g > 0.01)}")
print(f"  overlap (<-0.01s):   {sum(1 for g in gaps if g < -0.01)}")
print(f"  max gap: {max(gaps):.2f}s")
print(f"  avg gap: {sum(gaps)/len(gaps):.2f}s")
