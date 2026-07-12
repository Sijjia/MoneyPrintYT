"""
services/overlays/render_bridge.py
Рендер-мост: overlays.json → прозрачные MOV (ProRes 4444 с альфой) через Remotion.

Для каждого оверлея пишет props в json-файл (чтобы кириллица/₽/$ не ломали
командную строку), зовёт `npx remotion render <composition> <out.mov>` с альфа-
профилем. Пути передаём ОТНОСИТЕЛЬНО папки remotion (в них нет кириллицы —
кириллица только в абсолютном префиксе, его берёт cwd).
"""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List

from core.logger import setup_logger

log = setup_logger("overlay_render")

REMOTION_DIR = Path(__file__).resolve().parents[2] / "remotion"
FPS = 30

# Прозрачный ProRes 4444 (yuva = альфа) — Premiere читает нативно.
ALPHA_ARGS = (
    "--codec=prores --prores-profile=4444 "
    "--pixel-format=yuva444p10le --image-format=png --log=error"
)


def render_overlays(
    overlays: List[dict],
    out_dir: Path,
    *,
    remotion_dir: Path = REMOTION_DIR,
    overwrite: bool = False,
) -> List[dict]:
    """Рендерит каждый оверлей в out_dir/<id>.mov. Возвращает список с полем 'file'."""
    out_dir.mkdir(parents=True, exist_ok=True)
    props_dir = out_dir / "_props"
    props_dir.mkdir(exist_ok=True)

    rendered: List[dict] = []
    for ov in overlays:
        out_mov = out_dir / f"{ov['id']}.mov"
        if out_mov.exists() and out_mov.stat().st_size > 10_000 and not overwrite:
            log.info(f"  {ov['id']}: уже есть, пропуск")
            rendered.append({**ov, "file": str(out_mov)})
            continue

        props = dict(ov.get("props", {}))
        props["bgImage"] = None  # прод → прозрачный фон
        pf = props_dir / f"{ov['id']}.json"
        pf.write_text(json.dumps(props, ensure_ascii=False), encoding="utf-8")

        rel_out = os.path.relpath(out_mov, remotion_dir)
        rel_props = os.path.relpath(pf, remotion_dir)
        cmd = (
            f'npx remotion render {ov["composition"]} "{rel_out}" '
            f'--props="{rel_props}" {ALPHA_ARGS}'
        )
        log.info(f"  рендер {ov['id']} [{ov['type']}] {ov['composition']} → {out_mov.name}")
        r = subprocess.run(
            cmd,
            cwd=str(remotion_dir),
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r.returncode != 0 or not out_mov.exists():
            log.warning(f"  {ov['id']}: рендер упал (rc={r.returncode}): {(r.stderr or '')[-300:]}")
            continue
        rendered.append({**ov, "file": str(out_mov)})

    log.info(f"Отрендерено {len(rendered)}/{len(overlays)} оверлеев в {out_dir}")
    return rendered
