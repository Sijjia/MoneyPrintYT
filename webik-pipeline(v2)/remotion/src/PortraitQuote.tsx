import React from "react";
import { AbsoluteFill, Img, staticFile, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";

export type PortraitQuoteProps = {
  photo?: string;            // портрет человека (public path)
  name?: string;
  role?: string;             // подпись под именем (кто это / когда)
  quote?: string;            // сама реплика
  accent?: string;
  durationInFrames?: number;
};

// «Человек сказал: …» — портрет слева + цитата в кавычках справа + имя.
export const PortraitQuote: React.FC<PortraitQuoteProps> = ({
  photo = "", name = "ДЖЕФФРИ КАТЦЕНБЕРГ", role = "сооснователь DreamWorks",
  quote = "Мы построили студию, чтобы бросить вызов Disney — и это была война.",
  accent = "#d9282f",
}) => {
  const frame = useCurrentFrame();
  const { width, height, durationInFrames, fps } = useVideoConfig();
  const intro = interpolate(frame, [0, 14], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 14, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const pin = spring({ frame, fps, config: { damping: 16, stiffness: 90 } });

  const PW = width * 0.30, PH = PW * 1.25;
  const PX = width * 0.10, PY = height * 0.5 - PH / 2;

  // цитата по словам
  const words = quote.split(" ");
  const per = Math.max(1.6, (durationInFrames * 0.55) / Math.max(1, words.length));

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit,
      background: "radial-gradient(ellipse at 35% 45%, #16161b 0%, #0a0a0d 60%, #050506 100%)" }}>
      <AbsoluteFill style={{ opacity: 0.05, backgroundImage:
        "repeating-linear-gradient(0deg,#fff 0,#fff 1px,transparent 1px,transparent 3px)" }} />

      {/* портрет */}
      <div style={{ position: "absolute", left: PX + interpolate(pin, [0, 1], [-40, 0]), top: PY, width: PW, height: PH,
        opacity: intro, borderRadius: 16, overflow: "hidden",
        boxShadow: `0 26px 70px rgba(0,0,0,0.7), 0 0 0 3px ${accent}, 0 0 44px ${accent}55` }}>
        {photo
          ? <Img src={staticFile(photo)} style={{ width: "100%", height: "100%", objectFit: "cover",
              filter: "saturate(0.9) contrast(1.05)", transform: `scale(${1.03 + intro * 0.02})` }} />
          : <div style={{ width: "100%", height: "100%", background: "#222" }} />}
        <AbsoluteFill style={{ boxShadow: "inset 0 0 80px rgba(0,0,0,0.6)", pointerEvents: "none" }} />
      </div>

      {/* цитата */}
      <div style={{ position: "absolute", left: PX + PW + width * 0.05, top: height * 0.22,
        width: width - (PX + PW + width * 0.05) - width * 0.06, opacity: intro }}>
        <div style={{ color: accent, fontSize: 150, fontWeight: 800, lineHeight: 0.6, height: 60 }}>“</div>
        <div style={{ color: "#f2f2f4", fontSize: 52, fontWeight: 700, lineHeight: 1.28, marginTop: 8 }}>
          {words.map((w, i) => {
            const o = interpolate(frame, [10 + i * per, 10 + i * per + 8], [0.12, 1],
              { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
            return <span key={i} style={{ opacity: o }}>{w} </span>;
          })}
        </div>
        <div style={{ marginTop: 34, display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{ width: 46, height: 4, background: accent }} />
          <div>
            <div style={{ color: "#fff", fontSize: 34, fontWeight: 800, letterSpacing: 2 }}>{name}</div>
            {role && <div style={{ color: "#8a8a92", fontSize: 22, fontWeight: 600, letterSpacing: 1 }}>{role}</div>}
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};
