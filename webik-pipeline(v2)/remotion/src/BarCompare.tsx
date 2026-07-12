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

export type BarItem = { label: string; value: number };
export type BarCompareProps = {
  title?: string;
  items: BarItem[];
  bgImage?: string | null;
  accent?: string;
  textColor?: string;
  font?: FontName;
};

// Сравнение величин: подписанные бары растут, топ выделен акцентом.
export const BarCompare: React.FC<BarCompareProps> = ({
  title = "",
  items,
  bgImage = null,
  accent = PALETTE.red,
  textColor = PALETTE.cream,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const sorted = [...items].sort((a, b) => b.value - a.value).slice(0, 4);
  const maxV = Math.max(1, ...sorted.map((i) => i.value));

  const titleOpacity = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
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
            "linear-gradient(90deg, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0.5) 50%, rgba(0,0,0,0.25) 100%)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", paddingLeft: 150, paddingRight: 200 }}>
        {title && (
          <Censored
            text={title}
            style={{
              opacity: titleOpacity,
              color: textColor,
              fontSize: 52,
              fontWeight: 700,
              letterSpacing: 1,
              marginBottom: 40,
              textTransform: "uppercase",
              display: "inline-block",
              textShadow: "0 4px 20px rgba(0,0,0,0.85)",
            }}
          />
        )}
        {sorted.map((it, i) => {
          const delay = 8 + i * 7;
          const g = interpolate(frame, [delay, delay + 20], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          });
          const w = (it.value / maxV) * g * 1180;
          const shown = Math.round(it.value * g).toLocaleString("ru-RU");
          const isTop = i === 0;
          const barColor = isTop ? accent : "rgba(255,255,255,0.32)";
          return (
            <div key={i} style={{ marginBottom: 26 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 20 }}>
                <div
                  style={{
                    width: 340,
                    color: textColor,
                    fontSize: 40,
                    fontWeight: 600,
                    textAlign: "right",
                    opacity: interpolate(g, [0, 0.3], [0, 1]),
                    textShadow: "0 3px 14px rgba(0,0,0,0.9)",
                    whiteSpace: "nowrap",
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                  }}
                >
                  {it.label}
                </div>
                <div
                  style={{
                    height: 52,
                    width: w,
                    borderRadius: 6,
                    background: barColor,
                    boxShadow: isTop ? `0 0 22px ${accent}aa` : "none",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "flex-end",
                    paddingRight: 16,
                  }}
                >
                  <span
                    style={{
                      color: isTop ? "#fff" : textColor,
                      fontSize: 34,
                      fontWeight: 800,
                      opacity: interpolate(g, [0.5, 1], [0, 1], { extrapolateLeft: "clamp" }),
                    }}
                  >
                    {shown}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
