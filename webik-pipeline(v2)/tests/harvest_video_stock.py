"""Harvest video stock for iceberg-4-levels-test body scenes.

For each scene with visual.type == "stock_photo":
  1. Pexels Videos (search_query → fallback_query)
  2. Pixabay Videos (search_query → fallback_query)
  3. Skip — leave parallax mp4 as backup

Output: assets/video_stock/scene_NNN.mp4

Uses v1 services from ../webik-pipeline/services/stocks/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

V1_ROOT = Path(__file__).resolve().parent.parent.parent / "webik-pipeline"
sys.path.insert(0, str(V1_ROOT))

# Load v1's .env so v1's settings see PEXELS/PIXABAY keys.
import os
from dotenv import load_dotenv  # type: ignore[import-not-found]
load_dotenv(V1_ROOT / ".env")

from services.stocks.pexels_videos import PexelsVideosClient  # noqa: E402
from services.stocks.pixabay import PixabayClient  # noqa: E402


PROJECT_DIR = Path(__file__).resolve().parent.parent / "projects" / "iceberg-4-levels-test"
SCENES_PATH = PROJECT_DIR / "scenes.json"
OUT_DIR = PROJECT_DIR / "assets" / "video_stock"


def harvest_one(
    pexels: PexelsVideosClient,
    pixabay: PixabayClient,
    scene_id: str,
    query: str,
    fallback: str,
    min_dur: int,
    out_path: Path,
) -> tuple[str, str | None]:
    """Returns (source, path|None)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Try Pexels with primary query
    for q, idx in ((query, 0), (query, 1), (fallback, 0)):
        if not q:
            continue
        try:
            result = pexels.search_and_download(q, out_path, index=idx, min_duration=min_dur, max_duration=30)
            if result:
                return ("pexels", str(result))
        except Exception as e:
            print(f"    [warn] pexels '{q}' idx={idx}: {e}")

    # Pixabay fallback
    for q, idx in ((query, 0), (fallback, 0)):
        if not q:
            continue
        try:
            result = pixabay.search_and_download_video(q, out_path, index=idx, quality="large")
            if result:
                return ("pixabay", str(result))
        except Exception as e:
            print(f"    [warn] pixabay '{q}' idx={idx}: {e}")

    return ("none", None)


def main() -> int:
    if not SCENES_PATH.exists():
        print(f"ERROR: missing {SCENES_PATH}")
        return 1
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    scenes_data = json.loads(SCENES_PATH.read_text(encoding="utf-8"))
    body_scenes = [s for s in scenes_data["scenes"] if s["visual"]["type"] == "stock_photo"]
    print(f"[0] {len(body_scenes)} body scenes need video stock:")
    for s in body_scenes:
        v = s["visual"]
        print(f"    {s['id']}  ({s['duration_sec']}s)  '{v.get('search_query','')}' / '{v.get('fallback_query','')}'")
    print()

    pexels = PexelsVideosClient()
    pixabay = PixabayClient()

    results = {}
    for s in body_scenes:
        sid = s["id"]
        out_path = OUT_DIR / f"{sid}.mp4"

        # Skip if already exists (and is non-trivial size)
        if out_path.exists() and out_path.stat().st_size > 100_000:
            print(f"[skip] {sid}: already have {out_path.name} ({out_path.stat().st_size // 1024} KB)")
            results[sid] = ("existing", str(out_path))
            continue

        v = s["visual"]
        query = v.get("search_query") or ""
        fallback = v.get("fallback_query") or ""
        dur = int(s.get("duration_sec", 5))
        min_dur = max(4, dur - 3)

        print(f"[harvest] {sid}  q='{query}'  fb='{fallback}'  min_dur={min_dur}s")
        source, path = harvest_one(pexels, pixabay, sid, query, fallback, min_dur, out_path)
        results[sid] = (source, path)
        if path:
            size_kb = Path(path).stat().st_size // 1024
            print(f"    ✓ {source}: {Path(path).name} ({size_kb} KB)")
        else:
            print(f"    ✗ FAILED — all sources exhausted, parallax will stay as fallback")

    print()
    print(f"=== Summary ===")
    for sid, (src, path) in results.items():
        status = "OK" if path else "MISS"
        print(f"  {sid}: {status:4s} via {src}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
