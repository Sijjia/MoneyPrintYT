import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig, Easing } from "remotion";
import React from "react";

/** Первая тема GTA: капибара слева на весь отрезок + справа разнотипные анимированные
 *  инфографики с человечками (толпа смотрит трейлер → люди несут кэш → стопки денег →
 *  человечки таскают диски). НЕ повторяющиеся счётчики, а живые моушн-сцены. */
export type StageSeg = {
  from: number; to: number;                 // кадры сегмента
  kind: "views" | "cash" | "stacks" | "discs";
  value: number; prefix?: string; label: string; sub?: string;
};
type Props = { mouth?: number[]; segments?: StageSeg[]; accent?: string; accent2?: string };

const fmt = (n: number) => Math.round(n).toLocaleString("ru-RU").replace(/,/g, " ");
const easeOut = (t: number) => 1 - Math.pow(1 - t, 3);

/** маленький человечек-пиктограмма с walk-циклом и предметом в руках */
const Person: React.FC<{ x: number; y: number; s: number; phase: number; color: string;
  carry?: "disc" | "cash" | "none"; accent: string; walk?: boolean }> =
({ x, y, s, phase, color, carry = "none", accent, walk = true }) => {
  const f = useCurrentFrame();
  const t = walk ? Math.sin((f + phase) / 5) : 0;
  const legA = t * 16, legB = -t * 16;
  const armSwing = t * 12;
  return (
    <g transform={`translate(${x},${y}) scale(${s})`}>
      {/* ноги */}
      <line x1={-6} y1={16} x2={-6 + legA * 0.4} y2={44} stroke={color} strokeWidth={7} strokeLinecap="round" />
      <line x1={6} y1={16} x2={6 + legB * 0.4} y2={44} stroke={color} strokeWidth={7} strokeLinecap="round" />
      {/* тело */}
      <rect x={-11} y={-16} width={22} height={34} rx={9} fill={color} />
      {/* голова */}
      <circle cx={0} cy={-30} r={11} fill={color} />
      {/* руки + предмет */}
      {carry === "none" ? (
        <>
          <line x1={-9} y1={-6} x2={-16 - armSwing * 0.3} y2={12} stroke={color} strokeWidth={6} strokeLinecap="round" />
          <line x1={9} y1={-6} x2={16 + armSwing * 0.3} y2={12} stroke={color} strokeWidth={6} strokeLinecap="round" />
        </>
      ) : (
        <>
          <line x1={-9} y1={-6} x2={-18} y2={-4} stroke={color} strokeWidth={6} strokeLinecap="round" />
          <line x1={9} y1={-6} x2={18} y2={-4} stroke={color} strokeWidth={6} strokeLinecap="round" />
          {carry === "disc" && (
            <g transform="translate(0,-6)">
              <ellipse cx={0} cy={0} rx={20} ry={8} fill="#0c0c12" stroke={accent} strokeWidth={2.5} />
              <ellipse cx={0} cy={0} rx={6} ry={2.6} fill={accent} />
            </g>
          )}
          {carry === "cash" && (
            <g transform="translate(0,-8)">
              <rect x={-18} y={-8} width={36} height={17} rx={2} fill="#2fae5f" stroke="#8ff0b5" strokeWidth={1.5} />
              <circle cx={0} cy={0.5} r={4} fill="#8ff0b5" />
            </g>
          )}
        </>
      )}
    </g>
  );
};

/** большой счётчик, считает от 0 до value по прогрессу сегмента */
const BigNumber: React.FC<{ value: number; prefix?: string; label: string; sub?: string;
  prog: number; accent: string; suffixText?: string }> =
({ value, prefix = "", label, sub, prog, accent, suffixText }) => {
  const shown = Math.round(value * easeOut(Math.min(1, prog / 0.75)));
  const pop = interpolate(prog, [0, 0.08], [0.6, 1], { extrapolateRight: "clamp" });
  return (
    <div style={{ textAlign: "center", transform: `scale(${pop})` }}>
      <div style={{ fontSize: 118, fontWeight: 900, letterSpacing: -3, lineHeight: 1,
        color: "#fff", textShadow: `0 0 40px ${accent}90`, fontVariantNumeric: "tabular-nums" }}>
        {prefix}{fmt(shown)}{suffixText || ""}
      </div>
      <div style={{ marginTop: 14, fontSize: 34, fontWeight: 800, color: accent, letterSpacing: 3 }}>{label}</div>
      {sub && <div style={{ marginTop: 6, fontSize: 22, color: "#aab", letterSpacing: 1 }}>{sub}</div>}
    </div>
  );
};

