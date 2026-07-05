"""
services/charts/chart_renderer.py
Edit-style анимированные чарты как .mov с alpha-каналом.

Паттерн рендера: PIL (или matplotlib для сложных кейсов) → frames →
ffmpeg ProRes 4444 yuva444p10le. Stage 5 импортирует .mov как обычный
видео-клип на новый трек V8 (см. timeline_builder).

Spec-driven через `ChartSpec` dataclass: scenes.json в Stage 3 (LLM)
генерит spec, Stage 4 рендерит .mov, Stage 5 кладёт на V8.

Поддерживаемые типы (на 2026-05-11):
- counter        — число растёт от 0 до target с easing + ударом в конце
- percentage_donut — кольцо заполняется до N% (контраст «3% знают / 97% нет»)
- rank_bar       — горизонтальный bar-chart с подсвеченным таргетом

Планы (TODO): timeline_bar, map_arrow, iceberg_pyramid (более сложные).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Tuple

import ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from core.logger import setup_logger

log = setup_logger("chart_renderer")

FPS = 30
DEFAULT_FONT_PATHS = [
    r"C:\Windows\Fonts\impact.ttf",
    r"C:\Windows\Fonts\bahnschrift.ttf",
    r"C:\Windows\Fonts\seguibl.ttf",
    r"C:\Windows\Fonts\ariblk.ttf",
]


# ───── shared utils ─────

def _resolve_font(size: int) -> ImageFont.FreeTypeFont:
    for fp in DEFAULT_FONT_PATHS:
        try:
            return ImageFont.truetype(fp, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _ease_out_cubic(p: float) -> float:
    """Замедление к концу — типичный edit-стиль (быстрый старт, мягкая остановка)."""
    return 1 - (1 - p) ** 3


def _ease_out_back(p: float) -> float:
    """С небольшим overshoot в конце — даёт «удар» когда счётчик доходит до цели."""
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (p - 1) ** 3 + c1 * (p - 1) ** 2


def _format_number(value: float, fmt: str) -> str:
    """Форматирует число под подпись.

    fmt: "int" | "int_thousands" | "float1" | "percent"
    """
    if fmt == "percent":
        return f"{int(round(value))}%"
    if fmt == "float1":
        return f"{value:.1f}"
    if fmt == "int_thousands":
        return f"{int(round(value)):,}".replace(",", " ")
    return f"{int(round(value))}"


def _ffmpeg_writer(out_path: Path, frame_w: int, frame_h: int):
    """Запускает ProRes 4444 alpha writer, который читает rawvideo с pipe."""
    return (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgba", s=f"{frame_w}x{frame_h}", r=FPS)
        .output(
            str(out_path),
            vcodec="prores_ks", pix_fmt="yuva444p10le",
            **{"profile:v": "4"},
        )
        .overwrite_output()
        .global_args("-loglevel", "error")
        .run_async(pipe_stdin=True, pipe_stderr=True)
    )


def _write_frames(process, frames_iter, expected_bytes: int) -> None:
    """Безопасно пишет кадры в pipe — с проверкой размера буфера."""
    try:
        for f_idx, frame in enumerate(frames_iter):
            buf = np.array(frame).tobytes()
            if len(buf) != expected_bytes:
                log.warning(f"frame {f_idx}: buf size mismatch — подменяю на пустой")
                buf = b"\x00" * expected_bytes
            process.stdin.write(buf)
        process.stdin.close()
        rc = process.wait()
        if rc != 0:
            stderr = (process.stderr.read() or b"").decode("utf-8", errors="replace")[:500]
            raise RuntimeError(f"ffmpeg exit={rc} stderr={stderr}")
    except Exception as e:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.kill()
        except Exception:
            pass
        stderr = ""
        try:
            stderr = (process.stderr.read() or b"").decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        raise RuntimeError(f"chart render failed: {e} | stderr={stderr}") from e


# ───── chart specs ─────

@dataclass
class ChartSpec:
    """Параметры одного чарта. LLM в Stage 3 заполняет, Stage 4 рендерит."""
    kind: str  # counter | percentage_donut | rank_bar | timeline_bar | map_arrow | iceberg_pyramid
    duration_sec: float = 4.0              # total длительность клипа (включая hold/fade)
    label: str = ""                        # подпись под цифрой/чартом
    sublabel: str = ""                     # вторая строка (опционально)
    color: str = "#ffffff"                 # основной цвет (hex)
    accent_color: str = "#ff5050"          # акцентный цвет (для подсветки)
    # counter:
    counter_target: float = 0.0
    counter_format: str = "int"            # int|int_thousands|float1|percent
    counter_suffix: str = ""               # «человек», «лет», «$», и т.д.
    # percentage_donut:
    donut_percent: float = 0.0             # 0-100
    # rank_bar:
    rank_items: List[Tuple[str, float]] = field(default_factory=list)  # [("Россия", 50), ("США", 80)]
    rank_highlight_index: int = 0          # какой бар подсвечен (0-based)
    # timeline_bar: список (year_or_label, description). Например [("1953","ОПЕРАЦИЯ"),("1991","РАСКРЫТИЕ")]
    timeline_events: List[Tuple[str, str]] = field(default_factory=list)
    # map_arrow: список ((from_x_pct, from_y_pct), (to_x_pct, to_y_pct), label). Координаты 0-100.
    # Например [((50,40), (80,30), "США→Япония")]. Подложку фона генерим из gradient.
    map_arrows: List[Tuple[Tuple[float, float], Tuple[float, float], str]] = field(default_factory=list)
    map_origin_label: str = ""             # центральная точка (источник распространения)
    # iceberg_pyramid: список уровней сверху вниз. Текущий level подсвечивается accent.
    iceberg_levels: List[str] = field(default_factory=list)
    iceberg_current_level: int = 0         # 1-based: 1 = topmost layer; 0 = no highlight


# ───── counter ─────

def _render_counter_frame(
    spec: ChartSpec, value: float, alpha: float,
    frame_w: int, frame_h: int,
    big_font: ImageFont.FreeTypeFont, label_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01:
        return img
    d = ImageDraw.Draw(img)

    # Anchor по ФИНАЛЬНОМУ значению — иначе каждый кадр recenter и цифры
    # «съезжают» когда ширина строки меняется (1 → 12 → 1247 → "1 247").
    final_text = _format_number(spec.counter_target, spec.counter_format) + spec.counter_suffix
    final_bbox = d.textbbox((0, 0), final_text, font=big_font)
    final_tw = final_bbox[2] - final_bbox[0]
    # Correct vertical centering: median between bbox.top и bbox.bottom
    anchor_x = (frame_w - final_tw) // 2 - final_bbox[0]
    anchor_y = int(frame_h * 0.45) - (final_bbox[1] + final_bbox[3]) // 2

    text = _format_number(value, spec.counter_format) + spec.counter_suffix
    color = _hex_to_rgba(spec.accent_color, int(255 * alpha))
    d.text((anchor_x, anchor_y), text, font=big_font, fill=color)

    if spec.label:
        lb = spec.label.upper()
        lbbox = d.textbbox((0, 0), lb, font=label_font)
        lw = lbbox[2] - lbbox[0]
        lx = (frame_w - lw) // 2 - lbbox[0]
        # Под числом, фиксированный отступ от bottom of ФИНАЛЬНОГО числа
        ly = anchor_y + final_bbox[3] + 36
        d.text((lx, ly), lb, font=label_font, fill=_hex_to_rgba("#ffffff", int(255 * alpha)))
    return img


def _hex_to_rgba(hex_color: str, a: int = 255) -> tuple:
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (r, g, b, a)


def render_counter(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    """Счётчик: число растёт 0 → target за ~70% длительности, потом hold + fade."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    big_font = _resolve_font(280)
    label_font = _resolve_font(56)

    total = spec.duration_sec
    grow = total * 0.6
    hold = total * 0.25
    fade = total - grow - hold
    n_frames = int(round(total * FPS))

    target = float(spec.counter_target)

    log.info(f"  chart counter: target={target} {spec.counter_format} dur={total:.2f}s frames={n_frames}")

    process = _ffmpeg_writer(out_path, frame_w, frame_h)

    def gen():
        for i in range(n_frames):
            t = i / FPS
            if t < grow:
                p = _ease_out_back(t / max(0.001, grow))
                value = max(0.0, target * p)
                alpha = 1.0
            elif t < grow + hold:
                value = target
                alpha = 1.0
            else:
                value = target
                fp = (t - grow - hold) / max(0.001, fade)
                alpha = max(0.0, 1.0 - fp)
            yield _render_counter_frame(spec, value, alpha, frame_w, frame_h, big_font, label_font)

    _write_frames(process, gen(), frame_w * frame_h * 4)
    return out_path, total


