import React from "react";
import {
  AbsoluteFill,
  Img,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { PALETTE, fontFamily, FontName } from "./theme";

export type EvidenceFrameProps = {
  /** Метка-штамп, напр. "АРХИВ", "ДОКУМЕНТ", "ФОТО". */
  label?: string;
  /** Подпись под штампом: дата/место/источник. */
  sub?: string;
  bgImage?: string | null;
  accent?: string;
  font?: FontName;
};

const MARGIN = 78;
const ARM = 92;
const THICK = 5;

const Corner: React.FC<{ corner: "tl" | "tr" | "bl" | "br"; g: number; color: string }> = ({
  corner,
  g,
  color,
}) => {
  const vert: Record<string, React.CSSProperties> = {
    tl: { left: MARGIN, top: MARGIN },
    tr: { right: MARGIN, top: MARGIN },
    bl: { left: MARGIN, bottom: MARGIN },
    br: { right: MARGIN, bottom: MARGIN },
  };
  const horiz: Record<string, React.CSSProperties> = { ...vert };
  const len = ARM * g;
  return (
    <>
      {/* горизонтальная рука */}
      <div
        style={{
          position: "absolute",
          ...horiz[corner],
          width: len,
          height: THICK,
          background: color,
        }}
      />
      {/* вертикальная рука */}
      <div
        style={{
          position: "absolute",
          ...vert[corner],
          width: THICK,
          height: len,
          background: color,
        }}
      />
    </>
  );
};

// Архивный приём: подать кадр как вещдок — уголки-рамка + штамп + скан-линии.
export const EvidenceFrame: React.FC<EvidenceFrameProps> = ({
  label = "АРХИВ",
  sub = "",
  bgImage = null,
  accent = PALETTE.red,
  font = "oswald",
}) => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();

  const enter = spring({ frame, fps, config: { damping: 200, mass: 0.6 } });
  const cornerG = interpolate(enter, [0, 1], [0, 1]);

  const tagOpacity = interpolate(frame, [6, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const tagX = interpolate(enter, [0, 1], [-20, 0]);

  // мигающая точка «rec/архив»
  const dotOn = Math.sin(frame / 6) > -0.2 ? 1 : 0.25;

  const exit = interpolate(frame, [durationInFrames - 16, durationInFrames], [1, 0], {
    extrapolateLeft: "clamp",
  });

  return (
    <AbsoluteFill style={{ fontFamily: fontFamily(font), opacity: exit }}>
      {bgImage && (
        <Img src={staticFile(bgImage)} style={{ width: "100%", height: "100%", objectFit: "cover" }} />
      )}

      {/* лёгкие скан-линии — «архивность» */}
      <AbsoluteFill
        style={{
          background:
            "repeating-linear-gradient(0deg, rgba(0,0,0,0.10) 0px, rgba(0,0,0,0.10) 1px, transparent 2px, transparent 4px)",
          opacity: 0.5,
          mixBlendMode: "multiply",
        }}
      />
      {/* виньетка по краям */}
      <AbsoluteFill
        style={{
          boxShadow: "inset 0 0 260px rgba(0,0,0,0.55)",
        }}
      />

      {/* уголки-скобки */}
      <Corner corner="tl" g={cornerG} color={PALETTE.cream} />
      <Corner corner="tr" g={cornerG} color={PALETTE.cream} />
      <Corner corner="bl" g={cornerG} color={PALETTE.cream} />
      <Corner corner="br" g={cornerG} color={PALETTE.cream} />

      {/* штамп */}
      <div
        style={{
          position: "absolute",
          left: MARGIN + 20,
          top: MARGIN + 24,
          opacity: tagOpacity,
          transform: `translateX(${tagX}px)`,
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <div
          style={{
            width: 16,
            height: 16,
            borderRadius: "50%",
            background: accent,
            opacity: dotOn,
            boxShadow: `0 0 14px ${accent}`,
          }}
        />
        <div
          style={{
            color: PALETTE.cream,
            fontSize: 40,
            fontWeight: 700,
            letterSpacing: 6,
            textShadow: "0 3px 14px rgba(0,0,0,0.9)",
          }}
        >
          {label}
        </div>
      </div>
      {sub && (
        <div
          style={{
            position: "absolute",
            left: MARGIN + 20,
            top: MARGIN + 78,
            opacity: tagOpacity,
            color: accent,
            fontSize: 28,
            fontWeight: 600,
            letterSpacing: 3,
            textTransform: "uppercase",
            textShadow: "0 3px 14px rgba(0,0,0,0.9)",
          }}
        >
          {sub}
        </div>
      )}
    </AbsoluteFill>
  );
};
