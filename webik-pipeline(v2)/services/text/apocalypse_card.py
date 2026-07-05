"""
services/text/apocalypse_card.py
Level / topic title cards в стиле видео «Апокалипсис».

Стиль (по разбору референс-видео):
- тонкий гротеск (Bahnschrift / DIN), Light SemiCondensed
- ОДНА строка по центру, ШИРОКИЙ трекинг (разрядка)
- белый текст, числа/акцент — красным
- чистый чёрный фон (alpha), без scale-punch, только мягкий fade

Output: ProRes 4444 .mov (yuva444p10le, alpha), 30fps.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional, Tuple

import ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 30
FADE_IN_SEC = 0.45
HOLD_SEC = 1.6
FADE_OUT_SEC = 0.55

# Layout / look
FONT_PATH = r"C:\Windows\Fonts\bahnschrift.ttf"
FONT_VARIATION = "Light SemiCondensed"
# Share Tech Mono — шрифт родных плашек Апокалипсиса (моноширинный).
# Используется для плашек тем (печатная машинка), чтобы совпадать с уровнями.
SHARE_TECH_MONO = r"C:\Users\aidar\AppData\Local\Microsoft\Windows\Fonts\ShareTechMono-Regular.otf"
FONT_SIZE = 76
TRACKING_EM = 0.34          # межбуквенный трекинг как доля от размера шрифта
WORD_SPACE_EM = 0.55        # доп. ширина пробела между словами
CY_FRAC = 0.47              # вертикальный центр строки
COLOR_WHITE = (240, 240, 240, 255)
COLOR_RED = (196, 40, 40, 255)
MARGIN_FRAC = 0.08          # боковые поля; если текст шире — авто-уменьшаем шрифт

_DIGIT_RUN = re.compile(r"\d+")


def _load_font(size: int, font_path: str = FONT_PATH, variation: Optional[str] = FONT_VARIATION) -> ImageFont.FreeTypeFont:
    f = ImageFont.truetype(font_path, size)
    if variation:
        try:
            f.set_variation_by_name(variation)
        except Exception:
            pass
    return f


def _segments(line: str, red_digits: bool = True) -> List[Tuple[str, Tuple[int, int, int, int]]]:
    """Бьёт строку на сегменты (text, color): цифровые run'ы — красные, остальное белое.

    red_digits=False -> вся строка белая (для плашек уровня «N УРОВЕНЬ»).
    """
    if not red_digits:
        return [(line, COLOR_WHITE)]
    segs: List[Tuple[str, Tuple[int, int, int, int]]] = []
    idx = 0
    for m in _DIGIT_RUN.finditer(line):
        if m.start() > idx:
            segs.append((line[idx:m.start()], COLOR_WHITE))
        segs.append((m.group(), COLOR_RED))
        idx = m.end()
    if idx < len(line):
        segs.append((line[idx:], COLOR_WHITE))
    return segs or [(line, COLOR_WHITE)]


def _layout(line: str, font: ImageFont.FreeTypeFont, tracking: float, word_space: float):
    """Возвращает (chars, total_width). chars = list of (ch, advance)."""
    chars = []
    total = 0.0
    n = len(line)
    for i, ch in enumerate(line):
        w = font.getlength(ch)
        chars.append([ch, w])
        total += w
        if i < n - 1:
            total += word_space if ch == " " else tracking
    return chars, total


def _fit_font(line: str, frame_w: int, font_path: str = FONT_PATH,
              variation: Optional[str] = FONT_VARIATION, tracking_em: float = TRACKING_EM,
              base_size: int = FONT_SIZE):
    """Подбирает размер шрифта так, чтобы строка влезла в кадр с полями."""
    max_w = frame_w * (1.0 - 2 * MARGIN_FRAC)
    size = base_size
    while size > 24:
        font = _load_font(size, font_path, variation)
        tracking = size * tracking_em
        word_space = size * WORD_SPACE_EM
        _, total = _layout(line, font, tracking, word_space)
        if total <= max_w:
            return font, size, tracking, word_space
        size -= 2
    font = _load_font(size, font_path, variation)
    return font, size, size * tracking_em, size * WORD_SPACE_EM


def _render_frame(frame_w, frame_h, line, font, tracking, word_space, alpha: float, red_digits: bool = True) -> Image.Image:
    img = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 0))
    if alpha <= 0.01 or not line:
        return img
    td = ImageDraw.Draw(img)

    segs = _segments(line, red_digits)
    # цвет на каждый символ
    char_colors = []
    for text, color in segs:
        for ch in text:
            char_colors.append(color)

    chars, total = _layout(line, font, tracking, word_space)
    # вертикальное выравнивание по cap-боксу
    asc, desc = font.getmetrics()
    bbox = font.getbbox("УРОВЕНЬ")
    cap_h = bbox[3] - bbox[1]
    cy = int(frame_h * CY_FRAC)
    top = cy - cap_h // 2 - bbox[1]

    x = (frame_w - total) / 2.0
    for i, (ch, adv) in enumerate(chars):
        col = char_colors[i] if i < len(char_colors) else COLOR_WHITE
        if alpha < 1.0:
            col = (col[0], col[1], col[2], int(col[3] * alpha))
        td.text((x, top), ch, font=font, fill=col)
        x += adv + (word_space if ch == " " else tracking)
    return img


def render_apocalypse_card(
    line: str,
    out_path: Path,
    hold_sec: Optional[float] = None,
    frame_w: int = 1920,
    frame_h: int = 1080,
    red_digits: bool = True,
) -> Tuple[Path, float]:
    """Рендерит ProRes 4444 .mov с одной строкой в стиле Апокалипсиса.

    line: текст (UPPERCASE рекомендуется). Цифры авто-красные (red_digits).
    Returns (out_path, total_dur_sec).
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    line = line.upper()
    font, _, tracking, word_space = _fit_font(line, frame_w)

    actual_hold = HOLD_SEC if hold_sec is None else max(0.05, float(hold_sec))
    total_dur = FADE_IN_SEC + actual_hold + FADE_OUT_SEC
    total_frames = int(round(total_dur * FPS))

    process = (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgba", s=f"{frame_w}x{frame_h}", r=FPS)
        .output(str(out_path), vcodec="prores_ks", pix_fmt="yuva444p10le", **{"profile:v": "4"})
        .overwrite_output()
        .global_args("-loglevel", "error")
        .run_async(pipe_stdin=True, pipe_stderr=True)
    )
    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            if t < FADE_IN_SEC:
                alpha = t / FADE_IN_SEC
            elif t < FADE_IN_SEC + actual_hold:
                alpha = 1.0
            else:
                p = (t - FADE_IN_SEC - actual_hold) / max(0.001, FADE_OUT_SEC)
                alpha = max(0.0, 1.0 - p)
            frame = _render_frame(frame_w, frame_h, line, font, tracking, word_space, alpha, red_digits)
            process.stdin.write(np.array(frame).tobytes())
        process.stdin.close()
        process.wait()
    except Exception as e:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.kill()
        except Exception:
            pass
        raise RuntimeError(f"ffmpeg apocalypse-card render failed: {e}") from e
    return out_path, total_dur


