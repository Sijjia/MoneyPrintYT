import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type RedactedDossierProps = {
  value: string;
  label: string;
  suffix?: string;
  accent?: string;
};

// Рассекреченное досье: чёрная плашка цензуры съезжает и открывает число,
// штамп «СЕКРЕТНО», лейбл печатной машинкой, «ДЕЛО №».
export const RedactedDossier: React.FC<RedactedDossierProps> = ({
  value,
  label,
  suffix = "",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  const shownNum = (() => {
    const n = parseInt(value.replace(/\D/g, ""), 10);
    return Number.isNaN(n) ? value : n.toLocaleString("ru-RU");
  })();

  const cardIn = spring({ frame, fps, config: { damping: 14, stiffness: 120 }, durationInFrames: 20 });
  const cardX = interpolate(cardIn, [0, 1], [-80, 0]);
  // цензура съезжает вправо, открывая число
  const wipe = interpolate(frame, [16, 34], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.inOut(Easing.cubic) });
  // штамп СЕКРЕТНО бьётся
  const stampT = spring({ frame: frame - 20, fps, config: { damping: 8, stiffness: 200 } });
  const stampScale = interpolate(stampT, [0, 1], [2.4, 1]);
  const stampOp = interpolate(frame, [20, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  // машинка по лейблу
  const chars = Math.floor(interpolate(frame, [30, 30 + label.length * 1.7], [0, label.length], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const typed = label.slice(0, chars);
  const caret = Math.floor(frame / 6) % 2 === 0 ? "_" : "";
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit * cardIn }}>
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-start", paddingLeft: 150 }}>
        <div
          style={{
            position: "relative",
            width: 1000,
            transform: `translateX(${cardX}px) rotate(-1.2deg)`,
            background: "linear-gradient(180deg, rgba(24,22,20,0.94), rgba(16,14,13,0.9))",
            border: `1px solid ${accent}55`,
            borderLeft: `8px solid ${accent}`,
            padding: "36px 48px 44px",
            boxShadow: "0 30px 80px rgba(0,0,0,0.7)",
          }}
        >
          {/* хедер дела */}
          <div style={{ display: "flex", alignItems: "center", color: accent, fontSize: 30, letterSpacing: 6, fontWeight: 600, borderBottom: `1px solid ${accent}44`, paddingBottom: 12 }}>
            ДЕЛО № {(frame % 900 + 100).toString().padStart(4, "0")}
            <span style={{ marginLeft: "auto", color: PALETTE.cream, opacity: 0.5, fontSize: 22, letterSpacing: 3 }}>КНДР · ДОСТУП ЗАКРЫТ</span>
          </div>

          {/* число под цензурой */}
          <div style={{ position: "relative", marginTop: 24, height: 210, overflow: "hidden" }}>
            <div style={{ color: PALETTE.cream, fontSize: 200, fontWeight: 800, lineHeight: 1, letterSpacing: -4, textShadow: "0 8px 30px rgba(0,0,0,0.8)" }}>
              {shownNum}
              <span style={{ color: accent }}>{suffix}</span>
            </div>
            {/* чёрная плашка цензуры съезжает вправо */}
            <div
              style={{
                position: "absolute",
                top: 0,
                bottom: 0,
                left: `${wipe * 100}%`,
                right: 0,
                background: "#0a0908",
                borderLeft: `4px solid ${accent}`,
              }}
            />
          </div>

          {/* лейбл машинкой */}
          <div style={{ marginTop: 8, color: PALETTE.cream, fontSize: 42, letterSpacing: 3, textTransform: "uppercase", fontWeight: 600 }}>
            {typed}<span style={{ color: accent }}>{caret}</span>
          </div>

          {/* штамп СЕКРЕТНО */}
          <div
            style={{
              position: "absolute",
              right: 40,
              top: 120,
              transform: `rotate(-14deg) scale(${stampScale})`,
              opacity: stampOp * 0.92,
              color: accent,
              border: `5px solid ${accent}`,
              padding: "8px 22px",
              fontSize: 52,
              fontWeight: 800,
              letterSpacing: 6,
              borderRadius: 6,
              textShadow: `0 0 10px ${accent}55`,
              boxShadow: `0 0 0 2px ${accent}33`,
            }}
          >
            СЕКРЕТНО
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
