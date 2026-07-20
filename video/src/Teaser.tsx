import type {CSSProperties, ReactNode} from "react";
import {Audio} from "@remotion/media";
import {AbsoluteFill, interpolate, Sequence, staticFile, useCurrentFrame} from "remotion";
import {
  clamp,
  COLORS,
  CRISP_EASE,
  FONT_FAMILY,
  Wordmark,
} from "./brand";

export const TEASER_VIDEO = {
  durationInFrames: 600,
  fps: 30,
  height: 1350,
  width: 1080,
} as const;

const CUTS = {
  brand: {duration: 42, from: 126},
  demo: {duration: 168, from: 168},
  experiment: {duration: 72, from: 336},
  final: {duration: 84, from: 516},
  hook: {duration: 78, from: 0},
  punchline: {duration: 48, from: 78},
  tasting: {duration: 108, from: 408},
} as const;

type Palette = "concrete" | "signal" | "steel";

const PALETTES: Record<Palette, {background: string; foreground: string; grid: string}> = {
  concrete: {
    background: COLORS.concrete,
    foreground: COLORS.steel,
    grid: "rgba(2,13,19,0.065)",
  },
  signal: {
    background: COLORS.signal,
    foreground: COLORS.concrete,
    grid: "rgba(240,238,233,0.12)",
  },
  steel: {
    background: COLORS.steel,
    foreground: COLORS.concrete,
    grid: "rgba(240,238,233,0.065)",
  },
};

const enter = (
  frame: number,
  at = 0,
  distance = 70,
  duration = 10,
): CSSProperties => ({
  opacity: interpolate(frame, [at, at + Math.max(3, duration * 0.55)], [0, 1], {
    ...clamp,
    easing: CRISP_EASE,
  }),
  transform: `translateY(${interpolate(
    frame,
    [at, at + duration],
    [distance, 0],
    {...clamp, easing: CRISP_EASE},
  )}px)`,
});

const slide = (
  frame: number,
  at = 0,
  distance = 120,
  duration = 10,
): CSSProperties => ({
  opacity: interpolate(frame, [at, at + Math.max(3, duration * 0.55)], [0, 1], {
    ...clamp,
    easing: CRISP_EASE,
  }),
  transform: `translateX(${interpolate(
    frame,
    [at, at + duration],
    [distance, 0],
    {...clamp, easing: CRISP_EASE},
  )}px)`,
});

const Grid = ({grid}: {grid: string}) => (
  <AbsoluteFill
    style={{
      backgroundImage: `linear-gradient(to right, ${grid} 1px, transparent 1px), linear-gradient(to bottom, ${grid} 1px, transparent 1px)`,
      backgroundPosition: "64px 64px",
      backgroundSize: "112px 112px",
    }}
  />
);

const Progress = ({active, foreground}: {active: number; foreground: string}) => (
  <div style={{display: "flex", gap: 8}}>
    {Array.from({length: 7}, (_, index) => (
      <div
        key={index}
        style={{
          backgroundColor: index <= active ? COLORS.signal : foreground,
          height: 8,
          opacity: index <= active ? 1 : 0.28,
          width: index === active ? 34 : 13,
        }}
      />
    ))}
  </div>
);

const TeaserShell = ({
  active,
  children,
  label,
  palette = "concrete",
  showBrand = true,
}: {
  active: number;
  children: ReactNode;
  label: string;
  palette?: Palette;
  showBrand?: boolean;
}) => {
  const colors = PALETTES[palette];

  return (
    <AbsoluteFill
      style={{
        backgroundColor: colors.background,
        color: colors.foreground,
        fontFamily: FONT_FAMILY,
        overflow: "hidden",
      }}
    >
      <Grid grid={colors.grid} />
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          height: "100%",
          padding: "58px 64px 52px",
          position: "relative",
          zIndex: 1,
        }}
      >
        <header
          style={{
            alignItems: "center",
            borderBottom: `1px solid ${colors.foreground}`,
            display: "flex",
            flex: "0 0 62px",
            justifyContent: "space-between",
          }}
        >
          {showBrand ? (
            <Wordmark
              accentColor={palette === "signal" ? COLORS.steel : COLORS.signal}
              color={colors.foreground}
              size={29}
            />
          ) : (
            <span style={{fontSize: 21, letterSpacing: "0.06em"}}>CGT / 001</span>
          )}
          <span style={{fontSize: 20, letterSpacing: "0.05em", textTransform: "uppercase"}}>
            {label}
          </span>
        </header>

        <div style={{display: "flex", flex: 1, minHeight: 0}}>{children}</div>

        <footer
          style={{
            alignItems: "center",
            borderTop: `1px solid ${colors.foreground}`,
            display: "flex",
            flex: "0 0 48px",
            justifyContent: "space-between",
          }}
        >
          <span style={{fontSize: 18, letterSpacing: "0.05em"}}>USEFUL ANSWERS / MIXED DIFFERENTLY</span>
          <Progress active={active} foreground={colors.foreground} />
        </footer>
      </div>
    </AbsoluteFill>
  );
};

