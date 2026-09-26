import React from "react";
import { AbsoluteFill, OffthreadVideo, staticFile, Loop, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type GlitchLeakProps = {
  videoSrc?: string; videoLoopFrames?: number;
  title?: string; subtitle?: string; accent?: string;
};

const rnd = (i: number) => { const x = Math.sin(i * 91.7) * 43758.5; return x - Math.floor(x); };

// «Утёкший/повреждённый материал»: VHS-порча, RGB-сдвиг, tracking-помехи, метка УТЕЧКА.
export const GlitchLeak: React.FC<GlitchLeakProps> = ({
  videoSrc = "", videoLoopFrames = 150,
  title = "СБОЙ", subtitle = "ПОВРЕЖДЁННЫЙ СИГНАЛ", accent = "#7a4dff",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, width, height } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const intro = interpolate(frame, [0, 12], [0, 1], { extrapolateRight: "clamp" });
  const glitchOn = rnd(Math.floor(frame / 4)) > 0.55;
  const rgb = glitchOn ? 6 + rnd(frame) * 10 : 2;
  const jitter = glitchOn ? (rnd(frame + 3) - 0.5) * 14 : 0;
  const hasVideo = !!videoSrc;

  const lay = (dx: number, filt: string, op: number, mix: string) => (
    <AbsoluteFill style={{ transform: `translate(${dx + jitter}px,0)`, mixBlendMode: mix as any, opacity: op, filter: filt }}>
      <Loop durationInFrames={Math.max(30, videoLoopFrames)}>
        <OffthreadVideo src={staticFile(videoSrc)} muted style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      </Loop>
    </AbsoluteFill>
  );

  // процедурный глитч-фон (без видео): тёмное поле + RGB-помехи, датамош-блоки, дрожащая сетка
  const procBg = (
    <AbsoluteFill>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #12101c 0%, #060608 72%)" }} />
      {/* дрейфующие цветные полосы-датамош */}
      {Array.from({ length: 7 }).map((_, i) => {
        const yy = (frame * (3 + i * 2) + i * 170) % height;
        const on = rnd(i + Math.floor(frame / 3)) > 0.4;
        return <div key={`b${i}`} style={{ position: "absolute", left: 0, right: 0, top: yy,
          height: 10 + rnd(i + frame) * 46, transform: `translateX(${(rnd(i + frame) - 0.5) * 40}px)`,
          background: i % 3 === 0 ? accent : (i % 3 === 1 ? "#1f8bff" : "#ff2d55"),
          opacity: on ? 0.10 + rnd(i) * 0.14 : 0.03, mixBlendMode: "screen" }} />;
      })}
      {/* RGB-дубли текста-шума */}
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: 0.06 }}>
        <div style={{ color: "#fff", fontSize: 44, letterSpacing: 8, fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
          {Array.from({ length: 6 }).map((_, r) => (
            <div key={r} style={{ transform: `translateX(${(rnd(r + frame) - 0.5) * 30}px)` }}>
              {Array.from({ length: 20 }).map((_, c) => (rnd(r * 20 + c + Math.floor(frame / 5)) > 0.5 ? "1" : "0")).join(" ")}
            </div>
          ))}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );

  return (
    <AbsoluteFill style={{ opacity: exit, background: "#050505", fontFamily: fontFamily("oswald") }}>
      {hasVideo ? (<>
        {lay(0, "saturate(0.7) contrast(1.1)", 1, "normal")}
        {lay(-rgb, "brightness(1)", 0.5, "screen")}
        {lay(rgb, "brightness(1)", 0.5, "screen")}
      </>) : procBg}
      {/* tracking-полосы */}
      {Array.from({ length: 4 }).map((_, i) => {
        const yy = (frame * (7 + i * 4) + i * 260) % height;
        return <div key={i} style={{ position: "absolute", left: 0, right: 0, top: yy, height: 8 + rnd(i + frame) * 20,
          background: `rgba(255,255,255,${0.03 + rnd(i) * 0.06})`, mixBlendMode: "overlay", pointerEvents: "none" }} />;
      })}
      {/* блок-помеха */}
      {glitchOn && <div style={{ position: "absolute", left: rnd(frame) * width * 0.6, top: rnd(frame + 1) * height,
        width: 120 + rnd(frame + 2) * 260, height: 20 + rnd(frame + 5) * 40, background: accent, opacity: 0.25, mixBlendMode: "screen" }} />}
      <AbsoluteFill style={{ opacity: 0.14, backgroundImage:
        "repeating-linear-gradient(0deg, #000 0, #000 1px, transparent 1px, transparent 3px)", pointerEvents: "none" }} />
      <AbsoluteFill style={{ boxShadow: "inset 0 0 250px rgba(0,0,0,0.82)", pointerEvents: "none" }} />
      {/* метка + REC */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: 44, opacity: intro }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <span style={{ width: 16, height: 16, background: accent, borderRadius: "50%", opacity: frame % 30 < 15 ? 1 : 0.2 }} />
          <span style={{ color: "#fff", fontSize: 26, fontWeight: 800, letterSpacing: 3 }}>REC</span>
        </div>
      </AbsoluteFill>
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 66, opacity: intro }}>
        <div style={{ textAlign: "center", transform: `translateX(${jitter}px)` }}>
          <div style={{ color: accent, fontSize: 88, fontWeight: 800, letterSpacing: 8, textShadow: `0 0 26px ${accent}` }}>{title}</div>
          <div style={{ color: "#cdd0d0", fontSize: 26, fontWeight: 700, letterSpacing: 4 }}>{subtitle}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
