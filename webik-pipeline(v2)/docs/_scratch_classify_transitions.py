"""Classify all 96 VideoTransitionTrackItem instances by type, duration, track."""
import re
import sys
import json
from collections import Counter, defaultdict

sys.stdout.reconfigure(encoding="utf-8")
xml = open(r"C:\Users\aidar\AppData\Local\Temp\apocalypse.xml", encoding="utf-8").read()

TICK = 254016000000


# Build oid → track index from track_refs.json (only ClipItems, not transitions, were captured).
# Re-extract transition refs per track here.
v_uids = [
    ("V1", "88e52f0b-bd9e-4a85-80a0-c7e2ae7d3390"),
    ("V2", "6fde193f-2917-4dc4-860a-cd437584cd9a"),
    ("V3", "54fa466a-cd7b-439a-b78b-2dfa1a4be378"),
    ("V4", "8db03270-a39b-4399-aea0-c1b08f0dc0b9"),
    ("V5", "029f3d10-ab1b-41b1-8d70-e9f2da0cb49b"),
    ("V6", "9099404d-f3a1-4b40-aab7-3593c8c5d47d"),
    ("V7", "39431f8a-58c9-4ff9-bb38-a7f120bece0a"),
    ("V8", "474eac83-ef91-4fda-be31-cec298f12dac"),
]

oid_to_track = {}
for name, uid in v_uids:
    m = re.search(rf'<VideoClipTrack ObjectUID="{uid}".*?</VideoClipTrack>', xml, re.DOTALL)
    if not m:
        continue
    block = m.group(0)
    tm = re.search(r"<TransitionItems[^>]*>.*?</TransitionItems>", block, re.DOTALL)
    if not tm:
        continue
    for oid in re.findall(r'<TrackItem [^/]*ObjectRef="(\d+)"', tm.group(0)):
        oid_to_track[oid] = name


# Now iterate VideoTransitionTrackItem definitions
rows = []
for m in re.finditer(
    r'<VideoTransitionTrackItem ObjectID="(\d+)"[^>]*>(.*?)</VideoTransitionTrackItem>', xml, re.DOTALL
):
    oid = m.group(1)
    body = m.group(2)
    disp = re.search(r"<DisplayName>([^<]*)</DisplayName>", body)
    match = re.search(r"<MatchName>([^<]*)</MatchName>", body)
    start = re.search(r"<Start>(\d+)</Start>", body)
    end = re.search(r"<End>(\d+)</End>", body)
    align = re.search(r"<Alignment>(-?\d+)</Alignment>", body)
    has_out = re.search(r"<HasOutgoingClip>(true|false)</HasOutgoingClip>", body)
    has_in = re.search(r"<HasIncomingClip>(true|false)</HasIncomingClip>", body)
    rev = re.search(r"<Reverse>(true|false)</Reverse>", body)

    s = int(start.group(1)) if start else None
    e = int(end.group(1)) if end else None
    dur = (e - s) / TICK if (s is not None and e is not None) else None
    rows.append(
        {
            "oid": oid,
            "track": oid_to_track.get(oid, "?"),
            "display": disp.group(1) if disp else None,
            "match": match.group(1) if match else None,
            "start_sec": round(s / TICK, 3) if s is not None else None,
            "end_sec": round(e / TICK, 3) if e is not None else None,
            "dur_sec": round(dur, 3) if dur is not None else None,
            "alignment": int(align.group(1)) if align else None,
            "has_outgoing": has_out.group(1) if has_out else None,
            "has_incoming": has_in.group(1) if has_in else None,
            "reverse": rev.group(1) if rev else None,
        }
    )

print(f"=== TOTAL: {len(rows)} VideoTransitionTrackItems ===\n")

# Group by track
by_track = defaultdict(list)
for r in rows:
    by_track[r["track"]].append(r)

print("Per-track counts:")
for t in ("V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "?"):
    if t in by_track:
        print(f"  {t}: {len(by_track[t])}")

print("\nBy DisplayName overall:")
c_disp = Counter(r["display"] for r in rows)
for d, n in c_disp.most_common():
    print(f"  {n:>3}× {d}")

print("\nBy MatchName overall:")
c_match = Counter(r["match"] for r in rows)
for d, n in c_match.most_common():
    print(f"  {n:>3}× {d}")

print("\nDuration distribution (sec):")
durs = [r["dur_sec"] for r in rows if r["dur_sec"] is not None]
c_dur = Counter(durs)
for d, n in sorted(c_dur.items()):
    print(f"  {n:>3}× {d}s")

print("\nAlignment values:")
c_a = Counter(r["alignment"] for r in rows)
for a, n in c_a.most_common():
    sec = a / TICK if a else 0
    print(f"  {n:>3}× alignment={a} ({sec}s)")

print("\nIncoming/Outgoing pattern:")
c_io = Counter((r["has_outgoing"], r["has_incoming"]) for r in rows)
for (o, i), n in c_io.most_common():
    print(f"  {n:>3}× outgoing={o}, incoming={i}")

# Per-track type breakdown
print("\n=== Per-track type x duration ===")
for t in ("V1", "V2", "V3", "V4"):
    if t not in by_track:
        continue
    print(f"\n{t} ({len(by_track[t])} transitions):")
    pair = Counter((r["display"], r["dur_sec"]) for r in by_track[t])
    for (d, dur), n in pair.most_common():
        print(f"  {n:>3}× {d} @ {dur}s")

# Save
with open(r"C:\Users\aidar\AppData\Local\Temp\transitions.json", "w", encoding="utf-8") as f:
    json.dump(rows, f, ensure_ascii=False, indent=1)
print("\nSaved transitions.json")