const HookScene = () => {
  const frame = useCurrentFrame();
  const beats = [
    {from: 0, palette: "concrete" as const, size: 215, text: "AN AI", to: 20},
    {from: 20, palette: "steel" as const, size: 176, text: "WALKED\nINTO", to: 43},
    {from: 43, palette: "signal" as const, size: 228, text: "A BAR.", to: 78},
  ];
  const beat = beats.find(({from, to}) => frame >= from && frame < to) ?? beats[2];
  const localFrame = frame - beat.from;

  return (
    <TeaserShell active={0} label="OPENING LINE" palette={beat.palette} showBrand={false}>
      <div style={{alignItems: "center", display: "flex", flex: 1, minWidth: 0}}>
        <div
          style={{
            ...slide(localFrame, 0, 170, 9),
            fontSize: beat.size,
            letterSpacing: "-0.085em",
            lineHeight: 0.82,
            textTransform: "uppercase",
            whiteSpace: "pre-line",
            width: "100%",
          }}
        >
          {beat.text}
        </div>
        <div
          style={{
            backgroundColor: beat.palette === "signal" ? COLORS.steel : COLORS.signal,
            height: interpolate(localFrame, [0, 12], [0, 610], {...clamp, easing: CRISP_EASE}),
            position: "absolute",
            right: 64,
            top: 300,
            width: 18,
          }}
        />
      </div>
    </TeaserShell>
  );
};

const PunchlineScene = () => {
  const frame = useCurrentFrame();

  if (frame < 10) {
    return (
      <TeaserShell active={1} label="TRUE STORY" palette="concrete">
        <div
          style={{
            alignItems: "center",
            display: "flex",
            flex: 1,
            fontSize: 146,
            letterSpacing: "-0.075em",
            lineHeight: 0.9,
          }}
        >
          NO, REALLY.
        </div>
      </TeaserShell>
    );
  }

  const localFrame = frame - 10;
  return (
    <TeaserShell active={1} label="THE PREMISE" palette="steel">
      <div
        style={{
          display: "flex",
          flex: 1,
          flexDirection: "column",
          justifyContent: "center",
          minWidth: 0,
        }}
      >
        {["I TAUGHT IT", "TO MIX", "ANSWERS."].map((line, index) => (
          <div
            key={line}
            style={{
              ...slide(localFrame, index * 5, index % 2 === 0 ? -150 : 150, 9),
              color: index === 2 ? COLORS.signal : COLORS.concrete,
              fontSize: index === 2 ? 150 : 120,
              letterSpacing: "-0.075em",
              lineHeight: 0.88,
              textAlign: index === 1 ? "right" : "left",
              whiteSpace: "nowrap",
            }}
          >
            {line}
          </div>
        ))}
      </div>
    </TeaserShell>
  );
};

const BrandScene = () => {
  const frame = useCurrentFrame();

  return (
    <TeaserShell active={2} label="MEET THE MODEL" palette="concrete" showBrand={false}>
      <div style={{display: "flex", flex: 1, flexDirection: "column", justifyContent: "center"}}>
        <div style={enter(frame, 0, 90, 11)}>
          <Wordmark size={180} />
        </div>
        <div
          style={{
            ...enter(frame, 7, 60, 11),
            borderLeft: `12px solid ${COLORS.signal}`,
            fontSize: 64,
            letterSpacing: "-0.055em",
            lineHeight: 1.03,
            marginTop: 68,
            paddingLeft: 32,
          }}
        >
          Useful answers,
          <br />
          mixed differently.
        </div>
      </div>
    </TeaserShell>
  );
};