def render_level_card_apo(level: int, out_path: Path, hold_sec=None, **kw) -> Tuple[Path, float]:
    """Плашка уровня: «N УРОВЕНЬ» (как в Апокалипсисе, вся строка белая)."""
    return render_apocalypse_card(f"{level} УРОВЕНЬ", out_path, hold_sec=hold_sec, red_digits=False, **kw)


def render_topic_card_apo(title: str, out_path: Path, hold_sec=None, **kw) -> Tuple[Path, float]:
    """Плашка темы: заголовок темы (цифры красным)."""
    return render_apocalypse_card(title, out_path, hold_sec=hold_sec, **kw)


# ----------------------------------------------------------------------------
# Typewriter (печатная машинка) — для плашек тем
# ----------------------------------------------------------------------------

TYPE_CPS = 12.0           # символов в секунду (скорость набора; меньше = медленнее печать)
TW_FONT_SIZE = 76         # базовый кегль тем (умеренный); длинный заголовок ПЕРЕНОСИМ на 2 строки
TW_TRACKING_EM = 0.22     # трекинг для Share Tech Mono (моно уже широкий → меньше)
TW_MAX_LINES = 2          # макс. строк переноса; если не влезает — только тогда уменьшаем шрифт
TW_LINE_GAP_EM = 0.42     # межстрочный интервал как доля кегля
TW_FONT_FLOOR = 44        # ниже этого кегль не опускаем даже при переносе
LEAD_IN_SEC = 0.25        # пауза с мигающим курсором перед набором
TRAIL_HOLD_SEC = 1.4      # держим готовую строку
TYPE_FADE_OUT_SEC = 0.55  # затухание в конце
TYPE_MIN_HOLD_SEC = 0.35  # минимальный hold после набора при подгоне под слот
CURSOR_BLINK_HZ = 2.5     # частота мигания курсора (когда не печатает)
CURSOR_W_EM = 0.10        # ширина курсора как доля размера шрифта
CURSOR_GAP_EM = 0.12      # отступ курсора от последней буквы
TW_BG = (0, 0, 0, 255)    # чёрный НЕПРОЗРАЧНЫЙ фон плашки темы (чтобы не просвечивало фото)


