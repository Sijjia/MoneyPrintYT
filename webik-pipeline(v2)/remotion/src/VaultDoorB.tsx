import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { mspring, enterUp } from "./anim";

export type VaultDoorBProps = {
  kicker?: string;      // «PADMANABHASWAMY»
  title?: string;       // КАПСОМ
  valueText?: string;   // «$22 МЛРД» — оценка вскрытых 5 комнат
  valueLabel?: string;  // «5 из 6 комнат вскрыто»
  doorLabel?: string;   // «VAULT B — SEALED»
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

// Храм Падманабхасвами: массивная каменная дверь-B с двумя сплетёнными кобрами, золотой свет
// сочится из щелей, счётчик стоимости вскрытых комнат тикает. Наезд на печать двери.
export const VaultDoorB: React.FC<VaultDoorBProps> = ({
  kicker = "PADMANABHASWAMY",
  title = "THE DOOR THAT MUST NOT BE OPENED",
  valueText = "$22 000 000 000",
  valueLabel = "estimate of five opened chambers",
  doorLabel = "VAULT B — SEALED",
  accent = "#e3b23c",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const intro = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.08]);
  const glow = 0.5 + 0.5 * Math.sin(frame / 12);
  // счётчик $ тикает
  const val = valueText.replace(/[^0-9]/g, "");
  const cnt = Math.round(interpolate(frame, [16, 52], [0, parseInt(val || "0", 10)], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const fmt = "$" + cnt.toLocaleString("ru-RU");

  const Cobra = ({ flip }: { flip: number }) => (
    <g transform={`translate(410,0) scale(${flip},1)`}>
      <path d="M0,760 C-60,620 60,560 -30,420 C-70,350 -20,300 30,300 C70,300 110,340 96,410 C70,540 150,600 90,740"
        fill="none" stroke={accent} strokeWidth="14" strokeLinecap="round" opacity="0.85" style={{ filter: `drop-shadow(0 0 ${6 + glow * 6}px ${accent})` }} />
      <path d="M30,300 c-26,0 -40,-24 -40,-44 c0,-16 18,-30 40,-30 c22,0 40,14 40,30 c0,20 -14,44 -40,44 Z" fill={accent} opacity="0.9" />
      <circle cx="18" cy="256" r="5" fill="#1a0e00" /><circle cx="42" cy="256" r="5" fill="#1a0e00" />
    </g>
  );

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #241a10 0%, #140d07 60%, #080503 100%)" }} />

      <AbsoluteFill style={{ transform: `scale(${zoom})`, opacity: intro, justifyContent: "center", alignItems: "center" }}>
        <svg width={900} height={980} viewBox="0 0 900 980" style={{ filter: "drop-shadow(0 30px 80px rgba(0,0,0,0.8))" }}>
          {/* каменный портал */}
          <rect x="80" y="40" width="740" height="900" rx="10" fill="#2c2620" stroke="#5a4a2e" strokeWidth="6" />
          <rect x="120" y="80" width="660" height="820" rx="6" fill="#211c17" stroke="#3d3226" strokeWidth="3" />
          {/* резьба-орнамент по краю */}
          {Array.from({ length: 18 }).map((_, i) => (
            <circle key={i} cx={i % 2 ? 140 : 760} cy={110 + Math.floor(i / 2) * 90} r="6" fill={accent} opacity="0.4" />
          ))}
          {/* две створки */}
          <line x1="450" y1="80" x2="450" y2="900" stroke="#0a0704" strokeWidth="5" />
          {/* золотой свет из щели */}
          <rect x="446" y="90" width="8" height="800" fill={accent} opacity={0.5 + glow * 0.5} style={{ filter: `blur(4px)` }} />
          {/* сплетённые кобры */}
          <Cobra flip={1} /><Cobra flip={-1} />
          {/* печать по центру */}
          <circle cx="450" cy="490" r="60" fill="#1a1510" stroke={accent} strokeWidth="3" opacity="0.9" />
          <text x="450" y="505" fill={accent} fontSize="54" fontWeight="800" textAnchor="middle" style={{ fontFamily: fontFamily("oswald") }}>B</text>
        </svg>
      </AbsoluteFill>

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "70px 84px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 28, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f6ecd4", fontSize: 62, fontWeight: 700, lineHeight: 1.03, textShadow: "0 6px 30px rgba(0,0,0,0.85)", maxWidth: 720, marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {/* счётчик стоимости (справа) */}
      <div style={{ position: "absolute", right: 90, top: 360, textAlign: "right", opacity: intro * exit }}>
        <div style={{ color: "#fff", fontSize: 78, fontWeight: 800, fontVariantNumeric: "tabular-nums", textShadow: `0 0 26px ${accent}`, fontFamily: fontFamily("oswald") }}>{fmt}</div>
        <div style={{ color: accent, fontSize: 26, fontWeight: 600, letterSpacing: 1 }}>{valueLabel}</div>
        {(() => { const d = mspring(frame, 30, { stiffness: 170, damping: 12, delay: 42 }); return (
        <div style={{ marginTop: 22, display: "inline-block", background: "#7a1414", color: "#ffd7d7", fontSize: 26, fontWeight: 800, letterSpacing: 2, padding: "10px 20px", borderRadius: 6, opacity: Math.min(1, d), transform: `scale(${0.8 + d * 0.2})` }}>{doorLabel}</div>
        ); })()}
      </div>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", padding: "0 200px",
          color: "#ecdfc4", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [46, 60], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
