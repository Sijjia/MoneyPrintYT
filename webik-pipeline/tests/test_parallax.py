"""Smoke-тест parallax 3D рендера на одном фото."""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from services.visual.parallax import render_parallax_video


# Возьмём фото из demo-проекта
demo_assets = Path(r"C:\Users\aidar\OneDrive\Рабочий стол\automotization-youtube\webik-pipeline\projects\demo-vertical-slice\assets")
images = list(demo_assets.glob("**/*.jpg")) + list(demo_assets.glob("**/*.png"))
if not images:
    print(f"No images found in {demo_assets}")
    sys.exit(1)

img = images[0]
print(f"Using image: {img}")

out = Path(__file__).parent / "preview_parallax.mp4"
t0 = time.time()
ok = render_parallax_video(img, out, duration_sec=4.0)
elapsed = time.time() - t0
print(f"OK={ok}, elapsed={elapsed:.1f}s, output={out} ({out.stat().st_size/1024:.0f} KB)" if ok else f"FAILED in {elapsed:.1f}s")
