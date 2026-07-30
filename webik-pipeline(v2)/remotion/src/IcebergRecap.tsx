import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import { PALETTE, fontFamily } from "./theme";

type Lvl = { n: string; label: string };
export type IcebergRecapProps = { title?: string; levels?: Lvl[]; accent?: string };

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
// детерминированный псевдослучай (без Math.random — чтоб кадры совпадали)
const rnd = (i: number, s: number) => {
  const x = Math.sin(i * 12.9898 + s * 78.233) * 43758.5453;
  return x - Math.floor(x);
};

// Моушн-графика «прошли весь айсберг»: живой фон, световые лучи, всплывающие
// пузыри, айсберг с внутренним свечением, светящийся маркер глубины с хвостом,
// пружинные карточки уровней сталь→кровь. Спуск-камера вглубь.
export const IcebergRecap: React.FC<IcebergRecapProps> = ({ title = "", levels = [], accent = PALETTE.red }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames: D, width: W, height: H } = useVideoConfig();
  const n = Math.max(1, levels.length);

  const appear = interpolate(frame, [0, 22], [0, 1], CLAMP);
  const exit = interpolate(frame, [D - 22, D], [1, 0], CLAMP);
  const opacity = appear * exit;

  // спуск (камера вглубь) — весь массив медленно едет вверх
  const descend = interpolate(frame, [18, D - 26], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });

  // геометрия айсберга
  const cx = W * 0.5;
  const tipTop = H * 0.15;
  const waterY = H * 0.31;
  const bottomY = H * 0.985;
  const topHalf = W * 0.082;
  const maxHalf = W * 0.225;
  const botHalf = W * 0.05;
  const wideY = waterY + (bottomY - waterY) * 0.2;
  const zoneH = (bottomY - waterY) / n;
  const orbY = waterY + descend * (bottomY - waterY);

  // лёгкий «дыхательный» дрейф
  const bob = Math.sin(frame / 22) * 6;
  const camShift = -descend * 40; // параллакс камеры

  const berg = [
    [cx, tipTop], [cx - topHalf, waterY], [cx - maxHalf, wideY], [cx - botHalf, bottomY],
    [cx + botHalf, bottomY], [cx + maxHalf, wideY], [cx + topHalf, waterY],
  ].map((p) => p.join(",")).join(" ");

  const zoneColor = (i: number, a = 1) => {
    const t = n > 1 ? i / (n - 1) : 0;
    const c1 = [70, 116, 150], c2 = [168, 26, 30];
    const c = c1.map((v, k) => Math.round(v + (c2[k] - v) * t));
    return `rgba(${c[0]},${c[1]},${c[2]},${a})`;
  };

  const pulse = 0.5 + 0.5 * Math.sin(frame / 8);

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#04060b", opacity, overflow: "hidden" }}>
      {/* живой фон-градиент */}
      <AbsoluteFill style={{
        background: `radial-gradient(130% 100% at 50% ${8 + descend * 30}%, #0c2036 0%, #060a14 45%, #04060b 100%)`,
      }} />
      <AbsoluteFill style={{
        background: `radial-gradient(120% 80% at 50% 108%, ${accent}${descend > 0.6 ? "33" : "18"} 0%, rgba(0,0,0,0) 55%)`,
      }} />

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <clipPath id="bc"><polygon points={berg} /></clipPath>
          <linearGradient id="ice" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#e6eef6" /><stop offset="0.5" stopColor="#9fb6c9" /><stop offset="1" stopColor="#5b7285" />
          </linearGradient>
          <radialGradient id="orbG"><stop offset="0" stopColor="#fff" /><stop offset="0.4" stopColor={accent} /><stop offset="1" stopColor="rgba(0,0,0,0)" /></radialGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="7" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          <filter id="soft"><feGaussianBlur stdDeviation="2.2" /></filter>
        </defs>

        {/* световые лучи сверху */}
        {[0, 1, 2, 3].map((i) => {
          const rx = cx + (i - 1.5) * W * 0.16;
          const sh = 0.05 + 0.05 * (0.5 + 0.5 * Math.sin(frame / 30 + i));
          return <polygon key={"ray" + i} points={`${rx - 12},0 ${rx + 12},0 ${rx + 90},${H * 0.6} ${rx - 66},${H * 0.6}`}
            fill="#bcd6ef" opacity={sh * appear} filter="url(#soft)" />;
        })}

        {/* всплывающие пузыри (параллакс) */}
        {Array.from({ length: 40 }, (_, i) => {
          const x = rnd(i, 1) * W;
          const spd = 0.5 + rnd(i, 2) * 1.6;
          const size = 2 + rnd(i, 3) * 7;
          const y = (H - ((frame * spd + rnd(i, 4) * H) % (H + 40))) ;
          const op = (0.12 + rnd(i, 5) * 0.35) * appear;
          return <circle key={"bub" + i} cx={x} cy={y} r={size} fill="#9fc4e6" opacity={op} />;
        })}

        <g transform={`translate(0 ${camShift + bob})`}>
          {/* вода */}
          <rect x="0" y={waterY} width={W} height={H - waterY} fill="#0a1a2b" opacity={0.4} />
          <line x1="0" y1={waterY} x2={W} y2={waterY} stroke="#3a6a92" strokeWidth={2} opacity={0.6 + 0.25 * pulse} />

          {/* зоны айсберга */}
          <g clipPath="url(#bc)">
            {levels.map((_, i) => {
              const zTop = waterY + i * zoneH;
              const on = orbY >= zTop + zoneH * 0.4;
              const near = Math.abs(orbY - (zTop + zoneH / 2)) < zoneH * 0.6;
              const op = on ? 0.9 : near ? 0.55 : 0.16;
              const boost = i === n - 1 && on ? 0.12 * pulse : 0;
              return <rect key={i} x={cx - maxHalf} y={zTop} width={maxHalf * 2} height={zoneH + 1}
                fill={zoneColor(i, op + boost)} />;
            })}
            <polygon points={`${cx},${tipTop} ${cx - topHalf},${waterY} ${cx + topHalf},${waterY}`} fill="url(#ice)" opacity={0.95} />
            {levels.map((_, i) => i > 0 && (
              <line key={"d" + i} x1={cx - maxHalf} y1={waterY + i * zoneH} x2={cx + maxHalf} y2={waterY + i * zoneH}
                stroke="#04060b" strokeWidth={3} opacity={0.55} />
            ))}
          </g>
          <polygon points={berg} fill="none" stroke="#9fbdd6" strokeWidth={2.5} opacity={0.5} />

          {/* маркер глубины с хвостом */}
          {descend > 0.001 && descend < 0.999 && (
            <>
              <line x1={cx} y1={waterY} x2={cx} y2={orbY} stroke={accent} strokeWidth={2} opacity={0.4} />
              <circle cx={cx} cy={orbY} r={26} fill="url(#orbG)" opacity={0.9} />
              <circle cx={cx} cy={orbY} r={7} fill="#fff" filter="url(#glow)" />
            </>
          )}
        </g>
      </svg>

      {/* заголовок — kinetic reveal */}
      {title && (
        <div style={{ position: "absolute", top: 52, width: "100%", textAlign: "center", overflow: "hidden" }}>
          <div style={{
            color: PALETTE.cream, fontSize: 48, fontWeight: 800, letterSpacing: 7, textTransform: "uppercase",
            transform: `translateY(${interpolate(frame, [6, 26], [40, 0], CLAMP)}px)`,
            opacity: interpolate(frame, [6, 26], [0, 1], CLAMP),
            textShadow: `0 0 24px ${accent}66`,
          }}>{title}</div>
          <div style={{ height: 3, width: interpolate(frame, [18, 40], [0, 320], CLAMP), margin: "14px auto 0",
            background: `linear-gradient(90deg, rgba(0,0,0,0), ${accent}, rgba(0,0,0,0))` }} />
        </div>
      )}

      {/* карточки уровней — пружинный вылет по мере прохода маркера */}
      {levels.map((lv, i) => {
        const zTop = waterY + i * zoneH + camShift + bob;
        const zMid = zTop + zoneH * 0.5;
        const on = orbY >= waterY + i * zoneH + zoneH * 0.4;
        const s = spring({ frame: frame - (24 + i * ((D - 60) / n)), fps, config: { damping: 14, stiffness: 90 } });
        const sp = on ? s : 0;
        const left = i % 2 === 0;
        const dir = left ? -1 : 1;
        return (
          <div key={"c" + i} style={{
            position: "absolute", top: zMid - 34, [left ? "left" : "right"]: W * 0.5 + maxHalf + 26,
            width: 380, textAlign: left ? "right" : "left",
            transform: `translateX(${(1 - sp) * 60 * dir}px)`, opacity: sp,
          }}>
            <div style={{ display: "inline-flex", flexDirection: "column", alignItems: left ? "flex-end" : "flex-start",
              padding: "12px 20px", borderRadius: 12,
              background: "rgba(10,16,26,0.55)", border: `1px solid ${zoneColor(i, 0.5)}`,
              boxShadow: `0 0 26px ${zoneColor(i, 0.35)}, inset 0 0 20px rgba(0,0,0,0.4)`, backdropFilter: "blur(3px)" }}>
              <div style={{ color: zoneColor(i, 1), fontSize: 22, fontWeight: 800, letterSpacing: 4 }}>УРОВЕНЬ {lv.n}</div>
              <div style={{ color: PALETTE.cream, fontSize: 32, fontWeight: 700, marginTop: 2 }}>{lv.label}</div>
            </div>
          </div>
        );
      })}

      {/* виньетка */}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
