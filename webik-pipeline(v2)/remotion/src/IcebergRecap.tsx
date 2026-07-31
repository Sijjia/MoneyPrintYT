import React from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate, spring, Easing } from "remotion";
import { PALETTE, fontFamily } from "./theme";

type Lvl = { n: string; label: string };
export type IcebergRecapProps = { title?: string; levels?: Lvl[]; accent?: string };

const CLAMP = { extrapolateLeft: "clamp", extrapolateRight: "clamp" } as const;
const rnd = (i: number, s: number) => {
  const x = Math.sin(i * 12.9898 + s * 78.233) * 43758.5453;
  return x - Math.floor(x);
};

// Реалистичный айсберг-рекап: рваный органический силуэт, полупрозрачный лёд с
// гранями/трещинами и бликами, снежная шапка, отражение, подводные каустики,
// лучи, туман, глубинное свечение. Уровни — линии глубины с элегантными подписями.
export const IcebergRecap: React.FC<IcebergRecapProps> = ({ title = "", levels = [], accent = PALETTE.red }) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames: D, width: W, height: H } = useVideoConfig();
  const n = Math.max(1, levels.length);

  const appear = interpolate(frame, [0, 24], [0, 1], CLAMP);
  const exit = interpolate(frame, [D - 22, D], [1, 0], CLAMP);
  const opacity = appear * exit;
  const descend = interpolate(frame, [18, D - 26], [0, 1], { ...CLAMP, easing: Easing.inOut(Easing.cubic) });

  const cx = W * 0.5;
  const tipTop = H * 0.13;
  const waterY = H * 0.315;
  const bottomY = H * 0.99;
  const orbY = waterY + descend * (bottomY - waterY);
  const bob = Math.sin(frame / 26) * 5;
  const pulse = 0.5 + 0.5 * Math.sin(frame / 9);

  // полуширина айсберга по глубине t (0=верхушка,1=дно)
  const halfW = (t: number) => {
    const surf = 0.30 * (t < 0.185 ? t / 0.185 : 1);          // над водой узко
    const under = t < 0.185 ? 0 : Math.sin(((t - 0.185) / 0.815) * Math.PI * 0.62 + 0.12);
    return W * (0.055 + surf * 0.05 + under * 0.20);
  };
  const yAt = (t: number) => tipTop + t * (bottomY - tipTop);

  // рваные края (детерминированный джиттер, стабильный по кадрам)
  const STEPS = 26;
  const leftPts: [number, number][] = [];
  const rightPts: [number, number][] = [];
  for (let k = 0; k <= STEPS; k++) {
    const t = k / STEPS;
    const y = yAt(t);
    const hw = halfW(t);
    const jL = (rnd(k, 1) - 0.5) * (t < 0.185 ? 26 : 46);
    const jR = (rnd(k, 2) - 0.5) * (t < 0.185 ? 26 : 46);
    leftPts.push([cx - hw + jL, y]);
    rightPts.push([cx + hw + jR, y]);
  }
  const bergPath =
    "M " + leftPts.map((p) => p.join(",")).join(" L ") +
    " L " + rightPts.slice().reverse().map((p) => p.join(",")).join(" L ") + " Z";
  const waterlineHW = halfW(0.185);

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#030509", opacity, overflow: "hidden" }}>
      {/* небо/воздух над водой */}
      <AbsoluteFill style={{ background: `linear-gradient(180deg, #0a1826 0%, #0d2434 ${waterY / H * 100}%, #071824 ${waterY / H * 100}%, #040d16 62%, #05070d 100%)` }} />
      {/* глубинное свечение снизу — усиливается на спуске */}
      <AbsoluteFill style={{ background: `radial-gradient(120% 75% at 50% 112%, ${accent}${descend > 0.55 ? "38" : "16"} 0%, rgba(0,0,0,0) 58%)` }} />

      <svg width={W} height={H} style={{ position: "absolute", inset: 0 }}>
        <defs>
          <linearGradient id="ice" x1="0" y1="0" x2="0.3" y2="1">
            <stop offset="0" stopColor="#f2f9ff" /><stop offset="0.28" stopColor="#cfe6f4" />
            <stop offset="0.6" stopColor="#7fa6bf" /><stop offset="0.85" stopColor="#3f5f76" /><stop offset="1" stopColor="#243d50" />
          </linearGradient>
          <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0" stopColor="#12454f" stopOpacity="0.55" /><stop offset="0.4" stopColor="#0a2333" stopOpacity="0.5" />
            <stop offset="0.8" stopColor="#060f1c" stopOpacity="0.55" /><stop offset="1" stopColor="#0a0407" stopOpacity="0.6" />
          </linearGradient>
          <radialGradient id="orbG"><stop offset="0" stopColor="#fff" /><stop offset="0.35" stopColor={accent} /><stop offset="1" stopColor="rgba(0,0,0,0)" /></radialGradient>
          <filter id="glow"><feGaussianBlur stdDeviation="8" result="b" /><feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge></filter>
          <filter id="soft"><feGaussianBlur stdDeviation="3" /></filter>
          <filter id="blurR"><feGaussianBlur stdDeviation="6" /></filter>
          <clipPath id="waterclip"><rect x="0" y={waterY} width={W} height={H - waterY} /></clipPath>
        </defs>

        {/* вода */}
        <rect x="0" y={waterY} width={W} height={H - waterY} fill="url(#water)" />

        {/* световые лучи из-под поверхности */}
        <g clipPath="url(#waterclip)">
          {[0, 1, 2, 3, 4].map((i) => {
            const rx = cx + (i - 2) * W * 0.15 + Math.sin(frame / 40 + i) * 20;
            const sh = (0.05 + 0.06 * (0.5 + 0.5 * Math.sin(frame / 34 + i * 1.7))) * appear;
            return <polygon key={"ray" + i} points={`${rx - 14},${waterY} ${rx + 14},${waterY} ${rx + 120},${H * 0.82} ${rx - 92},${H * 0.82}`}
              fill="#bfe0f2" opacity={sh} filter="url(#soft)" />;
          })}
          {/* каустики — волнистые линии света у поверхности */}
          {[0, 1, 2, 3].map((i) => {
            const y = waterY + 30 + i * 46;
            const d = Array.from({ length: 20 }, (_, k) => {
              const x = (k / 19) * W;
              const yy = y + Math.sin(frame / 12 + k * 0.6 + i) * 7;
              return `${k === 0 ? "M" : "L"} ${x},${yy}`;
            }).join(" ");
            return <path key={"ca" + i} d={d} stroke="#9fd6ee" strokeWidth={1.5} fill="none" opacity={0.10 * appear} filter="url(#soft)" />;
          })}
          {/* планктон/частицы */}
          {Array.from({ length: 46 }, (_, i) => {
            const x = rnd(i, 1) * W;
            const spd = 0.3 + rnd(i, 2) * 1.3;
            const size = 1 + rnd(i, 3) * 3.2;
            const y = waterY + ((rnd(i, 4) * (H - waterY) - frame * spd) % (H - waterY) + (H - waterY)) % (H - waterY);
            const op = (0.10 + rnd(i, 5) * 0.32) * appear;
            const dx = Math.sin(frame / 30 + i) * 4;
            return <circle key={"p" + i} cx={x + dx} cy={y} r={size} fill="#a9cfe6" opacity={op} />;
          })}
        </g>

        {/* линия воды + пена */}
        <line x1="0" y1={waterY} x2={W} y2={waterY} stroke="#4a86a0" strokeWidth={2.5} opacity={0.55 + 0.2 * pulse} />
        <path d={Array.from({ length: 40 }, (_, k) => { const x = (k / 39) * W; const yy = waterY + Math.sin(frame / 10 + k * 0.5) * 2.2; return `${k === 0 ? "M" : "L"} ${x},${yy}`; }).join(" ")}
          stroke="#cdeaf5" strokeWidth={1.2} fill="none" opacity={0.28} />

        {/* отражение верхушки в воде */}
        <g clipPath="url(#waterclip)" opacity={0.16}>
          <g transform={`translate(${Math.sin(frame / 18) * 3} ${2 * waterY}) scale(1 -1)`} filter="url(#blurR)">
            <path d={bergPath} fill="url(#ice)" />
          </g>
        </g>

        {/* САМ АЙСБЕРГ */}
        <g transform={`translate(0 ${bob})`}>
          {/* тело льда */}
          <path d={bergPath} fill="url(#ice)" opacity={0.97} />
          {/* подводная часть чуть притемнена водой */}
          <g clipPath="url(#waterclip)"><path d={bergPath} fill="#0a2030" opacity={0.28} /></g>
          {/* грани (внутренние полигоны) */}
          <polygon points={`${cx},${tipTop} ${cx - waterlineHW * 0.5},${waterY} ${cx + waterlineHW * 0.2},${waterY + (bottomY - waterY) * 0.35}`} fill="#ffffff" opacity={0.10} />
          <polygon points={`${cx + waterlineHW * 0.3},${waterY} ${cx + halfW(0.55)},${yAt(0.55)} ${cx},${yAt(0.7)}`} fill="#0d2536" opacity={0.22} />
          <polygon points={`${cx - waterlineHW * 0.4},${waterY + 20} ${cx - halfW(0.5)},${yAt(0.5)} ${cx - halfW(0.2)},${yAt(0.28)}`} fill="#ffffff" opacity={0.07} />
          {/* трещины */}
          {[[0.24, 0.5], [0.42, 0.72], [0.3, 0.62]].map(([a, b], i) => (
            <line key={"cr" + i} x1={cx + (rnd(i, 7) - 0.5) * waterlineHW} y1={yAt(a)}
              x2={cx + (rnd(i, 8) - 0.5) * halfW(b) * 1.2} y2={yAt(b)} stroke="#dff0fa" strokeWidth={1.2} opacity={0.18} />
          ))}
          {/* снежная шапка + блик на верхушке */}
          <path d={`M ${cx - waterlineHW * 0.6},${waterY - 4} Q ${cx},${tipTop + 10} ${cx + waterlineHW * 0.55},${waterY - 4}`} fill="none" stroke="#ffffff" strokeWidth={3} opacity={0.5} filter="url(#soft)" />
          {/* рим-лайт по контуру */}
          <path d={bergPath} fill="none" stroke="#eaf6ff" strokeWidth={2} opacity={0.4} />
          {/* красное свечение из глубины сквозь лёд */}
          <g clipPath="url(#waterclip)"><rect x={cx - halfW(0.95)} y={yAt(0.78)} width={halfW(0.95) * 2} height={bottomY - yAt(0.78)} fill={accent} opacity={(0.12 + 0.08 * pulse) * descend} filter="url(#soft)" /></g>
        </g>

        {/* маркер глубины с хвостом */}
        {descend > 0.001 && descend < 0.999 && (
          <>
            <line x1={cx} y1={waterY} x2={cx} y2={orbY} stroke={accent} strokeWidth={2} opacity={0.35} />
            <circle cx={cx} cy={orbY} r={30} fill="url(#orbG)" opacity={0.85} />
            <circle cx={cx} cy={orbY} r={6} fill="#fff" filter="url(#glow)" />
          </>
        )}

        {/* туман-слои */}
        {[0.42, 0.66].map((ty, i) => (
          <rect key={"fog" + i} x={-40 + Math.sin(frame / 50 + i) * 30} y={waterY + (bottomY - waterY) * ty} width={W + 80} height={70}
            fill="#0e2434" opacity={0.10} filter="url(#soft)" />
        ))}
      </svg>

      {/* заголовок */}
      {title && (
        <div style={{ position: "absolute", top: 52, width: "100%", textAlign: "center" }}>
          <div style={{ color: PALETTE.cream, fontSize: 48, fontWeight: 800, letterSpacing: 7, textTransform: "uppercase",
            transform: `translateY(${interpolate(frame, [6, 28], [36, 0], CLAMP)}px)`, opacity: interpolate(frame, [6, 28], [0, 1], CLAMP),
            textShadow: `0 0 26px ${accent}66, 0 2px 8px #000` }}>{title}</div>
          <div style={{ height: 3, width: interpolate(frame, [20, 44], [0, 340], CLAMP), margin: "14px auto 0",
            background: `linear-gradient(90deg, rgba(0,0,0,0), ${accent}, rgba(0,0,0,0))` }} />
        </div>
      )}

      {/* подписи уровней — линия глубины + карточка, появляются по проходу маркера */}
      {levels.map((lv, i) => {
        const t = 0.185 + (i + 0.62) * ((1 - 0.185) / n);
        const y = yAt(t) + bob;
        const on = descend >= (t - 0.06);
        const s = spring({ frame: frame - (26 + i * ((D - 64) / n)), fps, config: { damping: 15, stiffness: 95 } });
        const sp = on ? s : 0;
        const left = i % 2 === 0;
        const tR = n > 1 ? i / (n - 1) : 0;
        const zc = `rgb(${Math.round(96 + (176 - 96) * tR)},${Math.round(160 - 120 * tR)},${Math.round(190 - 150 * tR)})`;
        const edgeX = cx + (left ? -1 : 1) * (halfW(t) + 22);
        return (
          <React.Fragment key={"lv" + i}>
            <div style={{ position: "absolute", top: y - 1, left: left ? edgeX - 120 : edgeX, width: 120, height: 2,
              background: `linear-gradient(${left ? "90deg" : "270deg"}, rgba(0,0,0,0), ${zc})`, opacity: sp }} />
            <div style={{ position: "absolute", top: y - 30, [left ? "right" : "left"]: (left ? W - (edgeX - 130) : edgeX + 130),
              width: 360, textAlign: left ? "right" : "left", transform: `translateX(${(1 - sp) * (left ? 40 : -40)}px)`, opacity: sp }}>
              <div style={{ display: "inline-flex", flexDirection: "column", alignItems: left ? "flex-end" : "flex-start",
                padding: "10px 18px", borderRadius: 12, background: "rgba(8,14,22,0.5)", border: `1px solid ${zc}88`,
                boxShadow: `0 0 24px ${zc}55, inset 0 0 18px rgba(0,0,0,0.45)`, backdropFilter: "blur(3px)" }}>
                <div style={{ color: zc, fontSize: 21, fontWeight: 800, letterSpacing: 4 }}>УРОВЕНЬ {lv.n}</div>
                <div style={{ color: PALETTE.cream, fontSize: 31, fontWeight: 700, marginTop: 1 }}>{lv.label}</div>
              </div>
            </div>
          </React.Fragment>
        );
      })}

      <AbsoluteFill style={{ boxShadow: "inset 0 0 360px rgba(0,0,0,0.9)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
