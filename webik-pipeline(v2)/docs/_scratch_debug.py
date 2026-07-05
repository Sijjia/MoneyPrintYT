"""Debug: trace one specific TrackItem through the resolver."""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
xml = open(r"C:\Users\aidar\AppData\Local\Temp\apocalypse.xml", encoding="utf-8").read()


def fb_id(oid, tag=None):
    if tag:
        m = re.search(rf'<{tag} ObjectID="{oid}"[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
        return m.group(1) if m else None
    # without tag, search by ANY tag (greedy)
    m = re.search(rf'<([A-Za-z]+) ObjectID="{oid}"[^>]*>(.*?)</\1>', xml, re.DOTALL)
    return m.group(2) if m else None


# Direct: find VideoClipTrackItem 1998
body_a = fb_id("1998", "VideoClipTrackItem")
print("VideoClipTrackItem 1998 found:", body_a is not None, "len=", len(body_a) if body_a else 0)
# Get SubClip ref
sr = re.search(r'<SubClip[^/]*ObjectRef="(\d+)"', body_a)
print("SubClip ref:", sr.group(1) if sr else None)

# Without explicit tag
body_b = fb_id("1998")
print("generic 1998 found:", body_b is not None)
# print first tag of generic resolution
m = re.search(r'<([A-Za-z]+) ObjectID="1998"', xml)
print("First tag with ObjectID=1998:", m.group(1) if m else None)

# Now sub-clip 2419
sb = fb_id("2419", "SubClip")
print("SubClip 2419 found:", sb is not None)
mu = re.search(r'<MasterClip[^/]*ObjectURef="([0-9a-f-]+)"', sb) if sb else None
print("MasterClip uuid:", mu.group(1) if mu else None)
nm = re.search(r"<Name>([^<]*)</Name>", sb) if sb else None
print("Name:", nm.group(1) if nm else None)
