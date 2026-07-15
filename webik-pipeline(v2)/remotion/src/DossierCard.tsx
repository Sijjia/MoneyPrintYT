import React from "react";
import { AbsoluteFill, Easing, Img, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { PALETTE, fontFamily } from "./theme";

// Досье на реального человека: фото (красный дуотон + уголки + скан-линии) слева,
// карточка-дело справа (имя, роль, поля), красный штамп в конце. Фото — реальный
// снимок из истории (проп photo, файл в remotion/public/); нет фото → силуэт.
export type DossierField = { k: string; v: string };
export type DossierProps = {
  name?: string;
  role?: string;
  fields?: DossierField[];
  stamp?: string; // напр. «ОСУЖДЁН» / «ПОГИБ» / «В РОЗЫСКЕ»
  photo?: string | null; // имя файла в public/ или data-URI
  accent?: string;
};

const Silhouette: React.FC = () => (
  <svg viewBox="0 0 300 380" width="100%" height="100%" style={{ display: "block" }}>
    <rect width="300" height="380" fill="#141a26" />
    <g fill="#2b3547">
      <circle cx="150" cy="140" r="72" />
      <path d="M30 380 C30 270 80 232 150 232 C220 232 270 270 270 380 Z" />
    </g>
  </svg>
);

export const DossierCard: React.FC<DossierProps> = ({
  name = "ИМЯ ФАМИЛИЯ",
  role = "",
  fields = [],
  stamp = "",
  photo = null,
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();

  const photoAp = interpolate(frame, [6, 24], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const photoScale = interpolate(frame, [6, 40], [1.12, 1.0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const nameAp = interpolate(frame, [20, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const nameX = interpolate(frame, [20, 40], [40, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });

  const stampF = Math.max(20, Math.round(durationInFrames * 0.42));
  const stampScale = interpolate(frame, [stampF, stampF + 8], [2.2, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
  const stampAp = interpolate(frame, [stampF, stampF + 6], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  const exit = interpolate(frame, [durationInFrames - 20, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), background: "#05070c", opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(circle at 32% 50%, rgba(217,40,40,0.10) 0%, rgba(0,0,0,0) 58%)" }} />
      <AbsoluteFill style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 80, padding: 120 }}>
        {/* ФОТО с обработкой */}
        <div style={{ position: "relative", width: 560, height: 700, flexShrink: 0, transform: `scale(${photoScale})`, opacity: photoAp }}>
          <div style={{ position: "absolute", inset: 0, overflow: "hidden", borderRadius: 6 }}>
            {photo ? (
              <Img src={photo.startsWith("data:") ? photo : staticFile(photo)} style={{ width: "100%", height: "100%", objectFit: "cover", filter: "grayscale(1) contrast(1.15) brightness(0.85)" }} />
            ) : (
              <Silhouette />
            )}
            {/* красный дуотон-оверлей */}
            <div style={{ position: "absolute", inset: 0, background: `linear-gradient(180deg, rgba(217,40,40,0.18), rgba(120,10,10,0.42))`, mixBlendMode: "multiply" }} />
            {/* скан-линии */}
            <div style={{ position: "absolute", inset: 0, background: "repeating-linear-gradient(0deg, rgba(0,0,0,0.0) 0px, rgba(0,0,0,0.0) 2px, rgba(0,0,0,0.22) 3px)", opacity: 0.5 }} />
          </div>
          {/* уголки */}
          {[[0, 0, 1, 1], [1, 0, -1, 1], [0, 1, 1, -1], [1, 1, -1, -1]].map(([cx, cy, dx, dy], i) => (
            <React.Fragment key={i}>
              <div style={{ position: "absolute", [cx ? "right" : "left"]: -4, [cy ? "bottom" : "top"]: -4, width: 40, height: 5, background: accent }} />
              <div style={{ position: "absolute", [cx ? "right" : "left"]: -4, [cy ? "bottom" : "top"]: -4, width: 5, height: 40, background: accent }} />
            </React.Fragment>
          ))}
        </div>

        {/* КАРТОЧКА-ДЕЛО */}
        <div style={{ flex: 1, maxWidth: 760 }}>
          <div style={{ color: accent, fontSize: 26, fontWeight: 700, letterSpacing: 8, marginBottom: 10, opacity: nameAp }}>ДЕЛО №</div>
          <div style={{ transform: `translateX(${nameX}px)`, opacity: nameAp }}>
            <div style={{ color: PALETTE.cream, fontSize: 96, fontWeight: 800, lineHeight: 0.98, letterSpacing: 1, textTransform: "uppercase", textShadow: "0 8px 30px rgba(0,0,0,0.9)" }}>{name}</div>
            {role && <div style={{ color: accent, fontSize: 40, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase", marginTop: 10 }}>{role}</div>}
          </div>
          <div style={{ height: 3, width: 300, background: accent, margin: "26px 0", boxShadow: `0 0 14px ${accent}` }} />
          {fields.map((f, i) => {
            const fd = 34 + i * 8;
            const ap = interpolate(frame, [fd, fd + 12], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            const x = interpolate(frame, [fd, fd + 14], [24, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) });
            return (
              <div key={i} style={{ display: "flex", gap: 20, marginBottom: 16, opacity: ap, transform: `translateX(${x}px)`, alignItems: "baseline" }}>
                <span style={{ color: "rgba(244,241,234,0.5)", fontSize: 26, fontWeight: 600, letterSpacing: 3, textTransform: "uppercase", minWidth: 240 }}>{f.k}</span>
                <span style={{ color: PALETTE.cream, fontSize: 36, fontWeight: 700 }}>{f.v}</span>
              </div>
            );
          })}
        </div>

        {/* ШТАМП */}
        {stamp && (
          <div style={{ position: "absolute", right: 180, bottom: 150, transform: `rotate(-13deg) scale(${stampScale})`, opacity: stampAp * 0.92, border: `6px solid ${accent}`, color: accent, fontSize: 68, fontWeight: 800, letterSpacing: 4, padding: "10px 34px", textTransform: "uppercase", borderRadius: 8, boxShadow: `0 0 30px ${accent}55` }}>
            {stamp}
          </div>
        )}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
