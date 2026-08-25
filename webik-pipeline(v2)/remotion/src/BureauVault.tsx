import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type BureauVaultProps = {
  title?: string;
  accent?: string;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 91.7 + s * 47.3) * 43758.5453;
  return x - Math.floor(x);
};

// Тёмное хранилище Бюро 39: падающие фальшивые доллары в 3D + красный «лёд» (мет).
export const BureauVault: React.FC<BureauVaultProps> = ({
  title = "БЮРО 39",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const green = "#3e6b4d";

  const intro = interpolate(frame, [0, 18], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 18, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const push = interpolate(frame, [0, durationInFrames], [0, 900]);

  const bills = Array.from({ length: 40 }).map((_, i) => {
    const x = (rnd(i, 1) - 0.5) * 1900;
    const z = -200 - rnd(i, 2) * 1600;
    const speed = 120 + rnd(i, 3) * 220;
    const fall = ((frame * speed) / 30 + rnd(i, 4) * 1200) % 1500 - 250;
    const rot = frame * (1 + rnd(i, 5) * 2) + rnd(i, 6) * 360;
    const rotY = frame * (0.6 + rnd(i, 7)) * (rnd(i, 8) > 0.5 ? 1 : -1);
    return { x, y: fall, z, rot, rotY, key: i };
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 50% 45%, #1c0a06 0%, #0e0503 55%, #050201 100%)" }} />
      {/* дверь сейфа */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 0.4 * intro }}>
        <svg width={760} height={760} viewBox="-380 -380 760 760">
          <circle r="360" fill="none" stroke={accent} strokeWidth="6" opacity="0.5" />
          <circle r="300" fill="none" stroke={accent} strokeWidth="3" opacity="0.4" />
          {Array.from({ length: 12 }).map((_, i) => {
            const a = (i / 12) * Math.PI * 2;
            return <circle key={i} cx={Math.cos(a) * 330} cy={Math.sin(a) * 330} r="10" fill={accent} opacity="0.6" />;
          })}
          <g style={{ transformOrigin: "center", transform: `rotate(${frame * 0.6}deg)` }}>
            <line x1="-120" y1="0" x2="120" y2="0" stroke={accent} strokeWidth="8" />
            <line x1="0" y1="-120" x2="0" y2="120" stroke={accent} strokeWidth="8" />
          </g>
        </svg>
      </AbsoluteFill>

      {/* падающие купюры в 3D */}
      <AbsoluteFill style={{ perspective: 1200, opacity: intro }}>
        <div style={{ position: "absolute", left: "50%", top: "50%", transformStyle: "preserve-3d", transform: `translate(-50%,-50%) translateZ(${push}px)` }}>
          {bills.map(({ x, y, z, rot, rotY, key }) => (
            <div
              key={key}
              style={{
                position: "absolute",
                transform: `translate3d(${x}px, ${y}px, ${z}px) rotateZ(${rot}deg) rotateY(${rotY}deg)`,
                width: 200,
                height: 92,
                marginLeft: -100,
                marginTop: -46,
                background: `linear-gradient(135deg, #2f5c40, ${green} 50%, #24493a)`,
                border: "2px solid #6f9a7e",
                borderRadius: 4,
                boxShadow: "0 6px 20px rgba(0,0,0,0.6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <div style={{ width: 54, height: 54, borderRadius: "50%", border: "3px solid #a9c6b3", color: "#cfe6d8", fontSize: 34, fontWeight: 800, display: "flex", alignItems: "center", justifyContent: "center" }}>$</div>
              <div style={{ position: "absolute", top: 6, left: 8, color: "#cfe6d8", fontSize: 20, fontWeight: 800 }}>100</div>
              <div style={{ position: "absolute", bottom: 6, right: 8, color: "#cfe6d8", fontSize: 20, fontWeight: 800 }}>100</div>
            </div>
          ))}
        </div>
      </AbsoluteFill>

      {/* красные кристаллы «мет» снизу */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", opacity: intro, pointerEvents: "none" }}>
        <svg width={1600} height={260} viewBox="0 0 1600 260" style={{ filter: `drop-shadow(0 0 30px ${accent})` }}>
          {Array.from({ length: 14 }).map((_, i) => {
            const x = 80 + i * 108 + (rnd(i, 9) - 0.5) * 40;
            const h = 90 + rnd(i, 10) * 120;
            return <polygon key={i} points={`${x},260 ${x - 26},${260 - h * 0.5} ${x},${260 - h} ${x + 26},${260 - h * 0.5}`} fill={accent} opacity={0.35 + rnd(i, 11) * 0.4} />;
          })}
        </svg>
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.85)", pointerEvents: "none" }} />

      {title && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 92, opacity: interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>
          <div style={{ color: PALETTE.cream, fontSize: 92, fontWeight: 800, letterSpacing: 8, textTransform: "uppercase", textShadow: `0 0 40px ${accent}, 0 6px 30px rgba(0,0,0,0.9)` }}>{title}</div>
          <div style={{ marginTop: 8, color: accent, fontSize: 32, letterSpacing: 5, fontWeight: 600 }}>ФАЛЬШИВКИ · НАРКОТИКИ · КАССА ВОЖДЯ</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
