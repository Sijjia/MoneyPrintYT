import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type BeamingTradeProps = {
  itemName: string;         // «Dominus Empyreus» / «Sparkle Time Fedora»
  itemSub?: string;         // «Limited · редчайший»
  price: string;            // «$13 605» / «$85 000»
  caption?: string;         // фраза снизу
  accent?: string;
};

// Как краденый лимитед превращается в реальные деньги: карточка предмета → стрелка → сумма, штамп STOLEN.
export const BeamingTrade: React.FC<BeamingTradeProps> = ({
  itemName, itemSub = "LIMITED", price, caption = "", accent = "#e2231a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const inCard = spring({ frame: frame - 6, fps, config: { damping: 13, stiffness: 150 } });
  const arrow = interpolate(frame, [24, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const priceIn = spring({ frame: frame - 40, fps, config: { damping: 12, stiffness: 160 } });
  const stampAt = Math.round(durationInFrames * 0.5);
  const stamp = interpolate(frame, [stampAt, stampAt + 8], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #1a0a0b 0%, #0b0607 60%, #050303 100%)", fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 60, flexDirection: "row" }}>
        {/* карточка предмета */}
        <div style={{ position: "relative", width: 480, height: 560, background: "linear-gradient(180deg, #14181f, #0c0f14)", border: `3px solid ${accent}`,
          boxShadow: `0 20px 60px rgba(0,0,0,0.7), 0 0 50px ${accent}33`, borderRadius: 18, transform: `translateY(${interpolate(inCard, [0, 1], [60, 0])}px) rotate(${interpolate(inCard, [0, 1], [-4, -2])}deg)`, opacity: inCard, overflow: "hidden" }}>
          <div style={{ height: 380, display: "flex", alignItems: "center", justifyContent: "center", background: "radial-gradient(circle at 50% 40%, #2a2030, #10121a)" }}>
            {/* стилизованная «шляпа»-корона Dominus */}
            <svg width={260} height={220} viewBox="0 0 260 220">
              <defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#f4d06a" /><stop offset="1" stopColor="#8a6a1e" /></linearGradient></defs>
              <path d="M40 170 L40 80 L80 120 L130 40 L180 120 L220 80 L220 170 Z" fill="url(#g)" stroke="#fff3c4" strokeWidth="3" />
              <rect x="40" y="168" width="180" height="26" rx="6" fill="#c8a24a" stroke="#fff3c4" strokeWidth="2" />
              {[70, 130, 190].map((cx, i) => <circle key={i} cx={cx} cy={181} r="7" fill="#e2231a" />)}
            </svg>
          </div>
          <div style={{ padding: "18px 22px" }}>
            <div style={{ color: "#fff", fontSize: 40, fontWeight: 700, letterSpacing: 1 }}>{itemName}</div>
            <div style={{ color: accent, fontSize: 24, letterSpacing: 4, marginTop: 4 }}>{itemSub}</div>
          </div>
          {/* штамп STOLEN */}
          <div style={{ position: "absolute", top: 150, left: -10, right: -10, textAlign: "center", opacity: stamp,
            transform: `rotate(-14deg) scale(${interpolate(stamp, [0, 1], [1.6, 1])})` }}>
            <span style={{ color: "#fff", background: accent, fontSize: 56, fontWeight: 800, letterSpacing: 6, padding: "6px 24px", border: "4px solid #fff", boxShadow: "0 0 30px rgba(0,0,0,0.6)" }}>STOLEN</span>
          </div>
        </div>

        {/* стрелка */}
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", opacity: arrow }}>
          <svg width={220} height={80} viewBox="0 0 220 80">
            <line x1="0" y1="40" x2={interpolate(arrow, [0, 1], [0, 180])} y2="40" stroke={accent} strokeWidth="8" />
            <polygon points="180,20 220,40 180,60" fill={accent} opacity={arrow > 0.7 ? 1 : 0} />
          </svg>
          <div style={{ color: accent, fontSize: 26, letterSpacing: 4, marginTop: 6 }}>ПРОДАН</div>
        </div>

        {/* сумма */}
        <div style={{ textAlign: "center", transform: `scale(${interpolate(priceIn, [0, 1], [0.6, 1])})`, opacity: priceIn }}>
          <div style={{ color: "#39d98a", fontSize: 44, letterSpacing: 6, fontWeight: 700 }}>РЕАЛЬНЫЕ ДЕНЬГИ</div>
          <div style={{ color: "#fff", fontSize: 150, fontWeight: 800, letterSpacing: -2, textShadow: "0 0 40px rgba(57,217,138,0.5)", fontFamily: "'Consolas', monospace" }}>{price}</div>
        </div>
      </AbsoluteFill>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 84,
          opacity: interpolate(frame, [18, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1500, textAlign: "center", color: "#f4f1ea", fontSize: 46, fontWeight: 600, textShadow: "0 4px 24px rgba(0,0,0,0.9)", lineHeight: 1.15, borderLeft: `4px solid ${accent}`, borderRight: `4px solid ${accent}`, padding: "6px 34px" }}>{caption}</div>
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
