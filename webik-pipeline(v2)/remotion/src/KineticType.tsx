import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";
import { isSensitive } from "./censor";

// Кинетическая типографика: фраза-герой. Слова влетают снизу со сдвигом, ключевое
// слово крупнее, красным, с коротким «ударом» (шейк). Число — акцент внизу.
export type KineticProps = {
  lines?: string[];
  highlight?: string; // слово(а) для акцента (регистронезависимо)
  stat?: string;
  statLabel?: string;
  accent?: string;
};

const norm = (s: string) => s.replace(/[^0-9a-zа-яё]/gi, "").toLowerCase();

export const KineticType: React.FC<KineticProps> = ({
  lines = ["ФРАЗА"],
  highlight = "",
  stat = "",
  statLabel = "",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const hl = new Set(highlight.split(/\s+/).map(norm).filter(Boolean));

  // разворачиваем в слова с индексом появления
  let idx = 0;
  const rendered = lines.map((line, li) => {
    const words = line.split(/\s+/).filter(Boolean).map((w) => {
      const i = idx++;
      return { w, i, hot: hl.has(norm(w)) };
    });
    return { li, words };
  });

  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const drift = Math.sin(frame / 60) * 6;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#05070c", opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, rgba(217,40,40,0.12) 0%, rgba(0,0,0,0) 60%)" }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `translateX(${drift}px)` }}>
        <div style={{ display: "flex", flexDirection: "column", gap: 6, alignItems: "center" }}>
          {rendered.map(({ li, words }) => (
            <div key={li} style={{ display: "flex", gap: 24, alignItems: "baseline", flexWrap: "wrap", justifyContent: "center" }}>
              {words.map(({ w, i, hot }) => {
                const d = 6 + i * 7;
                const ap = interpolate(frame, [d, d + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
                const y = interpolate(frame, [d, d + 16], [46, 0], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.out(Easing.back(1.6)),
                });
                const shake = hot ? Math.sin((frame - d) * 1.4) * Math.max(0, 6 - (frame - d)) : 0;
                return (
                  <span
                    key={i}
                    style={{
                      display: "inline-block",
                      transform: `translate(${shake}px, ${y}px)`,
                      opacity: ap,
                      color: hot ? accent : PALETTE.cream,
                      fontSize: hot ? 132 : 92,
                      fontWeight: 800,
                      letterSpacing: 2,
                      textTransform: "uppercase",
                      textShadow: hot ? `0 0 40px ${accent}88, 0 10px 40px rgba(0,0,0,0.9)` : "0 10px 40px rgba(0,0,0,0.9)",
                      filter: isSensitive(w) ? "blur(7px)" : "none",
                    }}
                  >
                    {w}
                  </span>
                );
              })}
            </div>
          ))}
        </div>
        {stat && (
          <div style={{ marginTop: 54, display: "flex", alignItems: "baseline", gap: 18, opacity: interpolate(frame, [idx * 7 + 6, idx * 7 + 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
            <span style={{ color: accent, fontSize: 96, fontWeight: 800 }}>{stat}</span>
            {statLabel && <span style={{ color: PALETTE.cream, fontSize: 36, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase", opacity: 0.8 }}>{statLabel}</span>}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
