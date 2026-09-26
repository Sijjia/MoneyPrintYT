import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, enterUp } from "./anim";

export type ThugStranglerProps = {
  kicker?: string;      // «THUGGEE»
  title?: string;       // КАПСОМ
  victims?: number;     // счётчик жертв (из vo)
  victimLabel?: string; // «victims over centuries»
  era?: string;         // «13th–19th c.»
  accent?: string;      // жёлтый румал
  caption?: string;
  durationInFrames?: number;
};

// Тхаги: состаренная карта дорог Индии с узлами-засадами, жёлтый шёлковый румал тянется по кадру,
// счётчик жертв тикает, силуэт Кали фоном. Мрачно-архивная эстетика.
export const ThugStrangler: React.FC<ThugStranglerProps> = ({
  kicker = "THUGGEE",
  title = "THE STRANGLER CULT OF KALI",
  victims = 50000,
  victimLabel = "victims over centuries",
  era = "13th–19th c.",
  accent = "#e5c53a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const intro = interpolate(frame, [0, 22], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const cnt = Math.round(interpolate(frame, [18, 56], [0, victims], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  // жёлтый румал — синусоида-лента поперёк кадра
  const rumal = () => {
    const pts: string[] = [];
    for (let i = 0; i <= 36; i++) {
      const t = i / 36;
      const x = -40 + t * 2000;
      const y = 540 + Math.sin(t * 5 + frame / 16) * 120;
      pts.push(`${x},${y}`);
    }
    return pts.join(" ");
  };

  const nodes = [[430, 400], [640, 560], [560, 760], [900, 470], [1080, 660], [1280, 420], [1420, 640], [1120, 300]];

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #241d10 0%, #17110a 55%, #0a0705 100%)" }} />
      {/* силуэт Кали фоном */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: intro * 0.12 }}>
        <g fill="#000" transform="translate(960,120)">
          <circle cx="0" cy="120" r="90" />
          <path d="M0,210 L0,620 M0,300 L-220,420 M0,300 L220,420 M0,300 L-260,300 M0,300 L260,300 M0,300 L-200,180 M0,300 L200,180" stroke="#000" strokeWidth="46" />
          <circle cx="-40" cy="110" r="12" fill={accent} /><circle cx="40" cy="110" r="12" fill={accent} />
        </g>
      </svg>

      {/* карта дорог Индии */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: intro }}>
        {/* грубый контур Индии */}
        <path d="M700,250 Q560,320 560,430 Q540,560 640,700 Q760,880 940,940 Q1020,860 1060,720 Q1160,700 1240,560 Q1340,470 1300,360 Q1180,300 1060,320 Q900,240 700,250 Z"
          fill="none" stroke="#5a4a2a" strokeWidth="3" opacity="0.6" />
        {/* дороги-паутина */}
        {nodes.map((a, i) => nodes.slice(i + 1).map((b, j) => (
          <line key={`${i}-${j}`} x1={a[0]} y1={a[1]} x2={b[0]} y2={b[1]} stroke="#6a5320" strokeWidth="1" opacity="0.25" strokeDasharray="4 8" />
        )))}
        {/* узлы-засады */}
        {nodes.map(([x, y], i) => {
          const on = interpolate(frame, [24 + i * 5, 40 + i * 5], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.backOut });
          const pulse = 0.6 + 0.4 * Math.sin((frame + i * 18) / 8);
          return (
            <g key={i} opacity={on}>
              <circle cx={x} cy={y} r={6 + pulse * 4} fill="none" stroke="#c0341f" strokeWidth="2" opacity="0.5" />
              <circle cx={x} cy={y} r="5" fill="#d23a22" style={{ filter: "drop-shadow(0 0 6px #d23a22)" }} />
            </g>
          );
        })}
      </svg>

      {/* жёлтый румал */}
      <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0, opacity: intro }}>
        <polyline points={rumal()} fill="none" stroke={accent} strokeWidth="22" strokeLinecap="round" opacity="0.85"
          style={{ filter: `drop-shadow(0 4px 10px rgba(0,0,0,0.6))` }} />
        <polyline points={rumal()} fill="none" stroke="#fff4c0" strokeWidth="4" strokeLinecap="round" opacity="0.4" />
      </svg>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "76px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 10, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker} · {era}</div>
          <div style={{ color: "#f4ecd2", fontSize: 68, fontWeight: 700, lineHeight: 1.02, textShadow: "0 6px 30px rgba(0,0,0,0.85)", maxWidth: 1080, marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {/* счётчик жертв */}
      <div style={{ position: "absolute", right: 90, bottom: 150, textAlign: "right", opacity: intro * exit }}>
        <div style={{ color: "#fff", fontSize: 92, fontWeight: 800, fontVariantNumeric: "tabular-nums", textShadow: `0 0 26px #c0341f`, fontFamily: fontFamily("oswald") }}>{cnt.toLocaleString("ru-RU")}</div>
        <div style={{ color: accent, fontSize: 26, fontWeight: 600, letterSpacing: 1 }}>{victimLabel}</div>
      </div>

      {caption && (
        <div style={{ position: "absolute", left: 90, right: 620, bottom: 66, textAlign: "left",
          color: "#eaddc0", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [40, 54], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
