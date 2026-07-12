import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";
import { Censored } from "./censor";

export type DonutProportionProps = {
  percent: number;
  label: string;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Кольцо/доля: обод заполняется до процента, крупный % в центре.
export const DonutProportion: React.FC<DonutProportionProps> = ({
  percent,
  label,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const R = 150;
  const C = 2 * Math.PI * R;
  const t = interpolate(frame, [0, 28], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const pct = Math.max(0, Math.min(100, percent));
  const shown = Math.round(pct * t);
  const offset = C * (1 - (pct / 100) * t);

  const labelOpacity = interpolate(frame, [14, 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill
        style={{ background: "radial-gradient(circle at 30% 50%, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.3) 60%, transparent 80%)" }}
      />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-start", paddingLeft: 200 }}>
        <div style={{ position: "relative", width: 360, height: 360 }}>
          <svg width="360" height="360" style={{ transform: "rotate(-90deg)" }}>
            <circle cx="180" cy="180" r={R} fill="none" stroke="rgba(255,255,255,0.16)" strokeWidth="26" />
            <circle
              cx="180"
              cy="180"
              r={R}
              fill="none"
              stroke={accent}
              strokeWidth="26"
              strokeLinecap="round"
              strokeDasharray={C}
              strokeDashoffset={offset}
              style={{ filter: `drop-shadow(0 0 12px ${accent}aa)` }}
            />
          </svg>
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: textColor,
              fontSize: 110,
              fontWeight: 800,
              textShadow: "0 6px 24px rgba(0,0,0,0.8)",
            }}
          >
            {shown}
            <span style={{ color: accent, fontSize: 70 }}>%</span>
          </div>
        </div>
        <Censored
          text={label}
          style={{
            marginTop: 30,
            opacity: labelOpacity,
            color: textColor,
            fontSize: 46,
            fontWeight: 600,
            letterSpacing: 2,
            textTransform: "uppercase",
            display: "inline-block",
            textShadow: "0 3px 16px rgba(0,0,0,0.9)",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
