"""High-level timeline operations on an open Premiere project."""
from __future__ import annotations

import json
import time
from pathlib import Path

import pymiere.core
from pymiere import objects as p
from pymiere.wrappers import time_from_seconds


# pymiere's PymiereBaseObject.__del__ fires an HTTP call to localhost:3000 for
# every object that goes out of scope. In loops with many clips this saturates
# the ephemeral TCP port pool (WinError 10048). Disable cleanup — server-side
# garbage accrues but Premiere handles it for the script lifetime.
pymiere.core.PymiereBaseObject.__del__ = lambda self: None  # type: ignore[assignment]

# Tiny delay between successive pymiere HTTP calls to avoid port exhaustion.
_CALL_DELAY = 0.03


def _throttle() -> None:
    time.sleep(_CALL_DELAY)


def clear_track(track) -> int:
    """Remove every clip on the given track via single ExtendScript bulk call."""
    return clear_track_bulk_es("audioTracks", track.id) if hasattr(track, "id") \
        else _legacy_clear_track(track)


def _legacy_clear_track(track) -> int:
    n = track.clips.numItems
    for i in range(n - 1, -1, -1):
        clip = track.clips[i]
        try:
            clip.remove(False, False)
        except Exception as e:
            print(f"[warn] failed to remove clip {i} on track: {e}")
        _throttle()
    return n


def clear_track_es(track_kind: str, track_idx: int) -> int:
    """Bulk-clear ALL clips on a track via single ExtendScript call.

    track_kind: 'videoTracks' or 'audioTracks'
    Returns number of clips removed (parsed from ExtendScript return).
    """
    js = f"""
    var seq = app.project.activeSequence;
    var track = seq.{track_kind}[{track_idx}];
    var removed = 0;
    for (var i = track.clips.numItems - 1; i >= 0; i--) {{
        try {{ track.clips[i].remove(false, false); removed++; }} catch (e) {{}}
    }}
    removed.toString();
    """
    try:
        r = pymiere.core.eval_script(js)
        return int(str(r).strip())
    except Exception as e:
        print(f"[clear_track_es] {track_kind}[{track_idx}] failed: {e}")
        return 0


def clear_track_bulk_es(track_kind: str, track_idx: int) -> int:
    return clear_track_es(track_kind, track_idx)


def clear_zone_es(track_kind: str, track_idx: int, zone_end_sec: float) -> int:
    """Bulk-remove clips with start < zone_end on a track via single ExtendScript call."""
    js = f"""
    var seq = app.project.activeSequence;
    var track = seq.{track_kind}[{track_idx}];
    var ze = {zone_end_sec};
    var removed = 0;
    for (var i = track.clips.numItems - 1; i >= 0; i--) {{
        try {{
            if (track.clips[i].start.seconds < ze - 0.001) {{
                track.clips[i].remove(false, false);
                removed++;
            }}
        }} catch (e) {{}}
    }}
    removed.toString();
    """
    try:
        r = pymiere.core.eval_script(js)
        return int(str(r).strip())
    except Exception as e:
        print(f"[clear_zone_es] {track_kind}[{track_idx}] failed: {e}")
        return 0


def clear_past_es(track_kind: str, track_idx: int, zone_end_sec: float) -> int:
    """Bulk-remove clips with start >= zone_end on a track via single ExtendScript call."""
    js = f"""
    var seq = app.project.activeSequence;
    var track = seq.{track_kind}[{track_idx}];
    var ze = {zone_end_sec};
    var removed = 0;
    for (var i = track.clips.numItems - 1; i >= 0; i--) {{
        try {{
            if (track.clips[i].start.seconds >= ze - 0.001) {{
                track.clips[i].remove(false, false);
                removed++;
            }}
        }} catch (e) {{}}
    }}
    removed.toString();
    """
    try:
        r = pymiere.core.eval_script(js)
        return int(str(r).strip())
    except Exception as e:
        print(f"[clear_past_es] {track_kind}[{track_idx}] failed: {e}")
        return 0


def remove_clip_at_es(track_kind: str, track_idx: int, target_sec: float, tol: float = 0.05) -> bool:
    """Remove first clip on track whose start ≈ target_sec via single ExtendScript call."""
    js = f"""
    var seq = app.project.activeSequence;
    var track = seq.{track_kind}[{track_idx}];
    var ts = {target_sec};
    var tol = {tol};
    var done = 0;
    for (var i = track.clips.numItems - 1; i >= 0; i--) {{
        try {{
            if (Math.abs(track.clips[i].start.seconds - ts) < tol) {{
                track.clips[i].remove(false, false);
                done = 1;
                break;
            }}
        }} catch (e) {{}}
    }}
    done.toString();
    """
    try:
        r = pymiere.core.eval_script(js)
        return int(str(r).strip()) == 1
    except Exception:
        return False


def _find_root_index_by_name(name: str) -> int:
    """Find index of root-bin item by basename via ExtendScript. Returns -1 if not found."""
    name_j = json.dumps(name)
    js = f"""
    var root = app.project.rootItem;
    var found = -1;
    var n = root.children.numItems;
    for (var i = 0; i < n; i++) {{
        if (root.children[i].name === {name_j}) {{ found = i; break; }}
    }}
    found.toString();
    """
    try:
        result = pymiere.core.eval_script(js)
        return int(str(result).strip())
    except Exception:
        return -1


def import_media(file_path: Path) -> object | None:
    """Import a file into the project bin and return its ProjectItem.

    Hybrid: ExtendScript for bin-iteration (fast — server-side loop over 500+
    items), pymiere for the actual importFiles call (ExtendScript importFiles
    silently fails when called from inside eval_script — see project notes).
    Total HTTP calls: 2-3 per import vs 1000+ for naive Python iteration.
    """
    target_name = file_path.name

    # 1. Check existence via server-side loop (1 HTTP)
    idx = _find_root_index_by_name(target_name)
    if idx >= 0:
        return p.app.project.rootItem.children[idx]

    # 2. Import via pymiere (1 HTTP) — ExtendScript importFiles doesn't work inline
    ok = p.app.project.importFiles([str(file_path)], False, p.app.project.rootItem, False)
    if not ok:
        print(f"[import_media] importFiles returned False for {target_name}")
        return None

    # 3. Find the freshly-imported item (1 HTTP)
    idx = _find_root_index_by_name(target_name)
    if idx < 0:
        print(f"[import_media] post-import find failed for {target_name}")
        return None
    return p.app.project.rootItem.children[idx]


def place_clip(track, project_item, start_sec: float, *, overwrite: bool = True) -> None:
    """Place a project item on the given track starting at start_sec."""
    t = time_from_seconds(float(start_sec))
    if overwrite:
        track.overwriteClip(project_item, t)
    else:
        track.insertClip(project_item, t)