def _draw_run(td, font, chars, char_colors, x_start, top, n_visible, tracking, word_space, alpha):
    """Рисует первые n_visible символов; возвращает x после последнего видимого."""
    x = x_start
    n_visible = max(0, min(n_visible, len(chars)))
    for i in range(n_visible):
        ch, adv = chars[i]
        col = char_colors[i] if i < len(char_colors) else COLOR_WHITE
        if alpha < 1.0:
            col = (col[0], col[1], col[2], int(col[3] * alpha))
        if ch != " ":
            td.text((x, top), ch, font=font, fill=col)
        x += adv + (word_space if ch == " " else tracking)
    # x сейчас «за» последним символом + лишний хвостовой трекинг — откатим его
    if n_visible > 0:
        last_ch = chars[n_visible - 1][0]
        x -= (word_space if last_ch == " " else tracking)
    return x


def _greedy_wrap(words, font, tracking, word_space, max_w):
    """Жадно упаковывает слова в строки шириной <= max_w. Возвращает список строк."""
    lines, cur = [], ""
    for w in words:
        cand = w if not cur else cur + " " + w
        _, total = _layout(cand, font, tracking, word_space)
        if total <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def _wrap_title_lines(line: str, frame_w: int):
    """Подбирает КРУПНЫЙ кегль + перенос заголовка на <= TW_MAX_LINES строк.
    Уменьшаем шрифт только если даже с переносом не влезает. Возвращает
    (lines, font, size, tracking, word_space)."""
    max_w = frame_w * (1.0 - 2 * MARGIN_FRAC)
    words = line.split()
    size = TW_FONT_SIZE
    while size >= TW_FONT_FLOOR:
        font = _load_font(size, SHARE_TECH_MONO, None)
        tracking = size * TW_TRACKING_EM
        word_space = size * WORD_SPACE_EM
        lines = _greedy_wrap(words, font, tracking, word_space, max_w)
        widths_ok = all(_layout(l, font, tracking, word_space)[1] <= max_w for l in lines)
        if len(lines) <= TW_MAX_LINES and widths_ok:
            return lines, font, size, tracking, word_space
        size -= 4
    # пол: последняя попытка на минимальном кегле
    font = _load_font(TW_FONT_FLOOR, SHARE_TECH_MONO, None)
    tracking = TW_FONT_FLOOR * TW_TRACKING_EM
    word_space = TW_FONT_FLOOR * WORD_SPACE_EM
    return _greedy_wrap(words, font, tracking, word_space, max_w), font, TW_FONT_FLOOR, tracking, word_space


def _render_typewriter_frame_ml(frame_w, frame_h, lines, font, size, tracking, word_space,
                                 n_visible, cursor_on, red_digits) -> Image.Image:
    """Кадр печатной машинки на ЧЁРНОМ фоне, многострочный. n_visible — сколько
    символов уже напечатано (сквозной счётчик по всем строкам)."""
    img = Image.new("RGBA", (frame_w, frame_h), TW_BG)
    td = ImageDraw.Draw(img)

    bbox = font.getbbox("УРОВЕНЬ")
    cap_h = bbox[3] - bbox[1]
    line_gap = int(size * TW_LINE_GAP_EM)
    n_lines = len(lines)
    block_h = n_lines * cap_h + (n_lines - 1) * line_gap
    cy = int(frame_h * CY_FRAC)
    block_top = cy - block_h // 2

    consumed = 0
    for li, line in enumerate(lines):
        segs = _segments(line, red_digits)
        char_colors = []
        for text, color in segs:
            for ch in text:
                char_colors.append(color)
        chars, total = _layout(line, font, tracking, word_space)
        top = block_top + li * (cap_h + line_gap) - bbox[1]
        x_start = (frame_w - total) / 2.0
        vis_here = max(0, min(len(line), n_visible - consumed))
        x_after = _draw_run(td, font, chars, char_colors, x_start, top, vis_here, tracking, word_space, 1.0)
        # курсор рисуем на строке, где сейчас идёт набор
        typing_here = (consumed < n_visible <= consumed + len(line))
        if cursor_on and (typing_here or (li == n_lines - 1 and n_visible >= consumed + len(line))):
            cur_w = max(2, int(size * CURSOR_W_EM))
            cur_x = int(x_after + size * CURSOR_GAP_EM) if vis_here > 0 else int(x_start)
            cur_top = block_top + li * (cap_h + line_gap)
            td.rectangle([cur_x, cur_top, cur_x + cur_w, cur_top + cap_h], fill=(230, 230, 230, 255))
        consumed += len(line)
    return img


