import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { mspring, enterUp } from "./anim";

export type GuruDossierProps = {
  kicker?: string;      // «CRIMINAL GURUS»
  name?: string;        // имя гуру
  followers?: string;   // «60 000 000 последователей»
  verdict?: string;     // «LIFE IMPRISONMENT» / «20 ЛЕТ»
  charge?: string;      // «изнасилование, убийство»
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

// Досье гуру-преступника: «дело» с силуэтом-портретом, штамп приговора, число последователей.
export const GuruDossier: React.FC<GuruDossierProps> = ({
  kicker = "CRIMINAL GURUS",
  name = "A 'GODMAN' ON TRIAL",
  followers = "millions of followers",
  verdict = "LIFE IMPRISONMENT",
  charge = "assault · fraud",
  accent = "#d24a3a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const card = enterUp(frame, 30, 4, 40, { stiffness: 120, damping: 17 });
  // штамп приговора «впечатывается»
  const stamp = mspring(frame, 30, { stiffness: 220, damping: 11, delay: 34 });
  const stampO = interpolate(frame, [34, 40], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 40%, #211512 0%, #140c0a 60%, #080504 100%)" }} />
      {/* тканевый паттерн-намёк на одеяния */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(135deg, rgba(255,255,255,0.015) 0 2px, transparent 2px 26px)", pointerEvents: "none" }} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", opacity: exit }}>
        <div style={{ width: 1500, background: "#efe9dc", borderRadius: 6, boxShadow: "0 30px 90px rgba(0,0,0,0.8)", overflow: "hidden",
          transform: `translateY(${card.translateY}px)`, opacity: card.opacity, display: "flex" }}>
          {/* фото-силуэт */}
          <div style={{ width: 380, background: "#c9c0ac", position: "relative", display: "flex", alignItems: "flex-end", justifyContent: "center" }}>
            <svg width="380" height="440" viewBox="0 0 380 440">
              <rect width="380" height="440" fill="#bcb29a" />
              {/* силуэт головы/плеч + борода */}
              <circle cx="190" cy="170" r="90" fill="#8a7f66" />
              <path d="M110,250 Q190,360 270,250 L270,440 L110,440 Z" fill="#8a7f66" />
              <path d="M120,190 Q190,320 260,190 Q250,270 190,300 Q130,270 120,190 Z" fill="#5a5040" opacity="0.35" />
            </svg>
            <div style={{ position: "absolute", top: 14, left: 14, background: "#111", color: "#eee", fontSize: 18, letterSpacing: 2, padding: "5px 12px", fontFamily: fontFamily("oswald") }}>ДЕЛО · ФОТО</div>
          </div>
          {/* данные дела */}
          <div style={{ flex: 1, padding: "34px 44px", color: "#221c12" }}>
            <div style={{ color: accent, fontSize: 26, fontWeight: 800, letterSpacing: 4 }}>{kicker}</div>
            <div style={{ fontSize: 58, fontWeight: 800, lineHeight: 1.05, marginTop: 8 }}>{name}</div>
            <div style={{ marginTop: 24, height: 2, background: "#221c1233" }} />
            <div style={{ marginTop: 20, fontSize: 30, fontWeight: 600 }}>Обвинение: <span style={{ color: accent }}>{charge}</span></div>
            <div style={{ marginTop: 10, fontSize: 30, fontWeight: 600 }}>Последователи: {followers}</div>
            {/* штамп приговора */}
            <div style={{ marginTop: 34, display: "inline-block", border: `5px solid ${accent}`, color: accent, fontSize: 40, fontWeight: 900,
              letterSpacing: 3, padding: "10px 26px", borderRadius: 6, transform: `rotate(-8deg) scale(${1.6 - stamp * 0.6})`, opacity: stampO,
              textShadow: "0 1px 0 rgba(0,0,0,0.1)" }}>{verdict}</div>
          </div>
        </div>
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 60, textAlign: "center", padding: "0 200px",
          color: "#e7ddce", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [42, 56], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 280px rgba(0,0,0,0.78)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