const PromptBeat = ({frame}: {frame: number}) => (
  <TeaserShell active={3} label="SPIRIT GUIDE" palette="concrete">
    <div style={{display: "flex", flex: 1, flexDirection: "column", justifyContent: "center"}}>
      <div style={{...enter(frame, 0, 60, 9), color: COLORS.signal, fontSize: 24, marginBottom: 26}}>
        NEW ORDER / LOW-STAKES QUESTION
      </div>
      <div
        style={{
          ...enter(frame, 2, 90, 10),
          border: `3px solid ${COLORS.steel}`,
          fontSize: 62,
          letterSpacing: "-0.055em",
          lineHeight: 1.07,
          padding: "46px 44px 52px",
        }}
      >
        Explain why compound interest grows faster over time.
      </div>
      <div
        style={{
          ...enter(frame, 9, 30, 8),
          alignSelf: "flex-end",
          backgroundColor: COLORS.signal,
          color: COLORS.concrete,
          fontSize: 27,
          marginTop: 24,
          padding: "18px 28px",
        }}
      >
        MIX ME AN ANSWER →
      </div>
    </div>
  </TeaserShell>
);

const MixingBeat = ({frame}: {frame: number}) => {
  const dots = ".".repeat((Math.floor(frame / 6) % 3) + 1);
  const progress = Math.round(interpolate(frame, [0, 77], [6, 99], clamp));
  const activeStage = frame < 24 ? 0 : frame < 52 ? 1 : 2;

  return (
    <TeaserShell active={3} label="PROCESSING" palette="signal">
      <div style={{alignItems: "center", display: "flex", flex: 1, flexDirection: "column", justifyContent: "center"}}>
        <div style={{fontSize: 140, letterSpacing: "-0.08em", lineHeight: 1}}>MIXING{dots}</div>
        <div style={{marginTop: 48, width: "100%"}}>
          <div style={{border: `2px solid ${COLORS.steel}`, height: 18, padding: 3}}>
            <div
              style={{
                backgroundColor: COLORS.steel,
                height: "100%",
                width: `${progress}%`,
              }}
            />
          </div>
          <div
            style={{
              display: "flex",
              fontSize: 21,
              justifyContent: "space-between",
              letterSpacing: "0.04em",
              marginTop: 13,
              width: "100%",
            }}
          >
            <span>RECIPE STRUCTURE = ANSWER STRUCTURE</span>
            <span>{progress}%</span>
          </div>
        </div>
        <div
          style={{
            display: "flex",
            fontSize: 25,
            gap: 20,
            justifyContent: "space-between",
            marginTop: 44,
            width: "100%",
          }}
        >
          {["QUESTION", "STRUCTURE", "RECIPE"].map((item, index) => (
            <div
              key={item}
              style={{
                backgroundColor: index <= activeStage ? COLORS.steel : "transparent",
                border: `2px solid ${COLORS.steel}`,
                color: index <= activeStage ? COLORS.concrete : COLORS.steel,
                flex: 1,
                padding: "18px 8px",
                textAlign: "center",
              }}
            >
              {item}
            </div>
          ))}
        </div>
      </div>
    </TeaserShell>
  );
};

const RecipeBeat = ({frame}: {frame: number}) => (
  <TeaserShell active={3} label="FIRST POUR / PARTIAL" palette="steel">
    <div style={{display: "flex", flex: 1, flexDirection: "column", justifyContent: "center"}}>
      <div style={{...enter(frame, 0, 70, 10), color: COLORS.signal, fontSize: 24, marginBottom: 22}}>
        SERVED AS A METAPHORICAL COCKTAIL
      </div>
      <div
        style={{
          ...enter(frame, 2, 90, 10),
          fontSize: 100,
          letterSpacing: "-0.075em",
          lineHeight: 0.86,
        }}
      >
        COMPOUNDING
        <br />
        SNOWBALL
        <br />
        <span style={{color: COLORS.signal}}>SWIZZLE</span>
      </div>
      <div
        style={{
          ...enter(frame, 10, 50, 10),
          alignItems: "center",
          borderBottom: `2px solid ${COLORS.signal}`,
          borderTop: `2px solid ${COLORS.signal}`,
          display: "flex",
          fontSize: 66,
          justifyContent: "space-between",
          letterSpacing: "-0.04em",
          marginTop: 62,
          padding: "25px 0 23px",
        }}
      >
        <span>100</span>
        <span style={{color: COLORS.signal}}>→</span>
        <span>110</span>
        <span style={{color: COLORS.signal}}>→</span>
        <span>121</span>
      </div>
    </div>
  </TeaserShell>
);

const DemoScene = () => {
  const frame = useCurrentFrame();

  if (frame < 36) return <PromptBeat frame={frame} />;
  if (frame < 114) return <MixingBeat frame={frame - 36} />;
  return <RecipeBeat frame={frame - 114} />;
};

