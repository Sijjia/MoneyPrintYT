import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { mspring, track, ease } from "./anim";

export type KarniCurseProps = {
  kicker?: string;
  title?: string;
  caption?: string;
  refuseLabel?: string;   // штамп у Врат Ямы («ОТКАЗ» / «REFUSED»)
  bypassLabel?: string;   // подпись на дуге-обходе («минуя власть Ямы»)
  durationInFrames?: number;
};

/**
 * Легенда Карни Маты (моушн-дизайн, «3D» через перспективу).
 * Круг перерождений рода: ЧЕЛОВЕК → смерть → ВРАТА ЯМЫ (ОТКАЗ, закрыты) →
 * душа огибает Яму золотой дугой «МИНУЯ ЕГО ВЛАСТЬ» → КРЫСА (священный предок) →
 * снова ЧЕЛОВЕК. Замкнутый цикл, летящая душа-искра.
 */
export const KarniCurse: React.FC<KarniCurseProps> = ({
  kicker = "ЛЕГЕНДА КАРНИ МАТЫ",
  title = "ПРОКЛЯТИЕ БОГА СМЕРТИ",
  caption = "Род Карни после смерти рождается крысами — минуя власть Ямы, а потом снова людьми",
  refuseLabel = "ОТКАЗ",
  bypassLabel = "минуя власть Ямы",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  // геометрия сцены (1920x1080)
  const CX = 960, CY = 560, R = 300;
  const humanP = { x: CX, y: CY + R };          // низ — ЧЕЛОВЕК
  const gateP = { x: CX, y: CY - R };           // верх — ВРАТА ЯМЫ
  const ratP = { x: CX + R + 40, y: CY + 40 };  // право — КРЫСА

  // «3D»: лёгкий наклон всей кольцевой сцены
  const introTilt = track(frame, 0, 40, ease.smoothOut);
  const tiltDeg = 60 - introTilt * 6;           // 60→54°
  const ringScale = mspring(frame, fps, { stiffness: 90, damping: 18, delay: 2 });

  // фазы повествования (кадры при 30fps ~ 16с)
  const F = (s: number) => s * fps;
  const soulRise = track(frame, F(0.6), F(3.2), ease.smoothOut);      // душа поднимается к Яме
  const refuse = track(frame, F(3.3), F(5.6), ease.backOut);          // ОТКАЗ впечатывается
  const curse = track(frame, F(5.8), F(8.4), ease.smoothOut);        // дуга-обход появляется
  const soulBypass = track(frame, F(6.2), F(10.6), ease.inOut);      // душа огибает → крыса
  const rebirth = track(frame, F(10.8), F(14.4), ease.smoothOut);    // крыса → снова человек

  // точка на квадратичной кривой
  const q = (a: any, c: any, b: any, t: number) => ({
    x: (1 - t) * (1 - t) * a.x + 2 * (1 - t) * t * c.x + t * t * b.x,
    y: (1 - t) * (1 - t) * a.y + 2 * (1 - t) * t * c.y + t * t * b.y,
  });
  // управляющая точка дуги-обхода (уводит вправо от Ямы)
  const ctrlBypass = { x: CX + R + 220, y: CY - R - 40 };
  const ctrlReturn = { x: CX + R + 220, y: CY + R + 120 };

  // позиция летящей души
  let soul = humanP;
  let soulGlow = 0.5;
  if (frame < F(3.3)) {
    // человек → к вратам (по вертикали вверх)
    soul = { x: humanP.x, y: humanP.y + (gateP.y - humanP.y) * soulRise };
    soulGlow = 0.6 + soulRise * 0.4;
  } else if (frame < F(6.2)) {
    // застыла у врат (отказ)
    soul = { x: gateP.x, y: gateP.y + 34 };
    soulGlow = 1;
  } else if (frame < F(10.8)) {
    // огибает Яму дугой до крысы
    soul = q(gateP, ctrlBypass, ratP, soulBypass);
    soulGlow = 1;
  } else {
    // крыса → снова человек
    soul = q(ratP, ctrlReturn, humanP, rebirth);
    soulGlow = 0.9;
  }

  const gold = "#e8c874", goldDeep = "#c9992f", red = "#c0402f";
  const pulse = 0.5 + 0.5 * Math.sin(frame / 5);

  const Node: React.FC<{ p: { x: number; y: number }; on: number; children: React.ReactNode }> = ({ p, on, children }) => (
    <g transform={`translate(${p.x},${p.y})`} opacity={on} style={{ transformBox: "fill-box" }}>
      <circle r={72} fill="#100a06" stroke={gold} strokeWidth={2} opacity={0.9} />
      <circle r={72} fill="none" stroke={gold} strokeWidth={6} opacity={0.25 * on} style={{ filter: "blur(6px)" }} />
      {children}
    </g>
  );

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      {/* фон храма-пустыни ночью */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #241608 0%, #150c06 55%, #080402 100%)" }} />
      <AbsoluteFill style={{ background: "repeating-linear-gradient(90deg, rgba(232,200,116,0.03) 0 1px, transparent 1px 90px)", pointerEvents: "none", opacity: 0.6 }} />

      {/* заголовок */}
      <div style={{ position: "absolute", top: 60, left: 0, right: 0, textAlign: "center",
        opacity: interpolate(frame, [4, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
        <div style={{ color: gold, fontSize: 28, letterSpacing: 8, fontWeight: 700 }}>{kicker}</div>
        <div style={{ color: "#f4ead2", fontSize: 62, letterSpacing: 2, fontWeight: 800, marginTop: 6, textShadow: "0 6px 30px rgba(0,0,0,0.9)" }}>{title}</div>
      </div>

      {/* КОЛЬЦО ПЕРЕРОЖДЕНИЙ в перспективе */}
      <div style={{ position: "absolute", inset: 0, perspective: "1400px" }}>
        <div style={{ position: "absolute", inset: 0, transform: `rotateX(${tiltDeg}deg) scale(${0.86 + ringScale * 0.14})`, transformOrigin: "50% 58%" }}>
          <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
            <defs>
              <radialGradient id="kc_soul" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#fff7e0" />
                <stop offset="40%" stopColor={gold} />
                <stop offset="100%" stopColor={goldDeep} stopOpacity="0" />
              </radialGradient>
            </defs>

            {/* каменное кольцо рода */}
            <circle cx={CX} cy={CY} r={R} fill="none" stroke="#3a2c17" strokeWidth={26} />
            <circle cx={CX} cy={CY} r={R} fill="none" stroke={gold} strokeWidth={3} opacity={0.5} strokeDasharray="2 16" />

            {/* «нормальный» путь смерти к Яме — тускнеет и перечёркивается */}
            <line x1={humanP.x} y1={humanP.y} x2={gateP.x} y2={gateP.y}
              stroke={red} strokeWidth={4} strokeDasharray="10 12" opacity={0.25 + 0.25 * (1 - curse)} />

            {/* золотая дуга-обход «минуя Яму» */}
            <path d={`M ${gateP.x} ${gateP.y} Q ${ctrlBypass.x} ${ctrlBypass.y} ${ratP.x} ${ratP.y}`}
              fill="none" stroke={gold} strokeWidth={6} strokeLinecap="round"
              strokeDasharray="1400" strokeDashoffset={1400 * (1 - curse)}
              opacity={0.9} style={{ filter: "drop-shadow(0 0 10px rgba(232,200,116,0.6))" }} />
            <path d={`M ${ratP.x} ${ratP.y} Q ${ctrlReturn.x} ${ctrlReturn.y} ${humanP.x} ${humanP.y}`}
              fill="none" stroke={gold} strokeWidth={5} strokeLinecap="round"
              strokeDasharray="1400" strokeDashoffset={1400 * (1 - rebirth)} opacity={0.8} />

            {/* УЗЕЛ: ВРАТА ЯМЫ (верх) */}
            <Node p={gateP} on={interpolate(frame, [F(2.6), F(3.4)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
              {/* ворота */}
              <rect x={-34} y={-46} width={68} height={92} rx={4} fill="#1c120a" stroke={red} strokeWidth={3} />
              <path d="M -30 -40 L 0 -60 L 30 -40" fill="none" stroke={red} strokeWidth={3} />
              <line x1={0} y1={-40} x2={0} y2={44} stroke={red} strokeWidth={3} />
            </Node>

            {/* УЗЕЛ: ЧЕЛОВЕК (низ) */}
            <Node p={humanP} on={interpolate(frame, [F(0.2), F(1.0)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
              <circle cx={0} cy={-24} r={16} fill={gold} />
              <path d="M -22 44 Q 0 -6 22 44 Z" fill={gold} />
            </Node>

            {/* УЗЕЛ: КРЫСА (право) */}
            <Node p={ratP} on={interpolate(frame, [F(6.0), F(7.0)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}>
              {/* силуэт крысы */}
              <path d="M -40 20 Q -46 -10 -18 -14 Q -8 -30 6 -18 Q 30 -22 40 2 Q 46 22 16 24 Z" fill={gold} />
              <circle cx={30} cy={-6} r={6} fill="#100a06" />
              <path d="M 40 6 Q 78 14 96 -14" fill="none" stroke={gold} strokeWidth={4} strokeLinecap="round" />
            </Node>

            {/* летящая ДУША */}
            <g transform={`translate(${soul.x},${soul.y})`}>
              <circle r={26 + pulse * 6} fill="url(#kc_soul)" opacity={soulGlow} />
              <circle r={9} fill="#fff8e6" opacity={soulGlow} />
            </g>
          </svg>
        </div>
      </div>

      {/* ШТАМП «ОТКАЗ» у врат */}
      <div style={{ position: "absolute", left: "50%", top: 300, transform: `translate(-50%,0) rotate(-9deg) scale(${1.5 - refuse * 0.5})`,
        opacity: interpolate(frame, [F(3.4), F(4.0), durationInFrames - 20], [0, 1, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit,
        border: `6px solid ${red}`, color: red, fontSize: 52, fontWeight: 900, letterSpacing: 6, padding: "8px 34px", borderRadius: 6,
        textShadow: "0 2px 0 rgba(0,0,0,0.3)", background: "rgba(10,6,4,0.35)" }}>
        {refuseLabel}
      </div>

      {/* подпись-курсив «минуя его власть» на дуге */}
      <div style={{ position: "absolute", right: 150, top: 430, color: gold, fontSize: 34, fontStyle: "italic", fontWeight: 600,
        fontFamily: fontFamily("montserrat"), textShadow: "0 3px 16px rgba(0,0,0,0.9)",
        opacity: interpolate(frame, [F(7.0), F(8.2)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
        {bypassLabel}
      </div>

      {/* нижняя подпись */}
      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 54, textAlign: "center", padding: "0 220px",
          color: "#eaddc2", fontSize: 30, fontWeight: 500, lineHeight: 1.3, fontFamily: fontFamily("montserrat"),
          textShadow: "0 4px 22px rgba(0,0,0,0.95)",
          opacity: interpolate(frame, [F(11.4), F(12.8)], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          {caption}
        </div>
      )}

      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
