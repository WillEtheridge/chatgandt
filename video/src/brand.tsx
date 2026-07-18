import type {CSSProperties, ReactNode} from "react";
import {AbsoluteFill, Easing, interpolate, staticFile, useCurrentFrame} from "remotion";
import {loadFont} from "@remotion/fonts";

void loadFont({
  family: "Neue Montreal Mono",
  url: staticFile("PPNeueMontrealMono-Book.woff2"),
  format: "woff2",
  weight: "400",
  style: "normal",
  display: "block",
});

export const FONT_FAMILY = "Neue Montreal Mono, Courier New, monospace";

export const COLORS = {
  concrete: "#f0eee9",
  steel: "#020d13",
  outline: "#3b454a",
  muted: "#7a8286",
  signal: "#cd533b",
} as const;

export const CRISP_EASE = Easing.bezier(0.16, 1, 0.3, 1);

export const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const Wordmark = ({
  accentColor = COLORS.signal,
  color = COLORS.steel,
  size = 38,
}: {
  accentColor?: string;
  color?: string;
  size?: number;
}) => (
  <div
    style={{
      color,
      fontFamily: FONT_FAMILY,
      fontSize: size,
      letterSpacing: "-0.06em",
      lineHeight: 1,
      whiteSpace: "nowrap",
    }}
  >
    ChatG<span style={{color: accentColor}}>&amp;</span>T
  </div>
);

const Grid = ({inverse}: {inverse: boolean}) => (
  <AbsoluteFill
    style={{
      backgroundImage: `linear-gradient(to right, ${
        inverse ? "rgba(240,238,233,0.055)" : "rgba(2,13,19,0.055)"
      } 1px, transparent 1px), linear-gradient(to bottom, ${
        inverse ? "rgba(240,238,233,0.045)" : "rgba(2,13,19,0.045)"
      } 1px, transparent 1px)`,
      backgroundPosition: "74px 74px",
      backgroundSize: "116px 116px",
      opacity: 0.6,
    }}
  />
);

export const SceneShell = ({
  children,
  chapter,
  index,
  inverse = false,
  label,
  style,
}: {
  children: ReactNode;
  chapter: string;
  index: string;
  inverse?: boolean;
  label: string;
  style?: CSSProperties;
}) => {
  const frame = useCurrentFrame();
  const foreground = inverse ? COLORS.concrete : COLORS.steel;
  const background = inverse ? COLORS.steel : COLORS.concrete;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: background,
        color: foreground,
        fontFamily: FONT_FAMILY,
        overflow: "hidden",
        ...style,
      }}
    >
      <Grid inverse={inverse} />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          padding: "62px 74px 58px",
          position: "relative",
        }}
      >
        <header
          style={{
            alignItems: "center",
            borderBottom: `1px solid ${inverse ? "rgba(240,238,233,0.35)" : COLORS.outline}`,
            display: "flex",
            flex: "0 0 68px",
            justifyContent: "space-between",
            opacity: interpolate(frame, [0, 12], [0, 1], {
              ...clamp,
              easing: CRISP_EASE,
            }),
            position: "relative",
            zIndex: 2,
          }}
        >
          <Wordmark color={foreground} size={32} />
          <div
            style={{
              fontSize: 22,
              letterSpacing: "0.05em",
              textTransform: "uppercase",
            }}
          >
            {chapter} / {index}
          </div>
        </header>

        <div style={{display: "flex", flex: 1, minHeight: 0}}>{children}</div>

        <footer
          style={{
            alignItems: "center",
            borderTop: `1px solid ${inverse ? "rgba(240,238,233,0.35)" : COLORS.outline}`,
            display: "flex",
            flex: "0 0 52px",
            fontSize: 19,
            justifyContent: "space-between",
            letterSpacing: "0.04em",
            opacity: interpolate(frame, [8, 20], [0, 1], {
              ...clamp,
              easing: CRISP_EASE,
            }),
            textTransform: "uppercase",
            position: "relative",
            zIndex: 2,
          }}
        >
          <span>{label}</span>
          <span style={{color: COLORS.signal}}>■■■□□</span>
        </footer>
      </div>
    </AbsoluteFill>
  );
};

export const Kicker = ({children, inverse = false}: {children: ReactNode; inverse?: boolean}) => (
  <div
    style={{
      color: inverse ? COLORS.signal : COLORS.signal,
      fontSize: 23,
      letterSpacing: "0.05em",
      lineHeight: 1.2,
      textTransform: "uppercase",
    }}
  >
    {children}
  </div>
);

export const Rule = ({color = COLORS.outline}: {color?: string}) => (
  <div style={{backgroundColor: color, height: 1, width: "100%"}} />
);

export const Reveal = ({
  children,
  delay = 0,
  distance = 48,
  duration = 24,
  style,
}: {
  children: ReactNode;
  delay?: number;
  distance?: number;
  duration?: number;
  style?: CSSProperties;
}) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        opacity: interpolate(frame, [delay, delay + duration * 0.65], [0, 1], {
          ...clamp,
          easing: CRISP_EASE,
        }),
        translate: `0 ${interpolate(frame, [delay, delay + duration], [distance, 0], {
          ...clamp,
          easing: CRISP_EASE,
        })}px`,
        ...style,
      }}
    >
      {children}
    </div>
  );
};
