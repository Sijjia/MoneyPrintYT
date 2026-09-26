import React from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { CameraMotionBlur } from "@remotion/motion-blur";
import { fontFamily } from "./theme";
import { enterUp } from "./anim";

export type NagaUnderworldProps = {
  kicker?: string;      // «ПATALA» / «ПОДЗЕМНЫЙ МИР»
  title?: string;       // КАПСОМ
  layers?: string[];    // подписи 7 нижних миров (опц.)
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

const DEF_LAYERS = ["ATALA", "VITALA", "SUTALA", "TALATALA", "MAHATALA", "RASATALA", "PATALA"];

// Патала: спуск сквозь 7 подземных миров к царству нагов — светящаяся кобра-змей, золото, каменные
// слои, холодная бирюза сверху → тёплое золото у дна. Камера ныряет вниз.
export const NagaUnderworld: React.FC<NagaUnderworldProps> = ({
  kicker = "ПATALA",
  title = "THE UNDERWORLD OF SERPENT BEINGS",
  layers,
  accent = "#e8b84a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const intro = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const dive = interpolate(frame, [0, durationInFrames], [0, 620], { easing: Easing.inOut(Easing.cubic) });
  const L = (layers && layers.length ? layers : DEF_LAYERS).slice(0, 7);

  // синусоидальное тело кобры, извивается по кадру
  const serpent = () => {
    const pts: string[] = [];
    for (let i = 0; i <= 40; i++) {
      const t = i / 40;
      const x = 300 + t * 1320;
      const y = 300 + Math.sin(t * 7 + frame / 14) * 210 + t * 340;
      pts.push(`${x},${y}`);
    }
    return pts.join(" ");
  };

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#06171c 0%,#08222a 22%,#0a1f24 44%,#140f10 66%,#2a1706 84%,#3a2007 100%)" }} />

      <CameraMotionBlur shutterAngle={200} samples={6}>
      <AbsoluteFill style={{ transform: `translateY(${-dive}px)`, opacity: intro }}>
        {/* каменные слои-миры */}
        <svg width={1920} height={1900} viewBox="0 0 1920 1900" style={{ position: "absolute", left: 0, top: 0 }}>
          {L.map((nm, i) => {
            const y = 260 + i * 220;
            const warm = i / 6;
            const col = `rgb(${40 + warm * 90},${34 + warm * 24},${28 + warm * 6})`;
            const on = interpolate(frame, [10 + i * 6, 26 + i * 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return (
              <g key={i} opacity={on}>
                <path d={`M0,${y} Q480,${y - 26} 960,${y} T1920,${y} L1920,${y + 30} L0,${y + 30} Z`} fill={col} opacity="0.55" />
                <line x1="120" y1={y} x2="1800" y2={y} stroke={accent} strokeWidth="1" strokeDasharray="3 10" opacity="0.35" />
                <text x="1700" y={y - 12} fill={accent} fontSize="22" fontWeight="700" textAnchor="end" opacity="0.7" style={{ fontFamily: fontFamily("oswald") }}>{nm}</text>
              </g>
            );
          })}
        </svg>

        {/* тело кобры-нага */}
        <svg width={1920} height={1900} viewBox="0 0 1920 1900" style={{ position: "absolute", left: 0, top: 0 }}>
          <defs>
            <linearGradient id="nagaBody" x1="0" y1="0" x2="1" y2="1">
              <stop offset="0" stopColor="#2fbf9a" /><stop offset="0.6" stopColor="#1c7f8f" /><stop offset="1" stopColor={accent} />
            </linearGradient>
          </defs>
          <polyline points={serpent()} fill="none" stroke="url(#nagaBody)" strokeWidth="30" strokeLinecap="round" opacity="0.9"
            style={{ filter: `drop-shadow(0 0 16px ${accent}88)` }} />
          <polyline points={serpent()} fill="none" stroke="#dffff5" strokeWidth="4" strokeLinecap="round" opacity="0.5" />
        </svg>

        {/* золотые искры-сокровища у дна */}
        {Array.from({ length: 34 }).map((_, i) => {
          const x = (i * 137.5) % 1920;
          const y = 900 + ((i * 240.7) % 900);
          const g = 0.4 + 0.6 * Math.sin((frame + i * 15) / 9);
          return <div key={i} style={{ position: "absolute", left: x, top: y, width: 5, height: 5, borderRadius: "50%", background: "#ffe9ad", boxShadow: `0 0 ${8 + g * 12}px ${accent}`, opacity: 0.6 * g }} />;
        })}
      </AbsoluteFill>
      </CameraMotionBlur>

      {/* капюшон кобры (фиксированный, «смотрит» на зрителя внизу) */}
      <svg width={520} height={420} viewBox="0 0 520 420" style={{ position: "absolute", left: "50%", bottom: 120, transform: "translateX(-50%)", opacity: intro * interpolate(frame, [30, 55], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
        <path d="M260,400 C250,300 130,280 150,150 C160,70 230,40 260,40 C290,40 360,70 370,150 C390,280 270,300 260,400 Z" fill="url(#nagaBody)" opacity="0.9" stroke={accent} strokeWidth="3" />
        <circle cx="215" cy="150" r="14" fill="#ffdf7a" style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
        <circle cx="305" cy="150" r="14" fill="#ffdf7a" style={{ filter: `drop-shadow(0 0 8px ${accent})` }} />
        <circle cx="215" cy="150" r="5" fill="#1a0e00" /><circle cx="305" cy="150" r="5" fill="#1a0e00" />
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", padding: "70px 90px 0", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 130, damping: 17 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 10, textAlign: "center", opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f4ecda", fontSize: 66, fontWeight: 700, letterSpacing: 1, textAlign: "center", textShadow: "0 6px 34px rgba(0,0,0,0.9)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", padding: "0 200px",
          color: "#eadfc8", fontSize: 34, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [30, 46], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
