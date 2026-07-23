"""Что сейчас лежит на дорожках в первых ~70 секундах (перед постановкой интро)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pymiere
from services.premiere_template import timeline_ops  # noqa: F401  (патчит __del__)
from services.premiere_template.media_swap import ensure_premiere_open

PRPROJ = (Path(__file__).resolve().parent.parent / "projects"
          / "2026-07-04_aysberg-religioznogo-terrora-samye-zhestkie-i-maloizvestnye-"
          / "project_template.prproj")


def main() -> int:
    ensure_premiere_open(PRPROJ)
    seq = pymiere.objects.app.project.activeSequence
    print(f"секвенция: {seq.name}")
    for kind in ("videoTracks", "audioTracks"):
        tracks = getattr(seq, kind)
        for idx in range(tracks.numTracks):
            tr = tracks[idx]
            rows = []
            lo = float(__import__("os").environ.get("LO", "0"))
            hi = float(__import__("os").environ.get("HI", "70"))
            for i in range(tr.clips.numItems):
                c = tr.clips[i]
                s = c.start.seconds
                if lo <= s < hi:
                    rows.append(f"{s:6.2f}-{c.end.seconds:6.2f} {c.name[:46]}")
            if rows:
                label = "V" if kind == "videoTracks" else "A"
                print(f"\n{label}{idx + 1} ({len(rows)} клипов в окне):")
                for r in rows:
                    print("   ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