# ───── percentage donut ─────

def _render_donut_frame(
    spec: ChartSpec, percent_visible: float, alpha: float,
    frame_w: int, frame_h: int,
    big_font: ImageFont.FreeTypeFont, label_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01:
        return img
    d = ImageDraw.Draw(img)

    cx, cy = frame_w // 2, int(frame_h * 0.42)
    radius = int(min(frame_w, frame_h) * 0.18)
    thickness = int(radius * 0.18)

    track_color = _hex_to_rgba("#3a3a3a", int(180 * alpha))
    fill_color = _hex_to_rgba(spec.accent_color, int(255 * alpha))

    # Background ring
    d.ellipse(
        [cx - radius, cy - radius, cx + radius, cy + radius],
        outline=track_color, width=thickness,
    )
    # Filled arc (start at 12 o'clock, clockwise)
    if percent_visible > 0.5:
        sweep = 360.0 * (percent_visible / 100.0)
        d.arc(
            [cx - radius, cy - radius, cx + radius, cy + radius],
            start=-90, end=-90 + sweep,
            fill=fill_color, width=thickness,
        )

    # Center text
    txt = _format_number(percent_visible, "percent")
    bbox = d.textbbox((0, 0), txt, font=big_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(
        (cx - tw // 2 - bbox[0], cy - th // 2 - bbox[1]),
        txt, font=big_font, fill=_hex_to_rgba("#ffffff", int(255 * alpha)),
    )

    if spec.label:
        lb = spec.label.upper()
        lbbox = d.textbbox((0, 0), lb, font=label_font)
        lw = lbbox[2] - lbbox[0]
        lx = (frame_w - lw) // 2 - lbbox[0]
        ly = cy + radius + 32
        d.text((lx, ly), lb, font=label_font, fill=_hex_to_rgba("#ffffff", int(255 * alpha)))
    return img


def render_percentage_donut(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    """Donut: кольцо заполняется от 0 до donut_percent с ease-out, hold, fade."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    big_font = _resolve_font(180)
    label_font = _resolve_font(56)

    total = spec.duration_sec
    grow = total * 0.55
    hold = total * 0.30
    fade = total - grow - hold
    n_frames = int(round(total * FPS))

    target = max(0.0, min(100.0, float(spec.donut_percent)))
    log.info(f"  chart donut: {target}% dur={total:.2f}s frames={n_frames}")

    process = _ffmpeg_writer(out_path, frame_w, frame_h)

    def gen():
        for i in range(n_frames):
            t = i / FPS
            if t < grow:
                p = _ease_out_cubic(t / max(0.001, grow))
                value = target * p
                alpha = 1.0
            elif t < grow + hold:
                value = target
                alpha = 1.0
            else:
                value = target
                fp = (t - grow - hold) / max(0.001, fade)
                alpha = max(0.0, 1.0 - fp)
            yield _render_donut_frame(spec, value, alpha, frame_w, frame_h, big_font, label_font)

    _write_frames(process, gen(), frame_w * frame_h * 4)
    return out_path, total


# ───── rank bar ─────

def _render_rank_bar_frame(
    spec: ChartSpec, anim_progress: float, alpha: float,
    frame_w: int, frame_h: int,
    label_font: ImageFont.FreeTypeFont, value_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01:
        return img
    d = ImageDraw.Draw(img)

    items = spec.rank_items
    if not items:
        return img

    n = len(items)
    max_val = max((v for _, v in items), default=1.0) or 1.0

    # Layout: занимаем центральные 60% по горизонтали, нижние 50% по вертикали
    bars_w_max = int(frame_w * 0.6)
    bars_x = (frame_w - bars_w_max) // 2
    bar_h = 56
    gap = 24
    total_h = n * bar_h + (n - 1) * gap
    start_y = (frame_h - total_h) // 2 + int(frame_h * 0.05)

    track_color = _hex_to_rgba("#2a2a2a", int(220 * alpha))
    base_color = _hex_to_rgba(spec.color, int(220 * alpha))
    accent = _hex_to_rgba(spec.accent_color, int(255 * alpha))
    text_color = _hex_to_rgba("#ffffff", int(255 * alpha))

    for i, (name, value) in enumerate(items):
        y = start_y + i * (bar_h + gap)
        # Track
        d.rectangle([bars_x, y, bars_x + bars_w_max, y + bar_h], fill=track_color)
        # Animated fill
        target_w = int(bars_w_max * (value / max_val))
        cur_w = int(target_w * _ease_out_cubic(anim_progress))
        col = accent if i == spec.rank_highlight_index else base_color
        if cur_w > 0:
            d.rectangle([bars_x, y, bars_x + cur_w, y + bar_h], fill=col)
        # Name (left)
        d.text((bars_x + 16, y + 6), name.upper(), font=label_font, fill=text_color)
        # Value (right of bar)
        val_text = _format_number(value, "int")
        d.text((bars_x + cur_w + 16, y + 6), val_text, font=value_font, fill=text_color)
    return img


def render_rank_bar(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    label_font = _resolve_font(36)
    value_font = _resolve_font(36)

    total = spec.duration_sec
    grow = total * 0.5
    hold = total * 0.35
    fade = total - grow - hold
    n_frames = int(round(total * FPS))
    log.info(f"  chart rank_bar: {len(spec.rank_items)} items dur={total:.2f}s")

    process = _ffmpeg_writer(out_path, frame_w, frame_h)

    def gen():
        for i in range(n_frames):
            t = i / FPS
            if t < grow:
                p = t / max(0.001, grow)
                alpha = 1.0
            elif t < grow + hold:
                p = 1.0
                alpha = 1.0
            else:
                p = 1.0
                fp = (t - grow - hold) / max(0.001, fade)
                alpha = max(0.0, 1.0 - fp)
            yield _render_rank_bar_frame(spec, p, alpha, frame_w, frame_h, label_font, value_font)

    _write_frames(process, gen(), frame_w * frame_h * 4)
    return out_path, total


# ───── timeline_bar ─────

def _render_timeline_frame(
    spec: ChartSpec, line_progress: float, alpha: float,
    frame_w: int, frame_h: int,
    year_font: ImageFont.FreeTypeFont, desc_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Линия слева направо + flash на каждой пройденной дате."""
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01 or not spec.timeline_events:
        return img
    d = ImageDraw.Draw(img)

    # Layout: горизонтальная линия в средней трети по вертикали, центральные 70% по горизонтали
    line_y = int(frame_h * 0.55)
    line_x_start = int(frame_w * 0.15)
    line_x_end = int(frame_w * 0.85)
    line_w = line_x_end - line_x_start
    line_thickness = 4

    track_color = _hex_to_rgba("#3a3a3a", int(200 * alpha))
    line_color = _hex_to_rgba(spec.accent_color, int(255 * alpha))
    text_color = _hex_to_rgba("#ffffff", int(255 * alpha))

    # Track (полная серая линия)
    d.rectangle(
        [line_x_start, line_y - line_thickness // 2,
         line_x_end, line_y + line_thickness // 2],
        fill=track_color,
    )
    # Animated bright line
    cur_end = line_x_start + int(line_w * line_progress)
    if cur_end > line_x_start:
        d.rectangle(
            [line_x_start, line_y - line_thickness // 2,
             cur_end, line_y + line_thickness // 2],
            fill=line_color,
        )

    # Маркеры событий: равномерно распределены вдоль линии
    n = len(spec.timeline_events)
    for i, (year, desc) in enumerate(spec.timeline_events):
        x = line_x_start if n == 1 else int(line_x_start + line_w * i / (n - 1))
        # Появляется когда линия дошла до этой точки
        passed = (line_progress * line_w) >= (x - line_x_start)
        if not passed:
            continue
        # Tick: вертикальный штрих + кружок
        d.ellipse([x - 12, line_y - 12, x + 12, line_y + 12], fill=line_color)
        d.ellipse([x - 6, line_y - 6, x + 6, line_y + 6], fill=text_color)

        # Year (выше линии)
        ybox = d.textbbox((0, 0), str(year), font=year_font)
        yw, yh = ybox[2] - ybox[0], ybox[3] - ybox[1]
        d.text((x - yw // 2 - ybox[0], line_y - 56 - yh - ybox[1]),
               str(year), font=year_font, fill=line_color)

        # Description (ниже линии)
        dbox = d.textbbox((0, 0), str(desc).upper(), font=desc_font)
        dw, dh = dbox[2] - dbox[0], dbox[3] - dbox[1]
        d.text((x - dw // 2 - dbox[0], line_y + 36 - dbox[1]),
               str(desc).upper(), font=desc_font, fill=text_color)

    # Header label (если есть)
    if spec.label:
        lb = spec.label.upper()
        lbbox = d.textbbox((0, 0), lb, font=year_font)
        lw = lbbox[2] - lbbox[0]
        d.text(((frame_w - lw) // 2 - lbbox[0], int(frame_h * 0.15)),
               lb, font=year_font, fill=text_color)
    return img


def render_timeline_bar(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    """Timeline bar: линия едет слева направо, на каждой дате tick + flash."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    year_font = _resolve_font(72)
    desc_font = _resolve_font(36)

    total = spec.duration_sec
    grow = total * 0.55
    hold = total * 0.30
    fade = total - grow - hold
    n_frames = int(round(total * FPS))
    log.info(f"  chart timeline_bar: {len(spec.timeline_events)} events dur={total:.2f}s")

    process = _ffmpeg_writer(out_path, frame_w, frame_h)

    def gen():
        for i in range(n_frames):
            t = i / FPS
            if t < grow:
                p = _ease_out_cubic(t / max(0.001, grow))
                alpha = 1.0
            elif t < grow + hold:
                p = 1.0
                alpha = 1.0
            else:
                p = 1.0
                fp = (t - grow - hold) / max(0.001, fade)
                alpha = max(0.0, 1.0 - fp)
            yield _render_timeline_frame(spec, p, alpha, frame_w, frame_h, year_font, desc_font)

    _write_frames(process, gen(), frame_w * frame_h * 4)
    return out_path, total


# ───── iceberg_pyramid ─────

def _render_iceberg_frame(
    spec: ChartSpec, reveal_progress: float, alpha: float,
    frame_w: int, frame_h: int,
    level_font: ImageFont.FreeTypeFont, label_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Iceberg как набор горизонтальных трапециевидных слоёв сверху вниз."""
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01 or not spec.iceberg_levels:
        return img
    d = ImageDraw.Draw(img)

    n = len(spec.iceberg_levels)
    cx = frame_w // 2
    top_y = int(frame_h * 0.18)
    bot_y = int(frame_h * 0.85)
    layer_h = (bot_y - top_y) / n

    # Iceberg shape: треугольник, расширяющийся книзу.
    # Узкий top (10% frame_w), широкий bottom (50% frame_w).
    top_half_w = int(frame_w * 0.05)
    bot_half_w = int(frame_w * 0.25)

    text_color = _hex_to_rgba("#ffffff", int(255 * alpha))
    base_color = _hex_to_rgba("#3a4a5a", int(200 * alpha))   # тёмный сине-серый
    accent = _hex_to_rgba(spec.accent_color, int(230 * alpha))

    # Слой за слоем сверху вниз (равномерно)
    n_revealed = int(n * reveal_progress) + 1
    for i in range(n):
        if i >= n_revealed:
            break
        y_top = top_y + int(layer_h * i)
        y_bot = top_y + int(layer_h * (i + 1))
        # Линейная интерполяция ширины по позиции layer'а
        t_top = i / max(1, n)
        t_bot = (i + 1) / max(1, n)
        hw_top = int(top_half_w + (bot_half_w - top_half_w) * t_top)
        hw_bot = int(top_half_w + (bot_half_w - top_half_w) * t_bot)
        # Polygon trapezoid
        poly = [
            (cx - hw_top, y_top),
            (cx + hw_top, y_top),
            (cx + hw_bot, y_bot),
            (cx - hw_bot, y_bot),
        ]
        is_current = (spec.iceberg_current_level == i + 1)
        fill = accent if is_current else base_color
        # Чуть темнее с глубиной — каждый слой темнее предыдущего
        if not is_current:
            shade = max(20, 80 - i * 12)  # 80, 68, 56, 44...
            fill = (shade, shade + 8, shade + 16, int(220 * alpha))
        d.polygon(poly, fill=fill, outline=_hex_to_rgba("#ffffff", int(40 * alpha)))

        # Текст уровня по центру
        level_text = f"{i + 1}. {spec.iceberg_levels[i].upper()}"
        tbox = d.textbbox((0, 0), level_text, font=level_font)
        tw = tbox[2] - tbox[0]
        text_y = (y_top + y_bot) // 2 - (tbox[3] - tbox[1]) // 2
        # Если ширина слоя слишком мала — кладём текст справа от слоя
        if tw < (hw_bot * 2 - 24):
            d.text((cx - tw // 2 - tbox[0], text_y - tbox[1]), level_text, font=level_font, fill=text_color)
        else:
            d.text((cx + hw_bot + 24, text_y - tbox[1]), level_text, font=level_font, fill=text_color)

    # Label сверху
    if spec.label:
        lb = spec.label.upper()
        lbbox = d.textbbox((0, 0), lb, font=label_font)
        lw = lbbox[2] - lbbox[0]
        d.text(((frame_w - lw) // 2 - lbbox[0], int(frame_h * 0.06)),
               lb, font=label_font, fill=text_color)
    return img


def render_iceberg_pyramid(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    """Iceberg pyramid: слои сверху вниз раскрываются по очереди + подсветка current."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    level_font = _resolve_font(40)
    label_font = _resolve_font(56)

    total = spec.duration_sec
    grow = total * 0.5
    hold = total * 0.4
    fade = total - grow - hold
    n_frames = int(round(total * FPS))
    log.info(f"  chart iceberg_pyramid: {len(spec.iceberg_levels)} levels dur={total:.2f}s")

    process = _ffmpeg_writer(out_path, frame_w, frame_h)

    def gen():
        for i in range(n_frames):
            t = i / FPS
            if t < grow:
                p = _ease_out_cubic(t / max(0.001, grow))
                alpha = 1.0
            elif t < grow + hold:
                p = 1.0
                alpha = 1.0
            else:
                p = 1.0
                fp = (t - grow - hold) / max(0.001, fade)
                alpha = max(0.0, 1.0 - fp)
            yield _render_iceberg_frame(spec, p, alpha, frame_w, frame_h, level_font, label_font)

    _write_frames(process, gen(), frame_w * frame_h * 4)
    return out_path, total


# ───── map_arrow ─────

def _draw_curved_arrow(d: ImageDraw.ImageDraw, x1: int, y1: int, x2: int, y2: int,
                       progress: float, color: tuple, thickness: int = 5) -> Tuple[int, int]:
    """Рисует кривую дугу от (x1,y1) к (x2,y2). progress 0..1.
    Возвращает текущую точку на кривой."""
    # Quadratic bezier через смещение control point вверх от середины
    mx = (x1 + x2) / 2
    my = (y1 + y2) / 2
    # control point чуть выше середины (изгиб «вверх»)
    distance = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
    cx = mx
    cy = my - distance * 0.18

    # Sample N points up to progress
    n = max(20, int(40 * progress))
    pts = []
    for i in range(n + 1):
        t = (i / n) * progress
        # Quadratic bezier
        x = (1 - t) ** 2 * x1 + 2 * (1 - t) * t * cx + t ** 2 * x2
        y = (1 - t) ** 2 * y1 + 2 * (1 - t) * t * cy + t ** 2 * y2
        pts.append((x, y))

    if len(pts) >= 2:
        d.line(pts, fill=color, width=thickness, joint="curve")

    if pts:
        return int(pts[-1][0]), int(pts[-1][1])
    return x1, y1


def _render_map_arrow_frame(
    spec: ChartSpec, anim_progress: float, alpha: float,
    frame_w: int, frame_h: int,
    label_font: ImageFont.FreeTypeFont, header_font: ImageFont.FreeTypeFont,
) -> Image.Image:
    """Тёмный фон + точки локаций + анимированные стрелки от origin."""
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01 or not spec.map_arrows:
        return img
    d = ImageDraw.Draw(img)

    # Тёмный gradient фон (имитация тёмной карты)
    bg_color = _hex_to_rgba("#0a1525", int(200 * alpha))
    d.rectangle([0, 0, frame_w, frame_h], fill=bg_color)
    # Лёгкая «сетка» из точек для атмосферы (опционально, бегло)
    grid_col = _hex_to_rgba("#1a2540", int(80 * alpha))
    for gx in range(60, frame_w, 80):
        for gy in range(60, frame_h, 80):
            d.ellipse([gx - 1, gy - 1, gx + 1, gy + 1], fill=grid_col)

    accent = _hex_to_rgba(spec.accent_color, int(255 * alpha))
    text_color = _hex_to_rgba("#ffffff", int(255 * alpha))
    dim_text = _hex_to_rgba("#cbd5e1", int(220 * alpha))

    # Каждая стрелка — отдельный временной интервал. Распределяем равномерно
    # 0..1 по spec.map_arrows. Каждая стрелка занимает 1/n интервал, рисуется во
    # время своей фазы.
    n = len(spec.map_arrows)
    arrow_dur = 1.0 / n if n > 0 else 1.0

    def pct_to_xy(pct_x: float, pct_y: float) -> Tuple[int, int]:
        return int(frame_w * pct_x / 100.0), int(frame_h * pct_y / 100.0)

    drawn_dots = set()  # (x,y) labels уже нарисованных

    for i, ((fx, fy), (tx, ty), label) in enumerate(spec.map_arrows):
        arrow_start = i * arrow_dur
        arrow_end = (i + 1) * arrow_dur
        if anim_progress < arrow_start:
            continue
        local_p = min(1.0, (anim_progress - arrow_start) / max(0.001, arrow_end - arrow_start))

        x1, y1 = pct_to_xy(fx, fy)
        x2, y2 = pct_to_xy(tx, ty)

        # Origin dot (всегда виден)
        d.ellipse([x1 - 10, y1 - 10, x1 + 10, y1 + 10], fill=accent)
        d.ellipse([x1 - 4, y1 - 4, x1 + 4, y1 + 4], fill=text_color)

        # Animated curved arrow
        end_x, end_y = _draw_curved_arrow(d, x1, y1, x2, y2, local_p, accent, thickness=4)

        # Целевая точка появляется когда стрелка дошла
        if local_p > 0.7:
            d.ellipse([x2 - 10, y2 - 10, x2 + 10, y2 + 10], fill=accent)
            # Label рядом с целью
            lbox = d.textbbox((0, 0), label.upper(), font=label_font)
            lw = lbox[2] - lbox[0]
            d.text((x2 - lw // 2 - lbox[0], y2 + 16 - lbox[1]),
                   label.upper(), font=label_font, fill=dim_text)

    # Origin label
    if spec.map_arrows and spec.map_origin_label:
        (fx, fy), _, _ = spec.map_arrows[0]
        x1, y1 = pct_to_xy(fx, fy)
        ob = d.textbbox((0, 0), spec.map_origin_label.upper(), font=label_font)
        ow = ob[2] - ob[0]
        d.text((x1 - ow // 2 - ob[0], y1 - 36 - ob[1]),
               spec.map_origin_label.upper(), font=label_font, fill=text_color)

    # Header
    if spec.label:
        lb = spec.label.upper()
        lbbox = d.textbbox((0, 0), lb, font=header_font)
        lw = lbbox[2] - lbbox[0]
        d.text(((frame_w - lw) // 2 - lbbox[0], int(frame_h * 0.06)),
               lb, font=header_font, fill=text_color)
    return img


def render_map_arrow(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    """Map+arrows: точки локаций + анимированные curved arrows от origin."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    label_font = _resolve_font(36)
    header_font = _resolve_font(56)

    total = spec.duration_sec
    grow = total * 0.6
    hold = total * 0.30
    fade = total - grow - hold
    n_frames = int(round(total * FPS))
    log.info(f"  chart map_arrow: {len(spec.map_arrows)} arrows dur={total:.2f}s")

    process = _ffmpeg_writer(out_path, frame_w, frame_h)

    def gen():
        for i in range(n_frames):
            t = i / FPS
            if t < grow:
                p = _ease_out_cubic(t / max(0.001, grow))
                alpha = 1.0
            elif t < grow + hold:
                p = 1.0
                alpha = 1.0
            else:
                p = 1.0
                fp = (t - grow - hold) / max(0.001, fade)
                alpha = max(0.0, 1.0 - fp)
            yield _render_map_arrow_frame(spec, p, alpha, frame_w, frame_h, label_font, header_font)

    _write_frames(process, gen(), frame_w * frame_h * 4)
    return out_path, total


# ───── unified entry ─────

def render_chart(spec: ChartSpec, out_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Tuple[Path, float]:
    """Dispatcher по spec.kind."""
    if spec.kind == "counter":
        return render_counter(spec, out_path, frame_w, frame_h)
    if spec.kind == "percentage_donut":
        return render_percentage_donut(spec, out_path, frame_w, frame_h)
    if spec.kind == "rank_bar":
        return render_rank_bar(spec, out_path, frame_w, frame_h)
    if spec.kind == "timeline_bar":
        return render_timeline_bar(spec, out_path, frame_w, frame_h)
    if spec.kind == "iceberg_pyramid":
        return render_iceberg_pyramid(spec, out_path, frame_w, frame_h)
    if spec.kind == "map_arrow":
        return render_map_arrow(spec, out_path, frame_w, frame_h)
    raise ValueError(f"Unknown chart kind: {spec.kind}")
