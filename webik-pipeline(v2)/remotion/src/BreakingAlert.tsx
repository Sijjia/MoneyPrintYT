import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
  random,
} from "remotion";
import { fontFamily } from "./theme";

export type BreakingAlertProps = {
  kicker?: string;        // «СРОЧНО» / «BREAKING»
  headline: string;       // основная строка
  cities?: number;        // сколько точек на карте пульсирует
  reveal?: string;        // текст-разоблачение (после глитча)
  stamp?: string;         // печать поверх на разоблачении
  showMooninite?: boolean;// пиксельный LED-инопланетянин в разоблачении
  accent?: string;
  lang?: "ru" | "en";     // язык внутренних надписей
};

const BA_L = {
  ru: { threat: "УГРОЗА · МАССОВАЯ ЭВАКУАЦИЯ", tags: ["САПЁРЫ", "ФБР", "ЗАКРЫТЫ МОСТЫ"] },
  en: { threat: "THREAT · MASS EVACUATION", tags: ["BOMB SQUAD", "FBI", "BRIDGES CLOSED"] },
} as const;

// Пиксельный «Mooninite» (Lite-Brite): грубый LED-инопланетянин с поднятой рукой.
const ALIEN = [
  "..GG..GG..",
  ".GGGGGGGG.",
  "GG.GGGG.GG",
  "GGGGGGGGGG",
  "GG.GGGG.GG",
  "GGGGGGGGGG",
  ".G.GGGG.G.",
  "..GGGGGG..",
  ".G..GG..G.",
  "GG..GG..GG",
];

const PixelAlien: React.FC<{ frame: number; start: number }> = ({ frame, start }) => {
  const cell = 26;
  const appear = interpolate(frame, [start, start + 14], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "relative", width: 10 * cell, height: 10 * cell, filter: "drop-shadow(0 0 18px #39ff88)" }}>
      {ALIEN.map((row, y) =>
        row.split("").map((ch, x) => {
          if (ch !== "G") return null;
          const lit = random(`led${x}-${y}-${Math.floor(frame / 4)}`) > 0.12;
          return (
            <div key={`${x}-${y}`} style={{
              position: "absolute", left: x * cell, top: y * cell, width: cell - 4, height: cell - 4,
              background: lit ? "#4dff9a" : "#1f6b40", borderRadius: 4,
              boxShadow: lit ? "0 0 8px #39ff88" : "none",
              opacity: appear,
              transform: `scale(${appear})`,
            }} />
          );
        })
      )}
    </div>
  );
};