const ExperimentScene = () => {
  const frame = useCurrentFrame();

  if (frame < 30) {
    return (
      <TeaserShell active={4} label="THE EXPERIMENT" palette="signal">
        <div
          style={{
            ...slide(frame, 0, 150, 10),
            display: "flex",
            flex: 1,
            flexDirection: "column",
            fontSize: 100,
            justifyContent: "center",
            letterSpacing: "-0.07em",
            lineHeight: 0.9,
          }}
        >
          <span>THEN I MADE IT</span>
          <span>COMPETE WITH</span>
          <span style={{alignSelf: "flex-end", color: COLORS.steel}}>ITSELF.</span>
        </div>
      </TeaserShell>
    );
  }

  const localFrame = frame - 30;
  return (
    <AbsoluteFill style={{backgroundColor: COLORS.concrete, color: COLORS.steel, fontFamily: FONT_FAMILY}}>
      <div style={{display: "flex", height: "100%"}}>
        <div
          style={{
            backgroundColor: COLORS.concrete,
            display: "flex",
            flex: 1,
            flexDirection: "column",
            justifyContent: "center",
            padding: "86px 48px 100px 64px",
          }}
        >
          <div style={{...slide(localFrame, 0, -120, 9), color: COLORS.signal, fontSize: 31}}>A / PROMPTED</div>
          <div
            style={{
              ...slide(localFrame, 3, -120, 9),
              fontSize: 87,
              letterSpacing: "-0.07em",
              lineHeight: 0.9,
              marginTop: 52,
            }}
          >
            TEACH IT
            <br />
            IN THE
            <br />
            PROMPT.
          </div>
        </div>
        <div
          style={{
            backgroundColor: COLORS.steel,
            color: COLORS.concrete,
            display: "flex",
            flex: 1,
            flexDirection: "column",
            justifyContent: "center",
            padding: "86px 64px 100px 48px",
          }}
        >
          <div style={{...slide(localFrame, 0, 120, 9), color: COLORS.signal, fontSize: 31}}>B / FINE-TUNED</div>
          <div
            style={{
              ...slide(localFrame, 3, 120, 9),
              fontSize: 87,
              letterSpacing: "-0.07em",
              lineHeight: 0.9,
              marginTop: 52,
            }}
          >
            TEACH IT
            <br />
            IN THE
            <br />
            WEIGHTS.
          </div>
        </div>
      </div>
      <div
        style={{
          ...enter(localFrame, 9, 30, 8),
          backgroundColor: COLORS.signal,
          bottom: 54,
          color: COLORS.concrete,
          fontSize: 27,
          left: 64,
          letterSpacing: "0.02em",
          padding: "18px 28px",
          position: "absolute",
          right: 64,
          textAlign: "center",
        }}
      >
        SAME 1.5B MODEL · 60 UNSEEN QUESTIONS
      </div>
    </AbsoluteFill>
  );
};

const ChoiceCard = ({
  active,
  code,
  lines,
  title,
}: {
  active: boolean;
  code: string;
  lines: string[];
  title: string;
}) => (
  <div
    style={{
      backgroundColor: active ? COLORS.steel : "transparent",
      border: `3px solid ${active ? COLORS.signal : COLORS.steel}`,
      color: active ? COLORS.concrete : COLORS.steel,
      display: "flex",
      flex: 1,
      flexDirection: "column",
      minWidth: 0,
      padding: "30px 27px",
    }}
  >
    <div style={{color: COLORS.signal, fontSize: 24}}>{code}</div>
    <div
      style={{
        fontSize: 42,
        letterSpacing: "-0.05em",
        lineHeight: 0.98,
        marginTop: 35,
        minHeight: 126,
      }}
    >
      {title}
    </div>
    <div style={{borderTop: `1px solid ${active ? COLORS.concrete : COLORS.steel}`, marginTop: 28, paddingTop: 24}}>
      {lines.map((line, index) => (
        <div key={line} style={{fontSize: 22, marginTop: index === 0 ? 0 : 13, opacity: 0.78}}>
          {String(index + 1).padStart(2, "0")} / {line}
        </div>
      ))}
    </div>
  </div>
);

