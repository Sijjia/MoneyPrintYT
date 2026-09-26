import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, mspring, enterUp } from "./anim";

export type KumbhaMelaProps = {
  kicker?: string;
  title?: string;
  countText?: string;   // «120 000 000»
  countLabel?: string;
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

const rnd = (i: number, s = 1) => { const x = Math.sin(i * 45.1 + s * 12.9) * 43758.5; return x - Math.floor(x); };

// Кумбха-мела: ночная «спутниковая» съёмка — миллионы точек-огней вдоль священной реки образуют
// гигантскую толпу, счётчик тикает к 120 млн. Медленный отъезд камеры (масштаб).
export const KumbhaMela: React.FC<KumbhaMelaProps> = ({
  kicker = "KUMBH MELA",
  title = "THE LARGEST GATHERING ON EARTH",
  countText = "120 000 000",
  countLabel = "pilgrims in one place",
  accent = "#ffb44a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const zoomOut = interpolate(frame, [0, durationInFrames], [1.25, 1.0], { easing: ease.smoothOut });
  const appear = interpolate(frame, [0, 40], [0, 1], { extrapolateRight: "clamp", easing: ease.expoOut });
  const target = parseInt(countText.replace(/\D/g, "") || "0", 10);
  const cnt = Math.round(mspring(frame, 30, { stiffness: 40, damping: 20, delay: 12 }) * target);

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 45%, #12100a 0%, #0a0906 55%, #050403 100%)" }} />
      {/* спутниковая толпа: точки-огни вдоль реки-изгиба */}
      <AbsoluteFill style={{ transform: `scale(${zoomOut})`, opacity: appear }}>
        <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
          {/* река */}
          <path d="M-50,760 C400,700 560,560 900,540 C1260,520 1440,380 1980,340" fill="none" stroke="#1a2740" strokeWidth="70" opacity="0.7" />
          <path d="M-50,760 C400,700 560,560 900,540 C1260,520 1440,380 1980,340" fill="none" stroke="#26507a" strokeWidth="60" opacity="0.5" />
        </svg>
        {/* толпа-огни (плотное поле точек по берегам) */}
        {Array.from({ length: 900 }).map((_, i) => {
          const t = rnd(i, 1);
          const bx = -50 + t * 2000;
          // берег реки по кривой (приближённо)
          const by = 760 - t * 420 + (rnd(i, 2) - 0.5) * 260;
          const on = interpolate(frame, [4 + rnd(i, 3) * 40, 20 + rnd(i, 3) * 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
          const fl = 0.5 + 0.5 * Math.sin((frame + i) / 7);
          const warm = rnd(i, 4) > 0.5;
          return <div key={i} style={{ position: "absolute", left: bx, top: by, width: 3, height: 3, borderRadius: "50%",
            background: warm ? accent : "#ffe6b0", opacity: on * (0.35 + fl * 0.5), boxShadow: `0 0 3px ${accent}` }} />;
        })}
      </AbsoluteFill>

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "80px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 26); const t = enterUp(frame, 30, 8, 42, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f6ecd8", fontSize: 66, fontWeight: 700, lineHeight: 1.02, maxWidth: 1150, textShadow: "0 6px 30px rgba(0,0,0,0.85)", marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {/* счётчик */}
      <div style={{ position: "absolute", right: 90, top: 300, textAlign: "right" }}>
        <div style={{ color: "#fff", fontSize: 96, fontWeight: 800, fontVariantNumeric: "tabular-nums", textShadow: `0 0 30px ${accent}`, fontFamily: fontFamily("oswald") }}>{cnt.toLocaleString("ru-RU")}</div>
        <div style={{ color: accent, fontSize: 26, fontWeight: 600, letterSpacing: 1 }}>{countLabel}</div>
      </div>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 62, textAlign: "center", padding: "0 200px",
          color: "#ecdfc6", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [34, 48], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
