// Профессиональный слой анимации: физика пружин и безье-кривые из motion.dev (motion),
// но СЭМПЛИРУЕМЫЕ по кадру (детерминированно для Remotion — без requestAnimationFrame).
import { spring as motionSpring, cubicBezier } from "motion";

// Фирменные кривые Motion (чистые функции progress0..1 → eased). Годятся в interpolate({easing}).
export const ease = {
  expoOut: cubicBezier(0.16, 1, 0.3, 1),     // мощный «выброс» и мягкое торможение
  smoothOut: cubicBezier(0.22, 1, 0.36, 1),  // плавно, кинематографично
  backOut: cubicBezier(0.34, 1.56, 0.64, 1), // лёгкий перелёт (overshoot)
  power: cubicBezier(0.4, 0, 0.2, 1),        // material-standard
  inOut: cubicBezier(0.65, 0, 0.35, 1),
};

// Пружина Motion, сэмплированная по кадру → значение (обычно 0..1, может перелетать).
export const mspring = (
  frame: number,
  fps: number,
  opts: { stiffness?: number; damping?: number; mass?: number; delay?: number; from?: number; to?: number } = {}
): number => {
  const { stiffness = 120, damping = 16, mass = 1, delay = 0, from = 0, to = 1 } = opts;
  const t = Math.max(0, (frame - delay) / fps) * 1000; // ms
  const g = motionSpring({ keyframes: [from, to], stiffness, damping, mass, velocity: 0 } as any);
  const v = g.next(t);
  return (v && typeof v.value === "number" ? v.value : to) as number;
};

// Прогресс с кривой Motion: frame из [a,b] → eased 0..1.
export const track = (frame: number, a: number, b: number, easing: (p: number) => number = ease.smoothOut): number => {
  const p = Math.min(1, Math.max(0, (frame - a) / Math.max(1, b - a)));
  return easing(p);
};

// Стаггер: время старта i-го элемента (кадры).
export const stagger = (i: number, start: number, step: number): number => start + i * step;

// Готовый «вход снизу с прояснением» на пружине: {opacity, translateY(px)}.
export const enterUp = (frame: number, fps: number, delay = 0, dist = 40, cfg = { stiffness: 130, damping: 17 }) => {
  const s = mspring(frame, fps, { ...cfg, delay });
  return { opacity: Math.min(1, s), translateY: (1 - s) * dist };
};