export const GTARecordsStage: React.FC<Props> = ({ mouth = [], segments = [], accent = "#ff2d78", accent2 = "#25e0c8" }) => {
  const frame = useCurrentFrame();
  const { width, height, fps, durationInFrames } = useVideoConfig();

  // ── фон: тёмный градиент + неоновая сетка (GTA VI vibe) ──────────────────
  const grid = 64;

  // ── капибара слева ───────────────────────────────────────────────────────
  const mh = height * 0.82, mw = mh * (1370 / 3068);
  const cx = width * 0.20;
  const inn = spring({ frame, fps, config: { damping: 15, stiffness: 90 } });
  const ex = interpolate(inn, [0, 1], [-140, 0]);
  const bob = Math.sin(frame / 50) * 4;
  const breathe = 1 + Math.sin(frame / 24) * 0.004;
  const mopen = interpolate(mouth[frame] ?? 0, [0, 1], [0, 1]);
  const left = cx - mw / 2 + ex, top = height - mh + bob - height * 0.02;

  // активный сегмент
  const seg = segments.find((s) => frame >= s.from && frame < s.to) || segments[segments.length - 1];
  const prog = seg ? (frame - seg.from) / Math.max(1, seg.to - seg.from) : 0;
  const segIn = seg ? interpolate(frame - seg.from, [0, 10], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) : 1;
  const segOut = seg ? interpolate(frame, [seg.to - 8, seg.to], [1, 0], { extrapolateLeft: "clamp" }) : 1;
  const segA = segIn * segOut;

  // правая сцена
  const stageX = width * 0.58, stageW = width * 0.40, stageCX = stageX + stageW / 2;
  const stageY = height * 0.16;

  return (
    <AbsoluteFill style={{ background: "radial-gradient(120% 90% at 60% 20%, #16111e 0%, #0a0a10 60%, #060608 100%)" }}>
      {/* неоновая сетка */}
      <svg width={width} height={height} style={{ position: "absolute", opacity: 0.10 }}>
        {Array.from({ length: Math.ceil(width / grid) }).map((_, i) => (
          <line key={"v" + i} x1={i * grid} y1={0} x2={i * grid} y2={height} stroke={accent2} strokeWidth={1} />))}
        {Array.from({ length: Math.ceil(height / grid) }).map((_, i) => (
          <line key={"h" + i} x1={0} y1={i * grid} x2={width} y2={i * grid} stroke={accent2} strokeWidth={1} />))}
      </svg>

      {/* тень под капибарой */}
      <div style={{ position: "absolute", left: cx - mw * 0.4, top: height - mh * 0.26, width: mw * 0.8, height: mh * 0.2,
        background: "radial-gradient(ellipse, rgba(0,0,0,.55), transparent 70%)", filter: "blur(6px)" }} />
      {/* капибара */}
      <div style={{ position: "absolute", left, top, width: mw, height: mh, transform: `scale(${breathe})`, transformOrigin: "bottom center" }}>
        <Img src={staticFile("mascot/closed.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0 }} />
        <Img src={staticFile("mascot/open.png")} style={{ width: "100%", position: "absolute", top: 0, left: 0, opacity: mopen }} />
      </div>

      {/* ── ПРАВАЯ СЦЕНА (сегменты) ─────────────────────────────────────── */}
      <div style={{ position: "absolute", left: stageX, top: stageY, width: stageW, height: height * 0.68,
        opacity: segA, transform: `translateY(${(1 - segA) * 30}px)` }}>
        {/* число сверху */}
        <div style={{ position: "absolute", top: 0, left: 0, width: "100%", display: "flex", justifyContent: "center" }}>
          {seg && <BigNumber value={seg.value} prefix={seg.prefix} label={seg.label} sub={seg.sub} prog={prog} accent={accent} />}
        </div>

        {/* иллюстрация под числом */}
        <svg width={stageW} height={height * 0.40} style={{ position: "absolute", top: height * 0.26, left: 0 }}
          viewBox={`0 0 ${stageW} ${height * 0.40}`}>
          {seg?.kind === "views" && (() => {
            // толпа смотрит на большой экран-телефон
            const phoneOn = (frame % 30) < 22;
            return (<g>
              <rect x={stageW / 2 - 70} y={20} width={140} height={200} rx={18} fill="#111119" stroke={accent} strokeWidth={4} />
              <rect x={stageW / 2 - 58} y={38} width={116} height={150} rx={6} fill={phoneOn ? accent2 : "#0c2a2a"} opacity={phoneOn ? 0.9 : 0.5} />
              <polygon points={`${stageW / 2 - 12},90 ${stageW / 2 - 12},140 ${stageW / 2 + 26},115`} fill="#0a0a10" />
              {Array.from({ length: 11 }).map((_, i) => {
                const px = 30 + (i % 6) * (stageW - 60) / 5 * (i < 6 ? 1 : 0.85) + (i >= 6 ? 26 : 0);
                const py = 300 + (i < 6 ? 0 : 34);
                return <Person key={i} x={px} y={py} s={0.62} phase={i * 7} color={i % 2 ? accent2 : "#dfe3ee"} accent={accent} walk={false} />;
              })}
            </g>);
          })()}

          {seg?.kind === "cash" && (() => {
            // люди несут кэш к кассе, купюры летят в кучу
            return (<g>
              {/* касса/пьедестал */}
              <rect x={stageW / 2 - 46} y={230} width={92} height={70} rx={8} fill="#141420" stroke={accent} strokeWidth={3} />
              <text x={stageW / 2} y={274} fontSize={30} textAnchor="middle" fill={accent2} fontWeight={800}>$</text>
              {/* летящие купюры */}
              {Array.from({ length: 7 }).map((_, i) => {
                const t = ((frame * 2 + i * 20) % 120) / 120;
                const bx = 40 + i * (stageW - 80) / 6, sxp = stageW / 2;
                const cxp = interpolate(t, [0, 1], [bx, sxp]);
                const cyp = interpolate(t, [0, 1], [70, 232]) - Math.sin(t * Math.PI) * 40;
                return <rect key={i} x={cxp - 16} y={cyp - 8} width={32} height={15} rx={2} fill="#2fae5f" stroke="#8ff0b5" strokeWidth={1}
                  transform={`rotate(${t * 180} ${cxp} ${cyp})`} opacity={0.9} />;
              })}
              {/* носильщики */}
              {Array.from({ length: 4 }).map((_, i) => (
                <Person key={i} x={40 + i * 46} y={340} s={0.7} phase={i * 11} color={i % 2 ? accent2 : "#dfe3ee"} carry="cash" accent={accent} />
              ))}
            </g>);
          })()}

          {seg?.kind === "stacks" && (() => {
            // растущие стопки денег (бары) + монеты
            const bars = [0.4, 0.62, 0.78, 0.95, 1.0];
            return (<g>
              {bars.map((bh, i) => {
                const grow = interpolate(prog, [0.05 + i * 0.12, 0.35 + i * 0.12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                const H = bh * 220 * grow, x = 30 + i * (stageW - 60) / 5;
                return (<g key={i}>
                  <rect x={x} y={300 - H} width={(stageW - 60) / 5 - 14} height={H} rx={4} fill={i === 4 ? accent : "#2fae5f"} opacity={0.9} />
                  {Array.from({ length: Math.floor(H / 18) }).map((_, k) => (
                    <line key={k} x1={x} y1={300 - k * 18} x2={x + (stageW - 60) / 5 - 14} y2={300 - k * 18} stroke="#0a0a10" strokeWidth={1.4} />))}
                </g>);
              })}
              <Person x={stageW - 40} y={330} s={0.7} phase={0} color="#dfe3ee" accent={accent} walk={false} />
            </g>);
          })()}

          {seg?.kind === "discs" && (() => {
            // конвейер: человечки таскают диски, диски копятся в стопку
            const stackN = Math.floor(interpolate(prog, [0.1, 0.9], [0, 9], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
            return (<g>
              {/* конвейерная лента */}
              <rect x={20} y={250} width={stageW - 40} height={12} rx={6} fill="#22222e" />
              {Array.from({ length: 8 }).map((_, i) => {
                const xx = ((frame * 3 + i * 60) % (stageW - 40)) + 20;
                return <circle key={i} cx={xx} cy={256} r={3} fill={accent2} opacity={0.6} />;
              })}
              {/* стопка дисков справа */}
              {Array.from({ length: stackN }).map((_, i) => (
                <ellipse key={i} cx={stageW - 70} cy={240 - i * 12} rx={34} ry={12} fill="#0c0c12" stroke={i === stackN - 1 ? accent : accent2} strokeWidth={2.5} />
              ))}
              {stackN > 0 && <ellipse cx={stageW - 70} cy={240 - (stackN - 1) * 12} rx={9} ry={3.4} fill={accent} />}
              {/* носильщики дисков идут слева направо */}
              {Array.from({ length: 4 }).map((_, i) => {
                const march = ((frame * 3 + i * 90) % (stageW - 120)) + 20;
                return <Person key={i} x={march} y={236} s={0.7} phase={i * 9} color={i % 2 ? accent2 : "#dfe3ee"} carry="disc" accent={accent} />;
              })}
            </g>);
          })()}
        </svg>
      </div>

      {/* лёгкая виньетка */}
      <div style={{ position: "absolute", inset: 0, boxShadow: "inset 0 0 220px rgba(0,0,0,.7)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};

export default GTARecordsStage;
