import React from "react";
import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { fontFamily } from "./theme";

export type RedditComment = { author: string; body: string; score?: string };
export type RedditThreadProps = {
  subreddit?: string;        // «r/nosleep» (можно без r/)
  title: string;            // заголовок поста
  author?: string;          // u/username
  age?: string;             // «7 ч. назад»
  upvotes?: number;         // финальное число апвоутов (тикает вверх)
  comments?: string;        // «10.6k» комментов
  body?: string;            // короткий текст поста (опц.)
  awardText?: string;       // плашка сверху «ЛЕГЕНДА / ХУДОЖКА / РЕАЛЬНОЕ ДЕЛО»
  commentList?: RedditComment[];
  accent?: string;
  caption?: string;
};

// Фирменный Reddit-визуал: тёмный пост-интерфейс с сабреддитом, тикающими апвоутами и комментами.
export const RedditThread: React.FC<RedditThreadProps> = ({
  subreddit = "r/nosleep",
  title,
  author = "u/anonymous",
  age = "5h ago",
  upvotes = 24800,
  comments = "3.2k",
  body = "",
  awardText = "",
  commentList = [],
  accent = "#ff4500",
  caption = "",
}) => {
  const frame = useCurrentFrame();
  const { durationInFrames, fps } = useVideoConfig();
  const sub = subreddit.startsWith("r/") ? subreddit : `r/${subreddit}`;
  const exit = interpolate(frame, [durationInFrames - 12, durationInFrames], [1, 0], { extrapolateLeft: "clamp" });
  const cardIn = spring({ frame: frame - 3, fps, config: { damping: 15, stiffness: 120 } });
  // апвоуты тикают вверх
  const up = Math.round(interpolate(frame, [14, 46], [Math.round(upvotes * 0.72), upvotes], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));
  const fmtUp = up >= 1000 ? `${(up / 1000).toFixed(1)}k` : `${up}`;
  const arrowGlow = interpolate(frame, [14, 22], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ background: "#0b0c0e", fontFamily: fontFamily("system"), opacity: exit, overflow: "hidden" }}>
      <AbsoluteFill style={{ background: "radial-gradient(ellipse at 50% 20%, #15171c 0%, #08090b 70%)" }} />
      {/* мягкая «сетка» фона */}
      <AbsoluteFill style={{ background: "repeating-linear-gradient(0deg, rgba(255,255,255,0.015) 0px, rgba(255,255,255,0.015) 1px, transparent 1px, transparent 44px)", pointerEvents: "none" }} />

      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "0 150px" }}>
        <div style={{
          width: 1500, background: "#16181c", borderRadius: 14, border: "1px solid #2a2d34",
          boxShadow: "0 30px 90px rgba(0,0,0,0.75)", overflow: "hidden",
          transform: `translateY(${interpolate(cardIn, [0, 1], [50, 0])}px) scale(${interpolate(cardIn, [0, 1], [0.96, 1])})`,
          opacity: cardIn,
        }}>
          {/* header: сабреддит */}
          <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "22px 30px 8px" }}>
            <div style={{ width: 46, height: 46, borderRadius: "50%", background: accent, display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 800, fontSize: 26 }}>r/</div>
            <span style={{ color: "#d7dadc", fontSize: 30, fontWeight: 700 }}>{sub}</span>
            <span style={{ color: "#7c7f83", fontSize: 24 }}>• Posted by {author} • {age}</span>
            {awardText && (
              <span style={{ marginLeft: "auto", background: accent, color: "#fff", fontSize: 22, fontWeight: 800, letterSpacing: 2, padding: "6px 16px", borderRadius: 6, opacity: interpolate(frame, [30, 42], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }) }}>{awardText}</span>
            )}
          </div>
          {/* title */}
          <div style={{ padding: "6px 30px 18px", color: "#f2f3f5", fontSize: 52, fontWeight: 700, lineHeight: 1.12 }}>{title}</div>
          {body && <div style={{ padding: "0 30px 24px", color: "#b6b9bd", fontSize: 30, lineHeight: 1.4, maxWidth: 1380 }}>{body}</div>}
          {/* footer: upvote + comments */}
          <div style={{ display: "flex", alignItems: "center", gap: 30, padding: "16px 30px", background: "#101216", borderTop: "1px solid #23262c" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
              <span style={{ color: accent, fontSize: 40, filter: `drop-shadow(0 0 ${8 * arrowGlow}px ${accent})`, transform: `translateY(${interpolate(frame % 60, [0, 8, 16], [0, -4, 0], { extrapolateRight: "clamp" })}px)` }}>▲</span>
              <span style={{ color: "#fff", fontSize: 38, fontWeight: 800, fontVariantNumeric: "tabular-nums" }}>{fmtUp}</span>
              <span style={{ color: "#565a5e", fontSize: 40 }}>▼</span>
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 10, color: "#b6b9bd", fontSize: 30, fontWeight: 600 }}>
              <span style={{ fontSize: 32 }}>💬</span> {comments} comments
            </div>
            <div style={{ marginLeft: "auto", color: "#7c7f83", fontSize: 28, fontWeight: 600 }}>Share · Save</div>
          </div>

          {/* опциональная ветка комментариев */}
          {commentList.slice(0, 2).map((c, i) => (
            <div key={i} style={{
              padding: "16px 30px 16px 60px", borderTop: "1px solid #1c1f24",
              opacity: interpolate(frame, [40 + i * 16, 54 + i * 16], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }),
              transform: `translateX(${interpolate(frame, [40 + i * 16, 54 + i * 16], [-20, 0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" })}px)`,
            }}>
              <div style={{ color: "#4fbcff", fontSize: 24, fontWeight: 700, marginBottom: 6 }}>{c.author} <span style={{ color: "#7c7f83", fontWeight: 400 }}>· {c.score || "1.2k"} points</span></div>
              <div style={{ color: "#d7dadc", fontSize: 30, lineHeight: 1.35 }}>{c.body}</div>
            </div>
          ))}
        </div>

        {caption && (
          <div style={{ marginTop: 46, maxWidth: 1440, textAlign: "center", color: "#cfd3da", fontSize: 34, fontWeight: 500, textShadow: "0 4px 20px rgba(0,0,0,0.9)",
            opacity: interpolate(frame, [30, 44], [0, 1], { extrapolateLeft: "clamp", extrapolateRight: "clamp", easing: Easing.out(Easing.cubic) }) }}>{caption}</div>
        )}
      </AbsoluteFill>
      <AbsoluteFill style={{ boxShadow: "inset 0 0 240px rgba(0,0,0,0.75)", pointerEvents: "none" }} />
    </AbsoluteFill>
  );
};
