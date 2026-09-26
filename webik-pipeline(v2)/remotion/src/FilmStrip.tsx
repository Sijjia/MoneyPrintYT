import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, Loop, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type FilmStripProps = {
  videoSrc?: string;
  videoLoopFrames?: number;
  title?: string;
  subtitle?: string;
  accent?: string;
};

const Sprockets: React.FC<{ w: number; y: number }> = ({ w, y }) => (
  <>{Array.from({ length: Math.ceil(w / 46) + 2 }).map((_, i) => (
    <div key={i} style={{ position: "absolute", left: i * 46 - 20, top: y, width: 22, height: 16,
      background: "#0a0a0c", borderRadius: 3 }} />
  ))}</>
);

// Кадр из мультфильма в движущейся киноленте (целлулоид, перфорация). «Показ футажа».
export const FilmStrip: React.FC<FilmStripProps> = ({
  videoSrc = "videos/dw_boo.mp4", videoLoopFrames = 150,
  title = "КАДР ИЗ ФИЛЬМА", subtitle = "", accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const intro = interpolate(frame, [0, 16], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const drift = -(frame * 0.6) % (width * 1.4);

  const stripH = height * 0.5, stripY = height * 0.22;
  const frW = stripH * 16 / 9 * 0.62, gap = 46;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, background: "#08080a" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 42%, #141418 0%, #09090c 60%, #050506 100%)" }} />
      {/* лента */}
      <div style={{ position: "absolute", left: 0, top: stripY, width: "140%", height: stripH,
        transform: `translateX(${drift}px) rotate(-3.5deg)`, background: "#161619",
        borderTop: "3px solid #232327", borderBottom: "3px solid #232327",
        boxShadow: "0 30px 80px rgba(0,0,0,0.7)", opacity: intro }}>
        {/* перфорация */}
        <div style={{ position: "absolute", left: 0, right: 0, top: 8, height: 16 }}><Sprockets w={width * 1.5} y={0} /></div>
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 8, height: 16 }}><Sprockets w={width * 1.5} y={0} /></div>
        {/* кадры с футажём */}
        {[0, 1, 2, 3].map((i) => (
          <div key={i} style={{ position: "absolute", left: 60 + i * (frW + gap), top: 40, width: frW, height: stripH - 80,
            background: "#000", border: "2px solid #2a2a2f", overflow: "hidden", opacity: i === 1 ? 1 : 0.55 }}>
            <Loop durationInFrames={Math.max(30, videoLoopFrames)}>
              <OffthreadVideo src={staticFile(videoSrc)} muted startFrom={i * 8}
                style={{ width: "100%", height: "100%", objectFit: "cover", filter: "saturate(0.85) contrast(1.05)" }} />
            </Loop>
          </div>
        ))}
      </div>
      {/* скан-линии поверх */}
      <AbsoluteFill style={{ opacity: 0.05, backgroundImage:
        "repeating-linear-gradient(0deg, #fff 0, #fff 1px, transparent 1px, transparent 3px)", pointerEvents: "none" }} />

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 90, opacity: intro }}>
        <div style={{ textAlign: "center" }}>
          <div style={{ color: "#8a8a92", fontSize: 20, fontWeight: 700, letterSpacing: 6 }}>DREAMWORKS · АРХИВ</div>
          <div style={{ color: "#f2f2f4", fontSize: 84, fontWeight: 800, letterSpacing: 4, lineHeight: 1,
            textShadow: `0 0 26px ${accent}55` }}>{title}</div>
          {subtitle ? <div style={{ color: accent, fontSize: 26, fontWeight: 700, letterSpacing: 3 }}>{subtitle}</div> : null}
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px rgba(0,0,0,0.72)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