def render_topic_card_typewriter(
    title: str,
    out_path: Path,
    cps: float = TYPE_CPS,
    cursor: bool = True,
    total_target: Optional[float] = None,
    frame_w: int = 1920,
    frame_h: int = 1080,
    red_digits: bool = True,
) -> Tuple[Path, float]:
    """Плашка темы: печатная машинка + мигающий курсор, КРУПНЫЙ текст с ПЕРЕНОСОМ
    строк на ЧЁРНОМ непрозрачном фоне (не просвечивает нижний слой).

    total_target (сек) — подгоняет длину под слот таймлайна: тянет/жмёт hold, а если
    заголовок длинный и печать не влезает — ускоряет набор (не режет текст, не вылезает
    за слот). Returns (out_path, total_dur_sec)."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    line = title.upper()
    lines, font, size, tracking, word_space = _wrap_title_lines(line, frame_w)
    n_chars = sum(len(l) for l in lines)  # без символов переноса

    eff_cps = max(1.0, cps)
    type_dur = n_chars / eff_cps
    if total_target is not None:
        avail_type = total_target - LEAD_IN_SEC - TYPE_FADE_OUT_SEC - TYPE_MIN_HOLD_SEC
        if type_dur > avail_type and avail_type > 0.1:
            eff_cps = n_chars / avail_type          # ускоряем набор, чтобы влезть в слот
            type_dur = avail_type
        trail_hold = max(TYPE_MIN_HOLD_SEC, total_target - LEAD_IN_SEC - type_dur - TYPE_FADE_OUT_SEC)
    else:
        trail_hold = TRAIL_HOLD_SEC
    total_dur = LEAD_IN_SEC + type_dur + trail_hold + TYPE_FADE_OUT_SEC
    total_frames = int(round(total_dur * FPS))

    process = (
        ffmpeg
        .input("pipe:", format="rawvideo", pix_fmt="rgba", s=f"{frame_w}x{frame_h}", r=FPS)
        .output(str(out_path), vcodec="prores_ks", pix_fmt="yuva444p10le", **{"profile:v": "4"})
        .overwrite_output()
        .global_args("-loglevel", "error")
        .run_async(pipe_stdin=True, pipe_stderr=True)
    )
    try:
        for f_idx in range(total_frames):
            t = f_idx / FPS
            if t < LEAD_IN_SEC:
                n_vis = 0
                typing = False
            elif t < LEAD_IN_SEC + type_dur:
                n_vis = min(n_chars, int((t - LEAD_IN_SEC) * eff_cps) + 1)
                typing = True
            else:
                n_vis = n_chars
                typing = False
            if cursor:
                cursor_on = True if typing else (int(t * CURSOR_BLINK_HZ * 2) % 2 == 0)
            else:
                cursor_on = False
            frame = _render_typewriter_frame_ml(
                frame_w, frame_h, lines, font, size, tracking, word_space,
                n_vis, cursor_on, red_digits,
            )
            process.stdin.write(np.array(frame).tobytes())
        process.stdin.close()
        process.wait()
    except Exception as e:
        try:
            process.stdin.close()
        except Exception:
            pass
        try:
            process.kill()
        except Exception:
            pass
        raise RuntimeError(f"ffmpeg typewriter render failed: {e}") from e
    return out_path, total_dur


def preview_typewriter_png(title: str, png_path: Path, n_visible: int,
                           cursor: bool = True, frame_w: int = 1920, frame_h: int = 1080) -> Path:
    """Статичный кадр печатной машинки на n_visible символах (для превью эффекта)."""
    line = title.upper()
    font, _, tracking, word_space = _fit_font(line, frame_w, SHARE_TECH_MONO, None, TW_TRACKING_EM, TW_FONT_SIZE)
    base = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 255))
    fg = _render_typewriter_frame(frame_w, frame_h, line, font, tracking, word_space,
                                  n_visible, cursor, 1.0, True)
    base.alpha_composite(fg)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(png_path, "JPEG", quality=88)
    return png_path


def preview_png(line: str, png_path: Path, frame_w: int = 1920, frame_h: int = 1080) -> Path:
    """Статичный кадр (на hold) для быстрого визуального сравнения."""
    line_u = line.upper()
    font, _, tracking, word_space = _fit_font(line_u, frame_w)
    # на чёрном фоне, чтобы было видно как в видео
    base = Image.new("RGBA", (frame_w, frame_h), (0, 0, 0, 255))
    fg = _render_frame(frame_w, frame_h, line_u, font, tracking, word_space, 1.0)
    base.alpha_composite(fg)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    base.convert("RGB").save(png_path, "JPEG", quality=88)
    return png_path
