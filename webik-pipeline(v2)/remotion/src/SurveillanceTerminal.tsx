import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type SurveillanceTerminalProps = {
  value: string;
  label: string;
  suffix?: string;
  accent?: string;
};

// Тёмный монитор слежки: скан-лайны, прицел, «МОНИТОРИНГ», число на пульте.
export const SurveillanceTerminal: React.FC<SurveillanceTerminalProps> = ({
  value,
  label,
  suffix = "",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const target = parseInt(value.replace(/\D/g, ""), 10);
  const hasNum = !Number.isNaN(target);
  const t = interpolate(frame, [4, 30], [0, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const shown = hasNum ? Math.round(target * t).toLocaleString("ru-RU") : value;

  const boot = interpolate(frame, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const panelW = interpolate(frame, [0, 12], [0.7, 1], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const flicker = 0.92 + 0.08 * Math.sin(frame * 1.7) * Math.sin(frame * 0.6);
  const cursor = Math.floor(frame / 8) % 2 === 0 ? "▮" : " ";
  const scanY = (frame * 9) % 100;
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const brk = 34;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit * boot }}>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "flex-start", padding: 120 }}>
        <div
          style={{
            position: "relative",
            width: 1040,
            transform: `scaleX(${panelW})`,
            transformOrigin: "left center",
            background: "linear-gradient(180deg, rgba(10,6,6,0.9), rgba(20,4,4,0.82))",
            border: `2px solid ${accent}`,
            boxShadow: `0 0 40px ${accent}55, inset 0 0 60px rgba(217,40,40,0.15)`,
            padding: "34px 44px 40px",
            overflow: "hidden",
            opacity: flicker,
          }}
        >
          {/* скан-лайны */}
          <AbsoluteFill
            style={{
              background: "repeating-linear-gradient(0deg, rgba(217,40,40,0.10) 0px, rgba(217,40,40,0.10) 1px, transparent 3px, transparent 5px)",
              pointerEvents: "none",
            }}
          />
          {/* бегущая полоса развёртки */}
          <div style={{ position: "absolute", left: 0, right: 0, top: `${scanY}%`, height: 60, background: `linear-gradient(180deg, transparent, ${accent}22, transparent)`, pointerEvents: "none" }} />
          {/* уголки-скобки */}
          {[["left","top"],["right","top"],["left","bottom"],["right","bottom"]].map(([x,y],i)=>(
            <div key={i} style={{position:"absolute",[x as string]:10,[y as string]:10,width:brk,height:brk,borderTop:y==="top"?`3px solid ${accent}`:"none",borderBottom:y==="bottom"?`3px solid ${accent}`:"none",borderLeft:x==="left"?`3px solid ${accent}`:"none",borderRight:x==="right"?`3px solid ${accent}`:"none"}}/>
          ))}
          {/* хедер */}
          <div style={{ display: "flex", alignItems: "center", gap: 14, color: accent, fontSize: 30, letterSpacing: 6, fontWeight: 600 }}>
            <span style={{ fontSize: 20 }}>●</span> МОНИТОРИНГ
            <span style={{ marginLeft: "auto", fontSize: 22, opacity: 0.8 }}>REC {Math.floor(frame / 30).toString().padStart(2, "0")}:{(frame % 30 * 3).toString().padStart(2, "0")}</span>
          </div>
          {/* число + прицел */}
          <div style={{ display: "flex", alignItems: "center", gap: 34, marginTop: 18 }}>
            <svg width={92} height={92} viewBox="-50 -50 100 100" style={{ flexShrink: 0 }}>
              <circle cx="0" cy="0" r="42" fill="none" stroke={accent} strokeWidth="3" strokeDasharray="18 10" style={{ transformOrigin: "center", transform: `rotate(${frame * 2}deg)` }} />
              <circle cx="0" cy="0" r="26" fill="none" stroke={accent} strokeWidth="2" opacity="0.6" />
              <line x1="-48" y1="0" x2="-14" y2="0" stroke={accent} strokeWidth="2" /><line x1="14" y1="0" x2="48" y2="0" stroke={accent} strokeWidth="2" />
              <line x1="0" y1="-48" x2="0" y2="-14" stroke={accent} strokeWidth="2" /><line x1="0" y1="14" x2="0" y2="48" stroke={accent} strokeWidth="2" />
            </svg>
            <div style={{ color: PALETTE.cream, fontSize: 168, fontWeight: 800, lineHeight: 0.9, letterSpacing: -2, textShadow: `0 0 30px ${accent}aa` }}>
              {shown}
              <span style={{ color: accent }}>{suffix}</span>
              <span style={{ color: accent, marginLeft: 8 }}>{cursor}</span>
            </div>
          </div>
          {/* лейбл */}
          <div style={{ marginTop: 14, color: accent, fontSize: 40, letterSpacing: 4, textTransform: "uppercase", fontWeight: 600, borderTop: `1px solid ${accent}66`, paddingTop: 14 }}>
            &gt; {label}
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
