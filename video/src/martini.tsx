import {interpolate, useCurrentFrame} from "remotion";
import {COLORS, CRISP_EASE, clamp} from "./brand";

const VOCABULARY = "MIX.STIR.POUR.TASTE.REVISE.REPEAT.";

const createMartini = (width: number, height: number) => {
  const center = Math.floor(width / 2);
  const bowlTop = 3;
  const bowlBottom = Math.floor(height * 0.45);
  const bowlWidth = Math.floor(width * 0.25);
  const stemBottom = height - 3;
  const baseWidth = Math.floor(width * 0.12);

  return Array.from({length: height}, (_, y) =>
    Array.from({length: width}, (_, x) => {
      if (y >= bowlTop && y <= bowlBottom) {
        const progress = (y - bowlTop) / (bowlBottom - bowlTop);
        const halfWidth = Math.max(1, Math.round(bowlWidth * (1 - progress)));
        if (Math.abs(x - center) <= halfWidth) return " ";
      }

      if (y > bowlBottom && y <= stemBottom && x === center) return " ";
      if (y === stemBottom + 1 && Math.abs(x - center) <= baseWidth) return " ";

      return VOCABULARY[(x + y * (width + 7)) % VOCABULARY.length];
    }).join(""),
  ).join("\n");
};

const MARTINI = createMartini(67, 29);

export const AsciiMartini = ({revealAt = 0}: {revealAt?: number}) => {
  const frame = useCurrentFrame();

  return (
    <div
      style={{
        borderBottom: `1px solid ${COLORS.signal}`,
        borderTop: `1px solid ${COLORS.signal}`,
        opacity: interpolate(frame, [revealAt, revealAt + 18], [0, 1], {
          ...clamp,
          easing: CRISP_EASE,
        }),
        padding: "24px 0",
        translate: `0 ${interpolate(frame, [revealAt, revealAt + 42], [42, 0], {
          ...clamp,
          easing: CRISP_EASE,
        })}px`,
      }}
    >
      <pre
        style={{
          color: COLORS.signal,
          fontFamily: "inherit",
          fontSize: 17,
          letterSpacing: "-0.04em",
          lineHeight: 0.92,
          margin: 0,
          textAlign: "center",
          whiteSpace: "pre",
        }}
      >
        {MARTINI}
      </pre>
    </div>
  );
};