const TastingScene = () => {
  const frame = useCurrentFrame();

  if (frame < 36) {
    return (
      <TeaserShell active={5} label="TASTING ROOM" palette="signal">
        <div
          style={{
            ...slide(frame, 0, 160, 9),
            display: "flex",
            flex: 1,
            flexDirection: "column",
            fontSize: 112,
            justifyContent: "center",
            letterSpacing: "-0.075em",
            lineHeight: 0.88,
          }}
        >
          <span>CAN YOU SPOT</span>
          <span>
            THE <span style={{color: COLORS.steel}}>FINE-TUNE?</span>
          </span>
        </div>
      </TeaserShell>
    );
  }

  const localFrame = frame - 36;
  const activeChoice = localFrame < 28 ? 0 : localFrame < 56 ? 1 : -1;

  return (
    <TeaserShell active={5} label="PICK ONE / NO PEEKING" palette="concrete">
      <div style={{display: "flex", flex: 1, flexDirection: "column", justifyContent: "center"}}>
        <div style={{display: "flex", gap: 20, height: 610}}>
          <ChoiceCard
            active={activeChoice === 0}
            code="RESPONSE / A"
            lines={["CLARIFY", "REFRAME", "SERVE"]}
            title="CLEAR-SURFACE COLLINS"
          />
          <ChoiceCard
            active={activeChoice === 1}
            code="RESPONSE / B"
            lines={["START SMALL", "BUILD", "REPEAT"]}
            title="FIRST-WIN HIGHBALL"
          />
        </div>
        <div
          style={{
            ...enter(localFrame, 3, 30, 8),
            fontSize: 27,
            letterSpacing: "0.04em",
            marginTop: 28,
            textAlign: "center",
          }}
        >
          ONE IS PROMPTED. ONE IS FINE-TUNED.
        </div>
      </div>
    </TeaserShell>
  );
};

export type ChatGntTeaserProps = {
  url: string;
  withAudio?: boolean;
};

const FinalScene = ({url}: ChatGntTeaserProps) => {
  const frame = useCurrentFrame();

  return (
    <TeaserShell active={6} label="FULL EXPERIMENT" palette="concrete">
      <div style={{display: "flex", flex: 1, flexDirection: "column", justifyContent: "center"}}>
        <div
          style={{
            ...enter(frame, 0, 75, 10),
            fontSize: 112,
            letterSpacing: "-0.075em",
            lineHeight: 0.9,
          }}
        >
          TASTE IT
          <br />
          <span style={{color: COLORS.signal}}>FOR YOURSELF.</span>
        </div>
        <div
          style={{
            ...enter(frame, 7, 45, 10),
            alignItems: "center",
            backgroundColor: COLORS.signal,
            color: COLORS.concrete,
            display: "flex",
            fontSize: 43,
            justifyContent: "space-between",
            letterSpacing: "-0.03em",
            marginTop: 70,
            padding: "31px 34px 29px",
          }}
        >
          <span>ENTER THE TASTING ROOM</span>
          <span>→</span>
        </div>
        <div
          style={{
            ...enter(frame, 13, 30, 9),
            alignItems: "flex-end",
            display: "flex",
            justifyContent: "space-between",
            marginTop: 44,
          }}
        >
          <Wordmark size={53} />
          <div style={{fontSize: 22, letterSpacing: "0.015em", textAlign: "right"}}>
            {url}
          </div>
        </div>
      </div>
    </TeaserShell>
  );
};

const TeaserSoundtrack = () => (
  <>
    <Sequence name="Audio — Original 150 BPM beat" layout="none">
      <Audio src={staticFile("audio/teaser-beat.wav")} volume={0.68} />
    </Sequence>
    <Sequence name="Audio — Frame-locked sound design" layout="none">
      <Audio src={staticFile("audio/teaser-sfx.wav")} volume={0.78} />
    </Sequence>
  </>
);

export const ChatGntTeaser = ({url, withAudio = true}: ChatGntTeaserProps) => (
  <>
    <Sequence from={CUTS.hook.from} durationInFrames={CUTS.hook.duration} name="01 — An AI walked into a bar">
      <HookScene />
    </Sequence>
    <Sequence
      from={CUTS.punchline.from}
      durationInFrames={CUTS.punchline.duration}
      name="02 — I taught it to mix answers"
    >
      <PunchlineScene />
    </Sequence>
    <Sequence from={CUTS.brand.from} durationInFrames={CUTS.brand.duration} name="03 — Brand flash">
      <BrandScene />
    </Sequence>
    <Sequence from={CUTS.demo.from} durationInFrames={CUTS.demo.duration} name="04 — Fast product pour">
      <DemoScene />
    </Sequence>
    <Sequence
      from={CUTS.experiment.from}
      durationInFrames={CUTS.experiment.duration}
      name="05 — Prompt versus fine-tune"
    >
      <ExperimentScene />
    </Sequence>
    <Sequence from={CUTS.tasting.from} durationInFrames={CUTS.tasting.duration} name="06 — Tasting Room">
      <TastingScene />
    </Sequence>
    <Sequence from={CUTS.final.from} durationInFrames={CUTS.final.duration} name="07 — Curiosity CTA">
      <FinalScene url={url} />
    </Sequence>
    {withAudio ? <TeaserSoundtrack /> : null}
  </>
);
