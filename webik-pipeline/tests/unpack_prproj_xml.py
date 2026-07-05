"""Распаковывает .prproj (gzipped XML) и сохраняет XML."""
import gzip
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2]) if len(sys.argv) >= 3 else src.with_suffix(".prproj.xml")

with gzip.open(src, "rb") as f_in:
    with open(dst, "wb") as f_out:
        shutil.copyfileobj(f_in, f_out)

print(f"Wrote {dst} ({dst.stat().st_size:,} bytes)")
