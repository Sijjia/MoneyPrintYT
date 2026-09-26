import React from "react";
import { AbsoluteFill, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { fontFamily } from "./theme";
import { mspring, enterUp } from "./anim";

export type FortCurseProps = {
  kicker?: string;      // «БХАНГАРХ» / «КУЛДХАРА»
  title?: string;       // КАПСОМ
  sign?: string;        // текст таблички ASI
  signAuthority?: string; // «ARCHAEOLOGICAL SURVEY OF INDIA»
  accent?: string;
  caption?: string;
  durationInFrames?: number;
};

// Заброшенный форт/хавели Раджастхана в сумерках: рваный силуэт крепости, официальная табличка ASI
// с запретом, пыль, мерцание. Медленный наезд, «проклятое запустение».
export const FortCurse: React.FC<FortCurseProps> = ({
  kicker = "BHANGARH FORT",
  title = "OFFICIALLY A CURSED PLACE",
  sign = "ENTRY INTO THE FORT AFTER SUNSET AND BEFORE SUNRISE IS STRICTLY PROHIBITED",
  signAuthority = "ARCHAEOLOGICAL SURVEY OF INDIA",
  accent = "#d98a3a",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const intro = interpolate(frame, [0, 24], [0, 1], { extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.1]);
  const signIn = mspring(frame, 30, { stiffness: 140, damping: 16, delay: 36 });
  const flick = frame > 60 ? (0.82 + 0.18 * Math.sin(frame * 1.7) * (Math.sin(frame / 9) > 0.6 ? 1 : 0.2)) : 1;

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "linear-gradient(180deg,#241a26 0%,#33202a 30%,#3e2622 50%,#241713 72%,#0e0808 100%)" }} />
      {/* луна */}
      <div style={{ position: "absolute", left: 1440, top: 120, width: 130, height: 130, borderRadius: "50%", background: "radial-gradient(circle at 40% 40%, #efe4c8, #b8a67e)", boxShadow: "0 0 90px rgba(220,200,150,0.35)", opacity: intro * 0.9 }} />

      <AbsoluteFill style={{ transform: `scale(${zoom})`, opacity: intro }}>
        <svg width={1920} height={1080} viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
          {/* холм */}
          <path d="M0,760 Q600,640 1000,700 T1920,720 L1920,1080 L0,1080 Z" fill="#171012" />
          {/* силуэт форта — рваная крепость с зубцами и куполом */}
          <g fill="#0d090b" opacity="0.98">
            <rect x="360" y="470" width="1200" height="300" />
            {Array.from({ length: 24 }).map((_, i) => <rect key={i} x={360 + i * 50} y="452" width="30" height="26" />)}
            {/* башни */}
            <rect x="330" y="380" width="90" height="390" />
            <rect x="1500" y="360" width="100" height="410" />
            <path d="M375,380 a45,45 0 0 1 -45,0 z" />
            {/* центральный купол-чхатри */}
            <rect x="850" y="360" width="220" height="120" />
            <path d="M960,300 C1030,300 1075,340 1075,362 L845,362 C845,340 890,300 960,300 Z" />
            <rect x="952" y="270" width="16" height="34" />
            {/* тёмные окна-арки */}
            {[[470, 560], [620, 560], [1140, 560], [1300, 560]].map(([x, y], i) => (
              <path key={i} d={`M${x},${y + 90} L${x},${y + 20} Q${x + 25},${y - 10} ${x + 50},${y + 20} L${x + 50},${y + 90} Z`} fill="#050304" />
            ))}
          </g>
          {/* одно тускло-мерцающее окно */}
          <path d="M700,650 L700,580 Q725,552 750,580 L750,650 Z" fill={accent} opacity={0.25 * flick} style={{ filter: `blur(2px)` }} />
        </svg>

        {/* пыль/споры в воздухе */}
        {Array.from({ length: 30 }).map((_, i) => {
          const x = (i * 129.3 + frame * (0.3 + (i % 4) * 0.2)) % 1920;
          const y = 300 + ((i * 91.7 + frame * 0.4) % 700);
          return <div key={i} style={{ position: "absolute", left: x, top: y, width: 3, height: 3, borderRadius: "50%", background: "rgba(210,180,140,0.5)", opacity: 0.2 + (i % 3) * 0.1 }} />;
        })}
      </AbsoluteFill>

      {/* официальная табличка ASI */}
      <div style={{ position: "absolute", left: "50%", bottom: 190, transform: `translateX(-50%) translateY(${interpolate(signIn, [0, 1], [26, 0])}px)`, opacity: signIn * exit,
        width: 1180, background: "linear-gradient(180deg,#123b22,#0c2c19)", border: `3px solid #e8e2d0`, borderRadius: 8, padding: "20px 34px", boxShadow: "0 20px 60px rgba(0,0,0,0.7)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 14, marginBottom: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: "50%", border: "2px solid #e8e2d0" }} />
          <div style={{ color: "#e8e2d0", fontSize: 22, fontWeight: 700, letterSpacing: 3 }}>{signAuthority}</div>
        </div>
        <div style={{ color: "#fff", fontSize: 36, fontWeight: 700, lineHeight: 1.2, letterSpacing: 0.5 }}>{sign}</div>
      </div>

      <AbsoluteFill style={{ justifyContent: "flex-start", alignItems: "flex-start", padding: "80px 90px", opacity: exit }}>
        {(() => { const k = enterUp(frame, 30, 2, 28); const t = enterUp(frame, 30, 8, 44, { stiffness: 125, damping: 18 }); return (<>
          <div style={{ color: accent, fontSize: 30, fontWeight: 700, letterSpacing: 8, opacity: k.opacity, transform: `translateY(${k.translateY}px)` }}>{kicker}</div>
          <div style={{ color: "#f2e8dc", fontSize: 74, fontWeight: 700, lineHeight: 1.02, textShadow: "0 6px 30px rgba(0,0,0,0.85)", maxWidth: 1100, marginTop: 6, opacity: t.opacity, transform: `translateY(${t.translateY}px)` }}>{title}</div>
        </>); })()}
      </AbsoluteFill>

      {caption && (
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 66, textAlign: "center", padding: "0 220px",
          color: "#e9ddce", fontSize: 32, fontWeight: 500, textShadow: "0 4px 22px rgba(0,0,0,0.95)", fontFamily: fontFamily("montserrat"),
          opacity: interpolate(frame, [56, 70], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) * exit }}>{caption}</div>
      )}
      <AbsoluteFill style={{ boxShadow: "inset 0 0 320px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
