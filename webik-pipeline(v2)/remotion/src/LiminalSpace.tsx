import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type LiminalSpaceProps = {
  title?: string;           // «BACKROOMS» / «УРОВЕНЬ 0»
  sub?: string;             // подпись под тайтлом
  caption?: string;
  accent?: string;
};

// Лиминальное пространство «Backrooms»: бесконечный жёлтый коридор с 3D-перспективой и гудящими лампами.
export const LiminalSpace: React.FC<LiminalSpaceProps> = ({
  title = "BACKROOMS",
  sub = "LEVEL 0",
  caption = "",
  accent = "#c9b23a",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  // «движение вперёд» — панели уезжают в глубину циклично
  const depth = 10;
  const flicker = (i: number) => {
    const n = Math.sin(frame * 0.5 + i * 2.1) * Math.sin(frame * 0.17 + i);
    return n > -0.85 ? 1 : 0.25; // редкие мигания
  };

  return (
    <AbsoluteFill style={{ background: "#b9a733", fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden", perspective: 900 }}>
      {/* дальний конец коридора */}
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 50%, #d8c65a 0%, #9c8b28 45%, #6f6018 100%)" }} />

      {/* уходящие в глубину сегменты потолка/пола/стен */}
      <AbsoluteFill style={{ transformStyle: "preserve-3d", justifyContent: "center", alignItems: "center" }}>
        {Array.from({ length: depth }).map((_, i) => {
          const t = ((i + (frame * 0.03) % 1) / depth); // 0..1 к камере
          const z = interpolate(t, [0, 1], [-2600, 200]);
          const scale = interpolate(t, [0, 1], [0.15, 1.25]);
          const op = interpolate(t, [0, 0.2, 1], [0, 1, 1]) * interpolate(t, [0.85, 1], [1, 0]);
          return (
            <div key={i} style={{
              position: "absolute", width: 1200, height: 700,
              transform: `translateZ(${z}px) scale(${scale})`,
              border: "18px solid #8f7f22", background: "transparent", boxSizing: "border-box",
              boxShadow: "inset 0 0 120px rgba(90,76,10,0.6)", opacity: op,
            }}>
              {/* лампа на «потолке» сегмента */}
              <div style={{ position: "absolute", top: 8, left: "50%", transform: "translateX(-50%)", width: 220, height: 26, background: "#fff7cf", opacity: flicker(i), boxShadow: `0 0 60px 20px rgba(255,247,207,${0.5 * flicker(i)})` }} />
            </div>
          );
        })}
      </AbsoluteFill>

      {/* «ковролин»-текстура снизу */}
      <AbsoluteFill style={{ top: "62%", background: "repeating-linear-gradient(90deg, rgba(120,104,26,0.5) 0px, rgba(120,104,26,0.5) 4px, transparent 4px, transparent 10px)", opacity: 0.5, pointerEvents: "none" }} />
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.10) 0px, rgba(0,0,0,0.10) 1px, transparent 3px, transparent 5px)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(60,50,8,0.85)", pointerEvents: "none" }} />

      {/* тайтл */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ textAlign: "center", opacity: interpolate(frame, [10, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>
          <div style={{ color: "#1c1808", fontSize: 130, fontWeight: 800, letterSpacing: 8, textShadow: "0 6px 30px rgba(255,247,180,0.5)" }}>{title}</div>
          {sub && <div style={{ color: "#2c2610", fontSize: 44, fontWeight: 600, letterSpacing: 12, marginTop: 6 }}>{sub}</div>}
        </div>
      </AbsoluteFill>

      {caption && (
        <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 60,
          opacity: interpolate(frame, [26, 42], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) * exit }}>
          <div style={{ maxWidth: 1480, textAlign: "center", color: "#211c09", fontSize: 36, fontWeight: 600, textShadow: "0 3px 14px rgba(255,247,180,0.4)" }}>{caption}</div>
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};
