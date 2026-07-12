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

export type CountUpBarProps = {
  value: string;
  label: string;
  suffix?: string;
  /** Если задан — шкала заполняется до value/max (доля). Иначе до 100%. */
  max?: number | null;
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Счётчик + шкала: число накручивается, под ним растёт «мера» — масштаб числа.
export const CountUpBar: React.FC<CountUpBarProps> = ({
  value,
  label,
  suffix = "",
  max = null,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const target = parseInt(value.replace(/\D/g, ""), 10);
  const hasNum = !Number.isNaN(target);
  const t = interpolate(frame, [0, 24], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = hasNum ? Math.round(target * t).toLocaleString("ru-RU") : value;

  const fullPct = max && hasNum ? Math.min(1, target / max) : 1;
  const barW = fullPct * t * 900; // px ширина шкалы

  const numOpacity = interpolate(frame, [0, 8], [0, 1], { extrapolateRight: "clamp" });
  const labelOpacity = interpolate(frame, [10, 24], [0, 1], {
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
        style={{
          background:
            "linear-gradient(90deg, rgba(0,0,0,0.74) 0%, rgba(0,0,0,0.4) 40%, transparent 68%)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 150 }}>
        <div
          style={{
            opacity: numOpacity,
            color: textColor,
            fontSize: 230,
            fontWeight: 800,
            lineHeight: 0.9,
            letterSpacing: -4,
            textShadow: "0 10px 50px rgba(0,0,0,0.7)",
          }}
        >
          {shown}
          <span style={{ color: accent }}>{suffix}</span>
        </div>
        {/* шкала */}
        <div
          style={{
            marginTop: 30,
            width: 900,
            height: 14,
            borderRadius: 8,
            background: "rgba(255,255,255,0.14)",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: barW,
              height: "100%",
              borderRadius: 8,
              background: `linear-gradient(90deg, ${accent}, ${accent}cc)`,
              boxShadow: `0 0 18px ${accent}aa`,
            }}
          />
        </div>
        <Censored
          text={label}
          style={{
            marginTop: 22,
            opacity: labelOpacity,
            color: textColor,
            fontSize: 44,
            fontWeight: 600,
            letterSpacing: 2,
            textTransform: "uppercase",
            display: "inline-block",
            textShadow: "0 4px 20px rgba(0,0,0,0.85)",
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
