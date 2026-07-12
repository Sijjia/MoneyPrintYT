import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";
import { Censored } from "./censor";

export type StatPopProps = {
  value: string;
  label: string;
  suffix?: string;
  countUp?: boolean;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

export const StatPop: React.FC<StatPopProps> = ({
  value,
  label,
  suffix = "",
  countUp = true,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const enter = spring({ frame, fps, config: { damping: 12, mass: 0.8, stiffness: 120 } });
  const numScale = interpolate(enter, [0, 1], [1.18, 1]);
  const numOpacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  const barH = interpolate(enter, [0, 1], [0, 168]);

  const labelOpacity = interpolate(frame, [10, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const labelX = interpolate(enter, [0, 1], [-30, 0]);

  const numTarget = parseInt(value.replace(/\D/g, ""), 10);
  const hasNum = countUp && !Number.isNaN(numTarget);
  const countT = interpolate(frame, [0, 22], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = hasNum ? Math.round(numTarget * countT).toLocaleString("ru-RU") : value;

  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}
      <AbsoluteFill
        style={{
          background:
            "linear-gradient(90deg, rgba(0,0,0,0.74) 0%, rgba(0,0,0,0.38) 34%, transparent 62%)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 150 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 46 }}>
          <div style={{ width: 8, height: barH, background: accent, borderRadius: 4 }} />
          <div>
            <div
              style={{
                opacity: numOpacity,
                transform: `scale(${numScale})`,
                transformOrigin: "left center",
                color: textColor,
                fontSize: 250,
                fontWeight: 800,
                lineHeight: 0.9,
                letterSpacing: -4,
                textShadow: "0 10px 50px rgba(0,0,0,0.7)",
              }}
            >
              {shown}
              <span style={{ color: accent }}>{suffix}</span>
            </div>
            <Censored
              text={label}
              style={{
                opacity: labelOpacity,
                transform: `translateX(${labelX}px)`,
                color: textColor,
                fontSize: 46,
                fontWeight: 600,
                letterSpacing: 2,
                marginTop: 20,
                textTransform: "uppercase",
                textShadow: "0 4px 20px rgba(0,0,0,0.85)",
                display: "inline-block",
              }}
            />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
