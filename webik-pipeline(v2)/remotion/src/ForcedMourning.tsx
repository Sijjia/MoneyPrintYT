import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type ForcedMourningProps = {
  title?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 41.3 + s * 71.9) * 43758.5453;
  return x - Math.floor(x);
};

// Принудительный траур: толпа склонённых силуэтов под гигантским портретом и камерами.
export const ForcedMourning: React.FC<ForcedMourningProps> = ({
  title = "СЛЁЗЫ ПОД НАДЗОРОМ",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const intro = interpolate(frame, [0, 20], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const crane = interpolate(frame, [0, durationInFrames], [-260, 40]); // камера опускается к толпе
  const push = interpolate(frame, [0, durationInFrames], [0, 500]);

  // толпа склонённых голов рядами в глубину
  const ROWS = 7, PER = 13;
  const crowd: { x: number; z: number; bow: number; key: string }[] = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < PER; c++) {
      const x = (c - (PER - 1) / 2) * 190 + (r % 2) * 95;
      const z = -200 - r * 300;
      const bow = 6 + Math.sin(frame / 20 + r + c) * 4; // покачивание «рыданий»
      crowd.push({ x, z, bow, key: `${r}-${c}` });
    }
  }

  // камеры слежения по бокам
  const cams = [[-1, "18%"], [1, "18%"], [-1, "42%"], [1, "42%"]] as const;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg, #0a0d12 0%, #0b0607 55%, #050202 100%)" }} />
      {/* холодный прожектор на портрет */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 20%, rgba(150,170,200,0.16), transparent 45%)" }} />

      {/* гигантский портрет вождя */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "center", paddingTop: 40, opacity: intro }}>
        <div style={{ width: 360, height: 460, background: "linear-gradient(180deg,#1a1110,#0a0605)", border: `12px solid ${PALETTE.gold}`, boxShadow: `0 0 80px rgba(0,0,0,0.8), 0 0 50px ${accent}44`, display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
          <svg width={360} height={400} viewBox="0 0 360 400">
            <ellipse cx="180" cy="150" rx="92" ry="110" fill="#000" opacity="0.85" />
            <path d="M46 400 Q180 230 314 400 Z" fill="#000" opacity="0.85" />
          </svg>
        </div>
      </AbsoluteFill>

      {/* 3D толпа */}
      <AbsoluteFill style={{ perspective: 1100, opacity: intro }}>
        <div style={{ position: "absolute", left: "50%", top: "66%", transformStyle: "preserve-3d", transform: `translate(-50%,-50%) rotateX(${crane}deg) translateZ(${push}px)` }}>
          {crowd.map(({ x, z, bow, key }) => (
            <div key={key} style={{ position: "absolute", transform: `translate3d(${x}px, 0px, ${z}px)` }}>
              <svg width={120} height={150} viewBox="0 0 120 150" style={{ transform: `translateX(-60px) translateY(-120px) rotate(${bow}deg)`, transformOrigin: "60px 140px" }}>
                {/* склонённая голова + плечи */}
                <ellipse cx="60" cy="52" rx="30" ry="34" fill="#000" opacity="0.9" />
                <path d="M14 150 Q60 80 106 150 Z" fill="#0a0808" opacity="0.92" />
                {/* красная «слеза» */}
                <circle cx="70" cy="66" r="3.4" fill={accent} opacity={0.6 + rnd(x + z, 1) * 0.4} />
              </svg>
            </div>
          ))}
        </div>
      </AbsoluteFill>

      {/* камеры слежения */}
      {cams.map(([side, top], i) => (
        <div key={i} style={{ position: "absolute", top, left: side < 0 ? "8%" : undefined, right: side > 0 ? "8%" : undefined, opacity: intro }}>
          <svg width={130} height={80} viewBox="0 0 130 80" style={{ transform: `scaleX(${side})`, filter: `drop-shadow(0 0 10px ${accent})` }}>
            <rect x="10" y="24" width="74" height="34" rx="6" fill="#140606" stroke={accent} strokeWidth="2.5" />
            <polygon points="84,30 118,20 118,62 84,52" fill="#140606" stroke={accent} strokeWidth="2.5" />
            <circle cx="112" cy="41" r="7" fill={accent} style={{ opacity: 0.5 + 0.5 * Math.abs(Math.sin(frame / 8 + i)) }} />
            <line x1="30" y1="58" x2="30" y2="76" stroke={accent} strokeWidth="3" />
          </svg>
        </div>
      ))}

      {/* красные лучи-слёзы сверху */}
      <AbsoluteFill style={{ opacity: 0.4 * intro, pointerEvents: "none" }}>
        {Array.from({ length: 5 }).map((_, i) => (
          <div key={i} style={{ position: "absolute", left: `${20 + i * 15}%`, top: "12%", width: 3, height: `${30 + rnd(i, 3) * 20}%`, background: `linear-gradient(180deg, ${accent}, transparent)`, opacity: 0.5 }} />
        ))}
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 340px rgba(0,0,0,0.9)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 84, opacity: interpolate(frame, [18, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 80, fontWeight: 800, letterSpacing: 6, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
          <div style={{ marginTop: 8, color: accent, fontSize: 32, letterSpacing: 5, fontWeight: 600 }}>АРЕСТ ЗА СУХИЕ ГЛАЗА</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
