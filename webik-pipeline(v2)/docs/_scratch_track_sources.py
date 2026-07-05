"""For each track, resolve TrackItem(OID) → SubClip → MasterClip(UUID) → file path.

Beware: ObjectID is NOT unique across tags in Premiere XML. Always pass tag explicitly.
"""
import re
import sys
import json
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")

XML = r"C:\Users\aidar\AppData\Local\Temp\apocalypse.xml"
with open(XML, encoding="utf-8") as f:
    xml = f.read()

TICK_PER_SEC = 254016000000


def fb_id(oid, tag):
    m = re.search(rf'<{tag} ObjectID="{oid}"[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
    return m.group(1) if m else None


def fb_uid(uuid, tag):
    m = re.search(rf'<{tag} ObjectUID="{uuid}"[^>]*>(.*?)</{tag}>', xml, re.DOTALL)
    return m.group(1) if m else None


def get_objref(body, name):
    m = re.search(rf'<{name}[^/]*ObjectRef="(\d+)"', body)
    return m.group(1) if m else None


def get_objuref(body, name):
    m = re.search(rf'<{name}[^/]*ObjectURef="([0-9a-f-]+)"', body)
    return m.group(1) if m else None


def get_text(body, name):
    m = re.search(rf"<{name}>([^<]*)</{name}>", body)
    return m.group(1) if m else None


# Build MasterClip index: uuid → {name, file}
master_index = {}
for m in re.finditer(r'<MasterClip ObjectUID="([0-9a-f-]+)"[^>]*>(.*?)</MasterClip>', xml, re.DOTALL):
    uid = m.group(1)
    body = m.group(2)
    name = get_text(body, "Name")
    # MasterClip → Clip ObjectRef → look for FilePath in that Clip
    file_ = None
    clip_ref = get_objref(body, "Clip")
    if clip_ref:
        # Clip may be VideoClip or AudioClip
        for ctag in ("VideoClip", "AudioClip"):
            cbody = fb_id(clip_ref, ctag)
            if not cbody:
                continue
            file_ = get_text(cbody, "FilePath") or get_text(cbody, "ActualMediaFilePath")
            if not file_:
                # source ref → MediaSource
                src_ref = get_objref(cbody, "Source")
                if src_ref:
                    for stag in ("VideoMediaSource", "AudioMediaSource"):
                        sbody = fb_id(src_ref, stag)
                        if sbody:
                            file_ = get_text(sbody, "FilePath") or get_text(sbody, "ActualMediaFilePath")
                            if file_:
                                break
            if file_:
                break
    master_index[uid] = {"name": name, "file": file_}

with_file = sum(1 for v in master_index.values() if v["file"])
print(f"[index] {len(master_index)} MasterClips, {with_file} with file path")


def resolve_trackitem(oid, item_tag):
    body = fb_id(oid, item_tag)
    if not body:
        return None
    start = get_text(body, "Start")
    end = get_text(body, "End")
    sub_ref = get_objref(body, "SubClip")
    name = None
    file_ = None
    master_uid = None
    if sub_ref:
        sbody = fb_id(sub_ref, "SubClip")
        if sbody:
            name = get_text(sbody, "Name")
            master_uid = get_objuref(sbody, "MasterClip")
            if master_uid and master_uid in master_index:
                file_ = master_index[master_uid]["file"]
                if not name:
                    name = master_index[master_uid]["name"]

    def to_sec(v):
        try:
            return round(int(v) / TICK_PER_SEC, 3)
        except Exception:
            return None

    return {
        "oid": oid,
        "start_sec": to_sec(start),
        "end_sec": to_sec(end),
        "name": name,
        "file": file_,
        "master_uid": master_uid,
    }


with open(r"C:\Users\aidar\AppData\Local\Temp\track_refs.json", encoding="utf-8") as f:
    refs = json.load(f)

result = {"V": {}, "A": {}}
for kind, item_tag in (("V", "VideoClipTrackItem"), ("A", "AudioClipTrackItem")):
    for track, oids in refs[kind].items():
        items = []
        for oid in oids:
            r = resolve_trackitem(oid, item_tag)
            if r:
                items.append(r)
        result[kind][track] = items
        print(f"\n=== {track} ({len(items)} clips) ===")
        keys = [(i["name"] or "?", i["file"] or "?") for i in items]
        c = Counter(keys)
        for (n, f), cnt in c.most_common(12):
            f_short = f if len(f) <= 60 else f"...{f[-57:]}"
            print(f"  [{cnt:>3}x] name='{n[:50]}' file={f_short}")
        # also show time range
        starts = [i["start_sec"] for i in items if i["start_sec"] is not None]
        ends = [i["end_sec"] for i in items if i["end_sec"] is not None]
        if starts:
            print(f"  range: {min(starts):.1f}s → {max(ends):.1f}s")

with open(r"C:\Users\aidar\AppData\Local\Temp\track_items.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1)
print("\nSaved track_items.json")
