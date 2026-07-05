"""Swap media via pymiere API (Premiere must be running).

Uses ProjectItem.changeMediaPath() — Premiere's own relink mechanism, so
fingerprints stay valid and there is no "Media offline" state.

Requires:
  - Premiere Pro running with the pymiere CEP extension (com.pymiere.link) loaded
  - A project open in Premiere (will be reported)
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pymiere
from pymiere import objects as p


# ---- connection -----------------------------------------------------------

def ensure_premiere_open(open_doc: Path | None = None) -> None:
    """Verify Premiere is reachable; optionally open a specific project."""
    app = p.app
    # Touch a trivial property to force the bridge to connect.
    _ = app.version
    if open_doc is not None:
        current = app.project.path or ""
        if Path(current).resolve() != open_doc.resolve():
            app.openDocument(str(open_doc))


def current_project_path() -> Path | None:
    path = p.app.project.path
    return Path(path) if path else None


# ---- swap -----------------------------------------------------------------

@dataclass
class MediaSwap:
    old_match: str            # substring to find (often a basename)
    new_path: str             # absolute path to replacement
    override_checks: bool = True  # accept mismatched duration / resolution


@dataclass
class SwapReport:
    matched: int              # how many project items were found
    swapped: int              # how many were successfully relinked
    failures: list[str]       # error messages per failed item


def swap_media(swap: MediaSwap, *, ignore_subclips: bool = False) -> SwapReport:
    """Find project items whose media path matches `swap.old_match` and
    relink them to `swap.new_path`. Returns a per-call report."""
    project = p.app.project
    if not Path(swap.new_path).exists():
        return SwapReport(matched=0, swapped=0, failures=[f"new file missing: {swap.new_path}"])

    found = project.rootItem.findItemsMatchingMediaPath(
        swap.old_match,
        1.0 if ignore_subclips else 0.0,
    )
    items = list(found) if found else []
    failures: list[str] = []
    swapped = 0
    for it in items:
        try:
            ok = it.canChangeMediaPath()
            if not ok:
                failures.append(f"canChangeMediaPath()=False for {it.name}")
                continue
            it.changeMediaPath(swap.new_path, swap.override_checks)
            swapped += 1
        except Exception as e:
            failures.append(f"{getattr(it, 'name', '?')}: {e}")
    return SwapReport(matched=len(items), swapped=swapped, failures=failures)


def save_project() -> None:
    p.app.project.save()
