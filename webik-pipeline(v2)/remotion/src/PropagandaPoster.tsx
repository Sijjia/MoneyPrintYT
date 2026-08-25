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

export type PropagandaPosterProps = {
  value: string;
  label: string;
  suffix?: string;
  accent?: string;
};

// Соцреализм/конструктивизм: красная звезда, лучи, число как лозунг на плакате.
export const PropagandaPoster: React.FC<PropagandaPosterProps> = ({
  value,
  label,
  suffix = "",
  accent = PALETTE.red,
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();

  const target = parseInt(value.replace(/\D/g, ""), 10);
  const hasNum = !Number.isNaN(target);
  const t = interpolate(frame, [0, 22], [0, 1], {
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const shown = hasNum ? Math.round(target * t).toLocaleString("ru-RU") : value;

  const slam = spring({ frame, fps, config: { damping: 11, stiffness: 140 }, durationInFrames: 24 });
  const numScale = interpolate(slam, [0, 1], [1.35, 1]);
  const rayRot = frame * 0.25;
  const starPop = spring({ frame: frame - 2, fps, config: { damping: 9, stiffness: 160 } });
  const labelReveal = interpolate(frame, [14, 26], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  const exit = interpolate(frame, [durationInFrames - 15, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });

  const rays = Array.from({ length: 16 });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily("oswald"), opacity: exit }}>
      <AbsoluteFill
        style={{
          background: "linear-gradient(100deg, rgba(0,0,0,0.72) 0%, rgba(0,0,0,0.35) 42%, transparent 66%)",
        }}
      />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "flex-start", paddingLeft: 140 }}>
        <div style={{ position: "relative", width: 980 }}>
          {/* лучи из-за числа */}
          <svg
            width={1100}
            height={1100}
            viewBox="-550 -550 1100 1100"
            style={{ position: "absolute", left: 40, top: -430, opacity: 0.5 * t, transform: `rotate(${rayRot}deg)` }}
          >
            {rays.map((_, i) => {
              const a = (i / rays.length) * Math.PI * 2;
              const x = Math.cos(a) * 540;
              const y = Math.sin(a) * 540;
              const px = Math.cos(a + 0.11) * 120;
              const py = Math.sin(a + 0.11) * 120;
              const nx = Math.cos(a - 0.11) * 120;
              const ny = Math.sin(a - 0.11) * 120;
              return <polygon key={i} points={`${px},${py} ${x},${y} ${nx},${ny}`} fill={accent} opacity={i % 2 ? 0.55 : 0.28} />;
            })}
          </svg>
          {/* звезда */}
          <svg width={150} height={150} viewBox="-50 -50 100 100" style={{ position: "absolute", left: -8, top: -140, transform: `scale(${starPop})` }}>
            <polygon
              points={Array.from({ length: 5 })
                .map((_, i) => {
                  const a = (-90 + i * 72) * (Math.PI / 180);
                  const ao = (-90 + i * 72 + 36) * (Math.PI / 180);
                  return `${Math.cos(a) * 46},${Math.sin(a) * 46} ${Math.cos(ao) * 19},${Math.sin(ao) * 19}`;
                })
                .join(" ")}
              fill={accent}
              stroke={PALETTE.cream}
              strokeWidth={3}
            />
          </svg>
          {/* число-лозунг */}
          <div
            style={{
              color: PALETTE.cream,
              fontSize: 250,
              fontWeight: 800,
              lineHeight: 0.85,
              letterSpacing: -6,
              transform: `scale(${numScale})`,
              transformOrigin: "left center",
              textShadow: `0 0 60px ${accent}, 0 12px 40px rgba(0,0,0,0.8)`,
              WebkitTextStroke: `2px ${accent}`,
            }}
          >
            {shown}
            <span style={{ color: accent }}>{suffix}</span>
          </div>
          {/* лента-лозунг */}
          <div style={{ marginTop: 26, overflow: "hidden", width: `${labelReveal * 100}%` }}>
            <div
              style={{
                display: "inline-block",
                background: accent,
                color: PALETTE.cream,
                fontSize: 52,
                fontWeight: 700,
                letterSpacing: 4,
                textTransform: "uppercase",
                padding: "10px 34px",
                whiteSpace: "nowrap",
                boxShadow: `0 8px 30px ${accent}88`,
                transform: "skewX(-8deg)",
              }}
            >
              <span style={{ display: "inline-block", transform: "skewX(8deg)" }}>{label}</span>
            </div>
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
