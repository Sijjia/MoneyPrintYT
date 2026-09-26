import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type QuoteCardDWProps = {
  text?: string;
  author?: string;
  accent?: string;
};

// Знаменитая реплика: «Они были всего лишь рабами» и т.п. Медленное проявление слов.
export const QuoteCardDW: React.FC<QuoteCardDWProps> = ({
  text = "Они были всего лишь рабами.",
  author = "«ПРИНЦ ЕГИПТА», 1998", accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const words = text.split(" ");

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit,
      background: "radial-gradient(ellipse at 50% 42%, #101014 0%, #08080b 60%, #040405 100%)" }}>
      <AbsoluteFill style={{ opacity: 0.04, backgroundImage:
        "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 4px)" }} />
      {/* большая кавычка */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", flexDirection: "column", padding: "0 12%" }}>
        <div style={{ color: accent, fontSize: 220, lineHeight: 0.6, marginBottom: 10, opacity: 0.5,
          fontFamily: "Georgia, serif" }}>“</div>
        <div style={{ textAlign: "center", fontFamily: "Georgia, serif", fontStyle: "italic",
          color: "#f2f2f4", fontSize: 74, fontWeight: 600, lineHeight: 1.2, maxWidth: "80%" }}>
          {words.map((w, i) => {
            const show = interpolate(frame, [8 + i * 5, 20 + i * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return <span key={i} style={{ opacity: show }}>{w}{" "}</span>;
          })}
        </div>
        <div style={{ marginTop: 44, color: accent, fontSize: 26, fontWeight: 700, letterSpacing: 4,
          opacity: interpolate(frame, [8 + words.length * 5, 24 + words.length * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
          — {author}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.75)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