export const BreakingAlert: React.FC<BreakingAlertProps> = ({
  kicker = "СРОЧНО", headline, cities = 10, reveal = "", stamp = "",
  showMooninite = false, accent = "#e11d1d", lang = "ru",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const bt = BA_L[lang] || BA_L.ru;
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const revealAt = Math.round(durationInFrames * 0.58);
  const isReveal = frame >= revealAt;
  const glitch = frame >= revealAt - 6 && frame < revealAt + 8;
  const gx = glitch ? (random(`gx${frame}`) - 0.5) * 40 : 0;

  const pulse = 0.5 + 0.5 * Math.sin(frame * 0.35);
  const barIn = interpolate(frame, [0, 10], [-100, 0], { extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const tick = Math.max(0, 180 - Math.floor(frame / 3));   // обратный отсчёт

  // точки «городов» на условной карте
  const dots = Array.from({ length: cities }, (_, i) => ({
    x: 12 + random(`cx${i}`) * 74,
    y: 18 + random(`cy${i}`) * 60,
    boston: i === 0,
    ph: random(`cp${i}`) * 6,
  }));

  const bg = isReveal ? "#04120a" : "#0a0406";
  const showAccent = isReveal ? "#39d98a" : accent;

  return (
    <AbsoluteFill style={{ background: bg, fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      {/* карта-подложка с точками */}
      <AbsoluteFill style={{ opacity: isReveal ? 0.12 : 0.5, transform: `translateX(${gx}px)` }}>
        <svg width={width} height={height} viewBox="0 0 100 100" preserveAspectRatio="none" style={{ position: "absolute", inset: 0 }}>
          <rect width="100" height="100" fill="none" />
          {Array.from({ length: 14 }).map((_, i) => (
            <line key={`h${i}`} x1="0" y1={i * 7} x2="100" y2={i * 7} stroke={showAccent} strokeWidth="0.08" opacity="0.25" />
          ))}
          {Array.from({ length: 20 }).map((_, i) => (
            <line key={`v${i}`} x1={i * 5} y1="0" x2={i * 5} y2="100" stroke={showAccent} strokeWidth="0.08" opacity="0.25" />
          ))}
          {!isReveal && dots.map((d, i) => (
            <g key={i}>
              <circle cx={d.x} cy={d.y} r={0.8 + (0.6 + 0.6 * Math.sin(frame * 0.3 + d.ph)) * (d.boston ? 2.4 : 1.4)}
                fill={d.boston ? "#ff5a5a" : accent} opacity={d.boston ? 0.9 : 0.55} />
              <circle cx={d.x} cy={d.y} r={1.2} fill={d.boston ? "#fff" : accent} opacity="0.8" />
            </g>
          ))}
        </svg>
      </AbsoluteFill>

      {/* скан-лайны */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0px, rgba(0,0,0,0.35) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />

      {/* верхняя красная плашка «СРОЧНО» */}
      {!isReveal && (
        <div style={{ position: "absolute", top: 90, left: 0, right: 0, transform: `translateY(${barIn}px)` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20, background: accent, padding: "16px 60px",
            boxShadow: `0 10px 40px ${accent}66` }}>
            <span style={{ background: "#fff", color: accent, fontWeight: 800, fontSize: 34, padding: "4px 18px", letterSpacing: 3, opacity: 0.3 + 0.7 * pulse }}>
              ● {kicker}
            </span>
            <span style={{ color: "#fff", fontSize: 40, fontWeight: 700, letterSpacing: 2 }}>{bt.threat}</span>
            <span style={{ marginLeft: "auto", color: "#fff", fontSize: 34, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              00:{(tick % 60).toString().padStart(2, "0")}
            </span>
          </div>
        </div>
      )}

      {/* центральный блок */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 120 }}>
        {!isReveal ? (
          <div style={{ textAlign: "center", transform: `translateX(${gx}px)` }}>
            <div style={{ display: "inline-flex", gap: 40, marginBottom: 28, color: accent, fontSize: 30, letterSpacing: 4 }}>
              {bt.tags.map((t, i) => (
                <span key={i} style={{ border: `2px solid ${accent}`, padding: "8px 20px", opacity: interpolate(frame, [14 + i * 5, 22 + i * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{t}</span>
              ))}
            </div>
            <div style={{ color: "#fff", fontSize: 78, fontWeight: 800, lineHeight: 1.04, letterSpacing: -1, textShadow: "0 6px 30px rgba(0,0,0,0.9)", maxWidth: 1500 }}>
              {headline}
            </div>
          </div>
        ) : (
          <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 40, transform: `translateX(${gx}px)` }}>
            {showMooninite && <PixelAlien frame={frame} start={revealAt + 2} />}
            <div style={{ color: "#eafff4", fontSize: 66, fontWeight: 800, textAlign: "center", lineHeight: 1.08, maxWidth: 1500,
              opacity: interpolate(frame, [revealAt + 6, revealAt + 18], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
              textShadow: "0 0 30px rgba(57,217,138,0.4)" }}>
              {reveal}
            </div>
          </div>
        )}
      </AbsoluteFill>

      {/* печать на разоблачении */}
      {isReveal && stamp && (
        <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-end", padding: 90,
          opacity: interpolate(frame, [revealAt + 10, revealAt + 20], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
          <div style={{ color: "#39d98a", border: "5px solid #39d98a", padding: "10px 28px", fontSize: 46, fontWeight: 800,
            letterSpacing: 4, transform: "rotate(-8deg)", borderRadius: 8 }}>{stamp}</div>
        </AbsoluteFill>
      )}

      {/* глитч-полоса на переходе */}
      {glitch && (
        <div style={{ position: "absolute", left: 0, right: 0, top: `${random(`gy${frame}`) * 70 + 15}%`, height: 20 + random(`gh${frame}`) * 40,
          background: "#39d98a", opacity: 0.3, mixBlendMode: "screen", transform: `translateX(${gx * 2}px)` }} />
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.9)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
