import React from "react";
import {
  AbsoluteFill,
  interpolate,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily } from "./theme";

export type CollapseBurstProps = {
  title?: string;
  accent?: string;
};

const ICONS: Record<string, React.ReactNode> = {
  hospital: (<g><rect x="60" y="70" width="200" height="200" rx="10" fill="none" stroke="currentColor" strokeWidth="12" /><rect x="145" y="110" width="30" height="120" fill="currentColor" /><rect x="100" y="155" width="120" height="30" fill="currentColor" /></g>),
  airport: (<g><path d="M60 250 L160 60 L260 250" fill="none" stroke="currentColor" strokeWidth="12" /><rect x="120" y="150" width="80" height="100" fill="none" stroke="currentColor" strokeWidth="12" /><line x1="140" y1="60" x2="180" y2="60" stroke="currentColor" strokeWidth="12" /></g>),
  bank: (<g><polygon points="160,50 280,120 40,120" fill="none" stroke="currentColor" strokeWidth="12" /><line x1="80" y1="130" x2="80" y2="240" stroke="currentColor" strokeWidth="14" /><line x1="160" y1="130" x2="160" y2="240" stroke="currentColor" strokeWidth="14" /><line x1="240" y1="130" x2="240" y2="240" stroke="currentColor" strokeWidth="14" /><rect x="40" y="250" width="240" height="20" fill="currentColor" /></g>),
  factory: (<g><path d="M50 260 V150 L120 190 V150 L190 190 V150 L260 190 V260 Z" fill="none" stroke="currentColor" strokeWidth="12" /><rect x="70" y="80" width="26" height="80" fill="currentColor" /></g>),
};

// Вспышка-монтаж: больницы/аэропорты/банки/заводы ВСТАЛИ (удар WannaCry).
export const CollapseBurst: React.FC<CollapseBurstProps> = ({
  title,
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames } = useVideoConfig();
  const exit = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const items = [
    { icon: "hospital", label: "БОЛЬНИЦЫ" },
    { icon: "airport", label: "АЭРОПОРТЫ" },
    { icon: "bank", label: "БАНКИ" },
    { icon: "factory", label: "ЗАВОДЫ" },
  ];
  const PER = 24; // 0.8с
  const idx = Math.min(items.length - 1, Math.floor(frame / PER));
  const local = frame - idx * PER;
  const flash = local < 3 ? 1 - local / 3 : 0; // белая вспышка «щелчок»
  const shake = local < 5 ? Math.sin(local * 4) * 6 : 0;
  const it = items[idx];

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill style={{ background: "#070202" }} />
      {/* скан-лайны */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(217,40,40,0.07) 0 1px, transparent 3px 6px)", pointerEvents: "none" }} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", transform: `translateX(${shake}px)` }}>
        <div style={{ color: accent, width: 320, height: 320, filter: `drop-shadow(0 0 20px ${accent})` }}>
          <svg width={320} height={320} viewBox="0 0 320 320">{ICONS[it.icon]}</svg>
        </div>
        <div style={{ marginTop: 20, color: PALETTE.cream, fontSize: 96, fontWeight: 800, letterSpacing: 6 }}>{it.label}</div>
        {/* штамп ВСТАЛО */}
        <div style={{ marginTop: 16, transform: "rotate(-6deg)", color: accent, border: `6px solid ${accent}`, padding: "6px 34px", fontSize: 64, fontWeight: 800, letterSpacing: 6, textShadow: `0 0 14px ${accent}`, boxShadow: `0 0 0 3px ${accent}33` }}>ВСТАЛО</div>
      </AbsoluteFill>

      {/* индикатор прогресса */}
      <AbsoluteFill style={{ justifyContent: "flex-end", alignItems: "center", paddingBottom: 70, pointerEvents: "none" }}>
        <div style={{ display: "flex", gap: 14 }}>
          {items.map((_, i) => <div key={i} style={{ width: 60, height: 8, background: i <= idx ? accent : "#3a1010", boxShadow: i === idx ? `0 0 10px ${accent}` : undefined }} />)}
        </div>
      </AbsoluteFill>

      <AbsoluteFill style={{ boxShadow: "inset 0 0 260px rgba(0,0,0,0.85)", pointerEvents: "none" }} />
      {/* вспышка-щелчок */}
      <AbsoluteFill style={{ background: "#fff", opacity: flash * 0.85, pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
