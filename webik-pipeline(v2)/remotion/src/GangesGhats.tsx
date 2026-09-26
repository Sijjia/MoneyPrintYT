import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { ease, enterUp } from "./anim";

export type GangesGhatsProps = {
  kicker?: string;      // «VARANASI» / «ГХАТЫ ГАНГА»
  title?: string;       // короткая строка КАПСОМ
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

const rnd = (i: number, s = 1) => {
  const x = Math.sin(i * 51.3 + s * 19.7) * 43758.5453;
  return x - Math.floor(x);
};

// Ночные гхаты Варанаси: тёмная река, дым погребальных костров, дрейф плавучих лампад-дийа,
// силуэты храмов, тёплые отражения в воде. Медленный пан камеры.
export const GangesGhats: React.FC<GangesGhatsProps> = ({
  kicker = "VARANASI",
  title = "THE CITY WHERE THE PYRES BURN",
  accent = "#ff8a2a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const intro = interpolate(frame, [0, 24], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const drift = interpolate(frame, [0, durationInFrames], [0, -60]); // медленный пан вправо-вниз
  const zoom = interpolate(frame, [0, durationInFrames], [1.04, 1.12]);

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      {/* небо-ночь + вода */}
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#100a12 0%,#1a0f16 34%,#241019 52%,#160b10 66%,#0a0608 100%)" }} />
      <AbsoluteFill style={{ transform: `translateX(${drift}px) scale(${zoom})`, opacity: intro }}>
        {/* дальний берег: силуэты храмов/шпилей */}
        <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
          <defs>
            <linearGradient id="ggwater" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0" stopColor="#3a1c10" stopOpacity="0.6" />
              <stop offset="1" stopColor="#080405" />
            </linearGradient>
            <radialGradient id="gghaze" cx="0.5" cy="0.4" r="0.6">
              <stop offset="0" stopColor={accent} stopOpacity="0.22" />
              <stop offset="1" stopColor="transparent" />
            </radialGradient>
          </defs>
          {/* храмовый горизонт */}
          <g fill="#1c1116" opacity="0.95">
            <rect x="0" y="470" width="1920" height="120" />
            <path d="M120,470 l0,-90 20,-40 20,40 0,90z" />
            <rect x="260" y="360" width="90" height="110" />
            <path d="M305,360 l-40,-46 40,-40 40,40z" />
            <rect x="470" y="392" width="130" height="78" />
            <path d="M700,470 l0,-120 26,-52 26,52 0,120z" fill="#241419" />
            <rect x="900" y="352" width="150" height="118" />
            <path d="M975,352 l-52,-58 52,-52 52,52z" />
            <rect x="1200" y="388" width="110" height="82" />
            <path d="M1255,388 l-38,-44 38,-40 38,40z" />
            <rect x="1470" y="360" width="140" height="110" />
            <path d="M1540,360 l-48,-54 48,-46 48,46z" />
            <rect x="1720" y="400" width="120" height="70" />
          </g>
          {/* каменные ступени-гхаты */}
          {Array.from({ length: 6 }).map((_, i) => (
            <rect key={i} x="0" y={470 + i * 16} width="1920" height="16" fill={`rgba(60,36,26,${0.5 - i * 0.05})`} />
          ))}
          {/* вода с отражениями */}
          <rect x="0" y="566" width="1920" height="514" fill="url(#ggwater)" />
          <rect x="0" y="380" width="1920" height="700" fill="url(#gghaze)" />
        </svg>

        {/* погребальные костры + дым */}
        {[440, 1080, 1560].map((x, i) => {
          const flick = 0.7 + 0.3 * Math.sin((frame + i * 30) / 6);
          return (
            <div key={`f${i}`} style={{ position: "absolute", left: x, top: 500 }}>
              <div style={{ width: 60, height: 46, borderRadius: "50% 50% 40% 40%", background: `radial-gradient(circle at 50% 70%, #ffdca0 0%, ${accent} 45%, #a12a10 80%, transparent 100%)`, filter: `blur(2px)`, opacity: flick, transform: `scaleY(${0.9 + 0.2 * Math.sin((frame + i * 17) / 5)})` }} />
              {/* дым */}
              {Array.from({ length: 4 }).map((_, k) => {
                const rise = ((frame * (0.8 + rnd(i * 4 + k, 2) * 0.6)) % 260);
                return <div key={k} style={{ position: "absolute", left: 10 + rnd(i * 4 + k, 3) * 30, top: -rise, width: 40 + rise * 0.5, height: 40 + rise * 0.5, borderRadius: "50%", background: "rgba(190,170,160,0.05)", filter: "blur(6px)", opacity: Math.max(0, 0.5 - rise / 260) }} />;
              })}
            </div>
          );
        })}

        {/* плавучие лампады-дийа на воде + их отражения */}
        {Array.from({ length: 26 }).map((_, i) => {
          const x = (rnd(i, 4) * 1920 + frame * (0.4 + rnd(i, 6) * 0.5)) % 1920;
          const y = 600 + rnd(i, 5) * 420;
          const gl = 0.5 + 0.5 * Math.sin((frame + i * 12) / 8);
          return (
            <React.Fragment key={`d${i}`}>
              <div style={{ position: "absolute", left: x, top: y, width: 7, height: 7, borderRadius: "50%", background: "#ffcf7a", boxShadow: `0 0 ${10 + gl * 12}px ${accent}`, opacity: 0.85 * gl }} />
              <div style={{ position: "absolute", left: x, top: y + 16, width: 5, height: 22, borderRadius: "50%", background: accent, filter: "blur(4px)", opacity: 0.28 * gl }} />
            </React.Fragment>
          );
        })}
      </AbsoluteFill>

      {/* заголовок */}
      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "84px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 28); const t = enterUp(frame, 30, 8, 44, { stiffness: 120, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f4ece2", fontSize: 78, fontWeight: 700, letterSpacing: 1, lineHeight: 1.02, textShadow: "0 6px 34px rgba(0,0,0,0.85)", maxWidth: 1200, marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 78, textAlign: "center", padding: "0 200px",
          color: "#e7ddd2", fontSize: 34, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [26, 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.expoOut }) * exit,
          transform: `translateY(${(1 - interpolate(frame, [26, 46], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: ease.expoOut })) * 16}px)` }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 300px rgba(0,0,0,0.8)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
