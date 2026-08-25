import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type IronCellsProps = {
  title?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 33.7 + s * 61.1) * 43758.5453;
  return x - Math.floor(x);
};

// Проезд по тюремному коридору: ряды решётчатых камер с силуэтами, аварийный свет.
export const IronCells: React.FC<IronCellsProps> = ({
  title = "ЛАГЕРЬ 22",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const dolly = interpolate(frame, [0, durationInFrames], [0, 4600]);
  const flick = 0.82 + 0.18 * Math.abs(Math.sin(frame / 6));

  const N = 10;
  const cells = Array.from({ length: N }).flatMap((_, i) =>
    [-1, 1].map((side) => ({ z: -420 - i * 470, side, i, hasFig: rnd(i * 3 + (side > 0 ? 1 : 0), 2) > 0.45, key: `${i}-${side}` }))
  );

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #0a0708 0%, #0c0506 50%, #060202 100%)" }} />
      {/* аварийный красный свет в глубине */}
      <AbsoluteFill style={{ background: `radial-gradient(circle at 50% 50%, ${accent}${Math.round(flick * 40).toString(16).padStart(2, "0")} 0%, transparent 42%)`, opacity: 0.7 }} />

      <AbsoluteFill style={{ perspective: 900, opacity: intro }}>
        <div style={{ position: "absolute", left: "50%", top: "50%", transformStyle: "preserve-3d", transform: `translate(-50%,-50%) translateZ(${dolly}px)` }}>
          {cells.map(({ z, side, hasFig, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                transform: `translate3d(${side * 470}px, 0px, ${z}px) rotateY(${side * 90}deg)`,
                width: 460,
                height: 520,
                marginLeft: -230,
                marginTop: -260,
                background: "linear-gradient(180deg,#141010,#080505)",
                borderTop: "8px solid #000",
                borderBottom: "8px solid #000",
                display: "flex",
                alignItems: "flex-end",
                justifyContent: "center",
                boxShadow: "inset 0 0 60px rgba(0,0,0,0.8)",
              }}
            >
              {/* решётка */}
              <svg width={460} height={520} viewBox="0 0 460 520" style={{ position: "absolute", inset: 0 }}>
                {Array.from({ length: 9 }).map((_, k) => (
                  <line key={k} x1={30 + k * 50} y1="20" x2={30 + k * 50} y2="500" stroke="#2a2020" strokeWidth="9" />
                ))}
                <line x1="20" y1="90" x2="440" y2="90" stroke="#2a2020" strokeWidth="8" />
                <line x1="20" y1="430" x2="440" y2="430" stroke="#2a2020" strokeWidth="8" />
              </svg>
              {/* силуэт заключённого */}
              {hasFig && (
                <svg width={200} height={300} viewBox="0 0 200 300" style={{ marginBottom: 20, opacity: 0.9 }}>
                  <ellipse cx="100" cy="70" rx="34" ry="40" fill="#000" />
                  <path d="M40 300 Q100 150 160 300 Z" fill="#000" />
                </svg>
              )}
            </div>
          ))}
          {/* пол */}
          <div style={{ position: "absolute", transform: "rotateX(90deg) translateZ(260px) translateY(-2400px)", width: 520, height: 5200, marginLeft: -260, background: `linear-gradient(180deg, transparent, ${accent}33)` }} />
        </div>
      </AbsoluteFill>

      {/* мигающая лампа сверху */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 40, opacity: intro * flick, pointerEvents: "none" }}>
        <div style={{ width: 160, height: 160, borderRadius: "50%", background: `radial-gradient(circle, ${accent}88, transparent 70%)`, filter: "blur(6px)" }} />
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.92)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 88, opacity: interpolate(frame, [18, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 88, fontWeight: 800, letterSpacing: 8, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.95)` }}>{title}</div>
          <div style={{ marginTop: 8, color: accent, fontSize: 32, letterSpacing: 5, fontWeight: 600 }}>ИСЧЕЗНОВЕНИЕ БЕЗ СЛЕДА</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
