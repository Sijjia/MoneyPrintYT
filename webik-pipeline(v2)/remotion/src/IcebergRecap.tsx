import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, Easing } from "remotion";
import { PALETTE, fontFamily } from "./theme";

type Lvl = { n: string; label: string };
export type IcebergRecapProps = { title?: string; levels?: Lvl[]; accent?: string };

// Оригинальный рекап «прошли весь айсберг»: разрез айсберга, ватерлиния, 4 зоны
// глубины. Вниз ползёт светящаяся линия-сканер и подсвечивает уровни по очереди —
// цвет от холодного (верх) к кроваво-красному (дно).
export const IcebergRecap: React.FC<IcebergRecapProps> = ({ title = "", levels = [], accent = PALETTE.red }) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width: W, height: H } = useVideoConfig();
  const n = Math.max(1, levels.length);

  const startF = 24;
  const endF = Math.max(startF + 30, durationInFrames - 34);
  const prog = interpolate(frame, [startF, endF], [0, 1], {
    extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic),
  });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const titleOp = interpolate(frame, [6, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  // геометрия айсберга
  const cx = W * 0.5;
  const tipTop = H * 0.14;
  const waterY = H * 0.30;
  const bottomY = H * 0.95;
  const topHalf = W * 0.085;   // полуширина на ватерлинии
  const maxHalf = W * 0.235;   // самое широкое (чуть ниже воды)
  const botHalf = W * 0.045;   // сужение ко дну
  const wideY = waterY + (bottomY - waterY) * 0.22;
  const zoneH = (bottomY - waterY) / n;
  const scanY = waterY + prog * (bottomY - waterY);

  const berg = [
    [cx, tipTop], [cx - topHalf, waterY], [cx - maxHalf, wideY], [cx - botHalf, bottomY],
    [cx + botHalf, bottomY], [cx + maxHalf, wideY], [cx + topHalf, waterY],
  ].map((p) => p.join(",")).join(" ");

  // цвет зоны по глубине: холодный сталь → кровь
  const zoneColor = (i: number) => {
    const t = n > 1 ? i / (n - 1) : 0;
    const c1 = [86, 122, 150];   // стальной-голубой
    const c2 = [150, 26, 30];    // тёмно-красный
    const c = c1.map((v, k) => Math.round(v + (c2[k] - v) * t));
    return `rgb(${c[0]},${c[1]},${c[2]})`;
  };

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#05070c", opacity: exit, overflow: "hidden" }}>
      {/* холодное свечение из глубины */}
      <AbsoluteFill style={{ background: `radial-gradient(120% 90% at 50% 105%, ${accent}22 0%, rgba(0,0,0,0) 55%)` }} />

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <clipPath id="bergclip"><polygon points={berg} /></clipPath>
          <linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#0b1220" /><stop offset="1" stopColor="#0a1a2b" />
          </linearGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="6" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
        </defs>

        {/* вода ниже ватерлинии */}
        <rect x="0" y={waterY} width={W} height={H - waterY} fill="url(#sky)" opacity={0.55} />
        {/* линия воды */}
        <line x1="0" y1={waterY} x2={W} y2={waterY} stroke="#2a4a66" strokeWidth={2} opacity={0.7} />

        {/* зоны айсберга (клип по форме) */}
        <g clipPath="url(#bergclip)">
          {levels.map((_, i) => {
            const zTop = waterY + i * zoneH;
            const activated = scanY >= zTop + zoneH * 0.35;
            const passing = scanY >= zTop && scanY < zTop + zoneH;
            const base = zoneColor(i);
            const op = activated ? 0.92 : passing ? 0.6 : 0.14;
            return (
              <rect key={i} x={cx - maxHalf} y={zTop} width={maxHalf * 2} height={zoneH + 1}
                fill={base} opacity={op} style={{ transition: "none" }} />
            );
          })}
          {/* верхушка над водой (лёд) */}
          <polygon points={`${cx},${tipTop} ${cx - topHalf},${waterY} ${cx + topHalf},${waterY}`} fill="#cdd8e2" opacity={0.9} />
          {/* разделители зон */}
          {levels.map((_, i) => i > 0 && (
            <line key={"d" + i} x1={cx - maxHalf} y1={waterY + i * zoneH} x2={cx + maxHalf} y2={waterY + i * zoneH}
              stroke="#05070c" strokeWidth={3} opacity={0.5} />
          ))}
        </g>
        {/* контур айсберга */}
        <polygon points={berg} fill="none" stroke="#8fa7bd" strokeWidth={2.5} opacity={0.55} />

        {/* сканер-линия */}
        {prog > 0.001 && prog < 0.999 && (
          <line x1={cx - maxHalf * 1.15} y1={scanY} x2={cx + maxHalf * 1.15} y2={scanY}
            stroke={accent} strokeWidth={3} opacity={0.95} filter="url(#glow)" />
        )}
      </svg>

      {/* заголовок */}
      {title && (
        <div style={{ position: "absolute", top: 54, width: "100%", textAlign: "center", color: PALETTE.cream,
          fontSize: 46, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", opacity: titleOp }}>
          {title}
        </div>
      )}

      {/* подписи уровней — по сторонам, появляются по мере подсветки */}
      {levels.map((lv, i) => {
        const zTop = waterY + i * zoneH;
        const zMid = zTop + zoneH * 0.5;
        const activated = scanY >= zTop + zoneH * 0.35;
        const op = interpolate(activated ? 1 : 0, [0, 1], [0, 1]);
        const left = i % 2 === 0;
        const x = left ? cx - maxHalf - 30 : cx + maxHalf + 30;
        return (
          <div key={"l" + i} style={{ position: "absolute", top: zMid - 26, [left ? "right" : "left"]: W - (left ? x : W - x),
            width: 360, textAlign: left ? "right" : "left",
            transform: `translateX(${op ? 0 : (left ? 24 : -24)}px)`, opacity: op, transition: "none" }}>
            <div style={{ color: accent, fontSize: 26, fontWeight: 800, letterSpacing: 3 }}>УРОВЕНЬ {lv.n}</div>
            <div style={{ color: PALETTE.cream, fontSize: 30, fontWeight: 700, marginTop: 2 }}>{lv.label}</div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};
