import React from "react";
import {
  AbsoluteFill,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type AbductionProps = {
  title?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 47.9 + s * 29.3) * 43758.5453;
  return x - Math.floor(x);
};

// Доска пропавших: сетка фото людей со штампами «ПОХИЩЕН», нити расследования, счётчик.
export const Abduction: React.FC<AbductionProps> = ({
  title = "ПОХИЩЕНИЯ",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const drift = Math.sin(frame / 60) * 16;
  const zoom = interpolate(frame, [0, durationInFrames], [1.03, 1.09]);
  const count = Math.round(interpolate(frame, [20, 90], [0, 17], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  const COLS = 6, ROWS = 3;
  const cards = Array.from({ length: COLS * ROWS }).map((_, i) => {
    const col = i % COLS, row = Math.floor(i / COLS);
    const x = 120 + col * 290;
    const y = 150 + row * 300;
    const tilt = (rnd(i, 1) - 0.5) * 5;
    const app = spring({ frame: frame - 6 - i * 2, fps, config: { damping: 15 }, durationInFrames: 16 });
    const kid = i === 8; // выделенная жертва — школьница
    return { x, y, tilt, app, kid, key: i };
  });
  const hub = { x: 120 + 2.5 * 290 + 110, y: 150 + 3 * 300 + 40 };

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 40%, #17100e 0%, #0d0806 55%, #060302 100%)" }} />

      <AbsoluteFill style={{ transform: `translateX(${drift}px) scale(${zoom})` }}>
        {/* нити расследования */}
        <svg style={{ position: "absolute", inset: 0 }} width={1920} height={1080}>
          {cards.filter((c) => c.app > 0.4).map((c) => (
            <line key={c.key} x1={c.x + 110} y1={c.y + 130} x2={hub.x} y2={hub.y} stroke={`${accent}55`} strokeWidth="2" />
          ))}
        </svg>

        {cards.map(({ x, y, tilt, app, kid, key }) => (
          <div key={key} style={{ position: "absolute", left: x, top: y, width: 220, height: 260, transform: `rotate(${tilt}deg) scale(${app})`, opacity: app }}>
            {/* пин */}
            <div style={{ position: "absolute", left: 100, top: -8, width: 18, height: 18, borderRadius: "50%", background: accent, boxShadow: `0 0 10px ${accent}` }} />
            {/* карточка-фото */}
            <div style={{ width: "100%", height: "100%", background: "linear-gradient(180deg,#2a2622,#161310)", border: "6px solid #d8d2c4", boxShadow: "0 12px 30px rgba(0,0,0,0.6)", display: "flex", alignItems: "flex-end", justifyContent: "center", overflow: "hidden" }}>
              <svg width={220} height={220} viewBox="0 0 220 220">
                <ellipse cx="110" cy={kid ? 92 : 82} rx={kid ? 40 : 52} ry={kid ? 46 : 60} fill="#0b0908" />
                <path d={kid ? "M40 220 Q110 150 180 220 Z" : "M24 220 Q110 120 196 220 Z"} fill="#0b0908" />
              </svg>
            </div>
            {/* штамп ПОХИЩЕН */}
            <div style={{ position: "absolute", top: 96, left: -8, right: -8, transform: "rotate(-9deg)", textAlign: "center", color: accent, border: `4px solid ${accent}`, background: "rgba(20,4,4,0.25)", fontSize: 30, fontWeight: 800, letterSpacing: 2, textShadow: `0 0 8px ${accent}` }}>
              {kid ? "13 ЛЕТ" : "ПОХИЩЕН"}
            </div>
          </div>
        ))}
      </AbsoluteFill>

      {/* счётчик */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-end", padding: 60, pointerEvents: "none" }}>
        <div style={{ textAlign: "right" }}>
          <div style={{ color: PALETTE.cream, fontSize: 150, fontWeight: 800, lineHeight: 0.9, textShadow: `0 0 40px ${accent}` }}>{count}</div>
          <div style={{ color: accent, fontSize: 34, letterSpacing: 3, fontWeight: 700 }}>ПОДТВЕРЖДЕНО ЯПОНИЕЙ</div>
          <div style={{ color: "#b8b2a6", fontSize: 26, letterSpacing: 2 }}>· сотни пропали без вести ·</div>
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 60, opacity: interpolate(frame, [18, 36], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 78, fontWeight: 800, letterSpacing: 8, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
          <div style={{ marginTop: 6, color: accent, fontSize: 28, letterSpacing: 4, fontWeight: 600 }}>КРАЛИ ЛЮДЕЙ С УЛИЦ ЧУЖОЙ СТРАНЫ</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
