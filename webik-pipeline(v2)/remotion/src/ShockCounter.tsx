import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";
import { Censored } from "./censor";

// Шок-каунтер: число жёстко карабкается вверх с тряской экрана и красными вспышками,
// в конце — «удар» (пульс) и оседание. Для шокирующего роста числа жертв.
export type ShockProps = {
  from?: number;
  to?: number;
  label?: string;
  sub?: string;
  accent?: string;
};

export const ShockCounter: React.FC<ShockProps> = ({ from = 0, to = 100, label = "", sub = "", accent = PALETTE.red }) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const climbEnd = Math.min(durationInFrames - 30, 92);
  const prog = interpolate(frame, [10, climbEnd], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.in(Easing.cubic) });
  const val = Math.round(from + (to - from) * prog);
  const climbing = frame >= 10 && prog < 1;
  const intensity = climbing ? 0.35 + 0.65 * prog : 0;
  const shakeX = Math.sin(frame * 3.3) * 11 * intensity;
  const shakeY = Math.cos(frame * 2.7) * 8 * intensity;
  const flash = climbing ? 0.08 + 0.12 * Math.abs(Math.sin(frame * 0.85)) : 0;
  const pop = interpolate(frame, [climbEnd, climbEnd + 8], [1.12, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#05070c", opacity: exit, overflow: "hidden", fontFamily: fontFamily("oswald") }}>
      <AbsoluteFill style={{ background: accent, opacity: flash }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `translate(${shakeX}px, ${shakeY}px)` }}>
        <div style={{ color: PALETTE.cream, fontSize: 340, fontWeight: 800, lineHeight: 0.82, letterSpacing: -10, transform: `scale(${pop})`, textShadow: `0 0 60px ${accent}66, 0 20px 80px rgba(0,0,0,0.8)` }}>
          {val.toLocaleString("ru-RU")}
        </div>
        {label && (
          <div style={{ marginTop: 26 }}>
            <Censored text={label} style={{ color: accent, fontSize: 58, fontWeight: 800, letterSpacing: 3, textTransform: "uppercase", display: "inline-block" }} />
          </div>
        )}
        {sub && <div style={{ marginTop: 10, color: PALETTE.cream, opacity: 0.6, fontSize: 30, fontWeight: 500, letterSpacing: 3, textTransform: "uppercase" }}>{sub}</div>}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
