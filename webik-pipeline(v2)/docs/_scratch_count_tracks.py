"""One-off: count clips/transitions per track in apocalypse.prproj XML."""
import re
import json
import sys

sys.stdout.reconfigure(encoding="utf-8")

with open(r"C:\Users\aidar\AppData\Local\Temp\apocalypse.xml", encoding="utf-8") as f:
    xml = f.read()

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
a_uids = [
    ("A1", "11a63d1d-b3a3-47e1-a082-5ee77c521dec"),
    ("A2", "88138f42-a4f9-4a51-9ade-ce66d9b6c33a"),
    ("A3", "6fc7a851-f9ba-493d-aba1-ac00bf48e457"),
    ("A4", "ccdcfe79-1003-487b-9f3e-d2aac4526af7"),
    ("A5", "cb9dde0b-09f1-4545-a4c4-f84a4a3f39b2"),
    ("A6", "1a6057a8-7735-4ad8-bd89-431b9f811249"),
    ("A7", "f25620de-999b-4240-babb-53f5dfb66bb5"),
    ("A8", "ab930c77-b15f-49db-8ca3-e644fb2c5f7a"),
    ("A9", "3b23b2a3-a6c8-4619-98a4-ee61269573d8"),
    ("A10", "ca1f7277-3a6a-4fe1-b669-30ef7a8e32b4"),
]


def count_in_track(uid, kind):
    m = re.search(rf'<{kind}ClipTrack ObjectUID="{uid}".*?</{kind}ClipTrack>', xml, re.DOTALL)
    if not m:
        return None, None, []
    block = m.group(0)
    cm = re.search(r"<ClipItems[^>]*>.*?</ClipItems>", block, re.DOTALL)
    tm = re.search(r"<TransitionItems[^>]*>.*?</TransitionItems>", block, re.DOTALL)
    n_clips = len(re.findall(r"<TrackItem ", cm.group(0))) if cm else 0
    n_trans = len(re.findall(r"<TrackItem ", tm.group(0))) if tm else 0
    refs = re.findall(r'<TrackItem [^/]*ObjectRef="(\d+)"', cm.group(0)) if cm else []
    return n_clips, n_trans, refs


print("=== VIDEO TRACKS ===")
total = 0
v_refs = {}
for name, uid in v_uids:
    c, t, refs = count_in_track(uid, "Video")
    v_refs[name] = refs
    total += c or 0
    print(f"  {name}: {c} clips, {t} transitions")
print(f"  TOTAL video clips: {total}")

print("=== AUDIO TRACKS ===")
total_a = 0
a_refs = {}
for name, uid in a_uids:
    c, t, refs = count_in_track(uid, "Audio")
    a_refs[name] = refs
    total_a += c or 0
    print(f"  {name}: {c} clips, {t} transitions")
print(f"  TOTAL audio clips: {total_a}")

with open(r"C:\Users\aidar\AppData\Local\Temp\track_refs.json", "w", encoding="utf-8") as f:
    json.dump({"V": v_refs, "A": a_refs}, f)
