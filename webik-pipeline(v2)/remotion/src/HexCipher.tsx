import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  random,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type HexCipherProps = {
  subreddit?: string;       // «r/A858DE45F56D9BC9»
  decoded?: string;         // расшифрованное послание, которое проявляется
  label?: string;           // «РАСШИФРОВАНО» / «ФРАГМЕНТ ДЕКОДИРОВАН»
  status?: string;          // нижняя строка-статус
  accent?: string;
  caption?: string;
};

const HEX = "0123456789abcdef";
function hexLine(seed: number, len: number): string {
  let s = "";
  for (let i = 0; i < len; i++) s += HEX[Math.floor(random(`${seed}-${i}`) * 16)];
  return s.replace(/(.{2})/g, "$1 ").trim();
}

// Зашифрованный сабреддит: стены гекс-кода, часть которых «расшифровывается» в послание.
export const HexCipher: React.FC<HexCipherProps> = ({
  subreddit = "r/A858DE45F56D9BC9",
  decoded = "WE CANNOT DISCLOSE THE PURPOSE",
  label = "FRAGMENT DECODED",
  status = "Project A858 concluded.",
  accent = "#5f9d84",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const rows = 16, cols = 34;
  const scroll = (frame * 0.6) % 1;
  const revealAt = 34; // кадр, когда часть кода складывается в текст
  const decodeGlow = interpolate(frame, [revealAt, revealAt + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#020403", fontFamily: fontFamily("system"), opacity: exit, overflow: "hidden" }}>
      {/* стены гекс-кода */}
      <AbsoluteFill style={{ padding: "40px 60px", opacity: 0.5 }}>
        {Array.from({ length: rows }).map((_, r) => {
          const y = ((r - scroll) / rows) * 100;
          const nearCenter = Math.abs(r - rows / 2) < 2;
          return (
            <div key={r} style={{
              position: "absolute", top: `${y}%`, left: 60, right: 60,
              color: nearCenter ? "#3a6b54" : "#20402f",
              fontSize: 30, letterSpacing: 4, fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap",
              opacity: nearCenter ? 0.15 : 0.5,
            }}>{hexLine(r * 7 + Math.floor(frame / 30), cols)}</div>
          );
        })}
      </AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, transparent 20%, rgba(0,0,0,0.85) 75%)" }} />
      {/* скан-лайн */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />

      {/* сабреддит-заголовок */}
      <div style={{ position: "absolute", top: 90, left: 0, right: 0, textAlign: "center",
        opacity: interpolate(frame, [4, 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <span style={{ color: "#6d9585", fontSize: 40, fontWeight: 700, letterSpacing: 2, textShadow: `0 0 6px ${accent}` }}>{subreddit}</span>
      </div>

      {/* центральное расшифрованное послание */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{
          border: `2px solid ${accent}`, background: "rgba(2,20,10,0.82)", padding: "26px 52px", borderRadius: 6,
          boxShadow: `0 0 ${14 * decodeGlow}px ${accent}44`, opacity: decodeGlow,
          transform: `scale(${interpolate(decodeGlow, [0, 1], [0.92, 1])})`,
        }}>
          <div style={{ color: "#8fae9f", fontSize: 24, letterSpacing: 6, marginBottom: 12, textAlign: "center" }}>{label}</div>
          <div style={{ color: "#dfe9e3", fontSize: 62, fontWeight: 800, letterSpacing: 3, textAlign: "center", textShadow: `0 0 6px ${accent}` }}>
            {decoded.slice(0, Math.max(0, Math.floor(interpolate(frame, [revealAt + 4, revealAt + 30], [0, decoded.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }))))}
            <span style={{ opacity: frame % 20 < 10 ? 1 : 0 }}>▊</span>
          </div>
        </div>
      </AbsoluteFill>

      {/* статус снизу */}
      <div style={{ position: "absolute", bottom: 140, left: 0, right: 0, textAlign: "center",
        opacity: interpolate(frame, [durationInFrames - 60, durationInFrames - 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
        <span style={{ color: "#6d9585", fontSize: 34, fontWeight: 600, letterSpacing: 2 }}>{status}</span>
      </div>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 56,
          opacity: interpolate(frame, [24, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1480, textAlign: "center", color: "#cfe8d8", fontSize: 34, fontWeight: 500, textShadow: "0 4px 20px rgba(0,0,0,0.9)" }}>{caption}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
