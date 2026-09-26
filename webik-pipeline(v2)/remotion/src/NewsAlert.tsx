import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { fontFamily } from "./theme";

export type NewsAlertProps = {
  kicker?: string;          // «СРОЧНО» / «АРЕСТ» / «СУД»
  headline: string;         // заголовок новости
  outlet?: string;          // «BleepingComputer» / «Bloomberg» / «Reuters»
  location?: string;        // «Львов, Украина» / «Техас, США»
  caption?: string;         // фраза снизу
  accent?: string;
};

// Новостная плашка под реальные события: аресты, иски, расследования. Строгий «breaking news» вид.
export const NewsAlert: React.FC<NewsAlertProps> = ({
  kicker = "BREAKING", headline, outlet = "", location = "", caption = "", accent = "#c8161d",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height, fps } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const barIn = spring({ frame: frame - 4, fps, config: { damping: 14, stiffness: 150 } });
  const pulse = 0.5 + 0.5 * Math.sin(frame * 0.35);
  const clock = `${Math.floor(frame / 30).toString().padStart(2, "0")}:${((frame * 2) % 60).toString().padStart(2, "0")}`;

  return (
    <AbsoluteFill style={{ background: "#0a0a0c", fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      {/* лёгкий «студийный» градиент + шум-развёртка */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 30%, #16181f 0%, #0a0a0c 65%)" }} />
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.30) 0px, rgba(0,0,0,0.30) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />

      {/* верхняя строка-тикер */}
      <div style={{ position: "absolute", top: 70, left: 0, right: 0, opacity: barIn }}>
        <div style={{ display: "flex", alignItems: "center", gap: 18, background: accent, padding: "14px 60px", transform: `translateY(${interpolate(barIn, [0, 1], [-90, 0])}px)` }}>
          <span style={{ background: "#fff", color: accent, fontWeight: 800, fontSize: 34, padding: "4px 18px", letterSpacing: 3, opacity: 0.35 + 0.65 * pulse }}>● {kicker}</span>
          {location && <span style={{ color: "#fff", fontSize: 34, fontWeight: 600, letterSpacing: 2 }}>{location}</span>}
          <span style={{ marginLeft: "auto", color: "#fff", fontSize: 30, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>LIVE {clock}</span>
        </div>
      </div>

      {/* центр — заголовок */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 130px" }}>
        <div style={{ color: "#fff", fontSize: 80, fontWeight: 800, textAlign: "center", lineHeight: 1.06, letterSpacing: -1, textShadow: "0 8px 34px rgba(0,0,0,0.9)", maxWidth: 1560,
          opacity: interpolate(frame, [12, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
          transform: `translateY(${interpolate(frame, [12, 26], [24, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}px)` }}>
          {headline}
        </div>
      </AbsoluteFill>

      {/* нижняя плашка «источник» (lower third) */}
      <div style={{ position: "absolute", bottom: 150, left: 0, right: 0, opacity: interpolate(frame, [22, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <div style={{ display: "flex", alignItems: "center" }}>
          <div style={{ background: accent, color: "#fff", fontSize: 30, fontWeight: 800, letterSpacing: 3, padding: "12px 28px" }}>FACT</div>
          <div style={{ background: "rgba(0,0,0,0.85)", color: "#e8e8e8", fontSize: 30, fontWeight: 500, letterSpacing: 1, padding: "12px 28px", flex: 1, borderBottom: `3px solid ${accent}` }}>
            {outlet ? `Source: ${outlet}` : "A real documented case"}
          </div>
        </div>
      </div>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 60,
          opacity: interpolate(frame, [24, 38], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1500, textAlign: "center", color: "#cfd3da", fontSize: 34, fontWeight: 500, textShadow: "0 4px 20px rgba(0,0,0,0.9)" }}>{caption}</div>
        </AbsoluteFill>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
