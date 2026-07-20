import type {CSSProperties, ReactNode} from "react";
import {AbsoluteFill, interpolate, useCurrentFrame} from "remotion";
import {
  COLORS,
  CRISP_EASE,
  FONT_FAMILY,
  Kicker,
  Reveal,
  Rule,
  SceneShell,
  Wordmark,
  clamp,
} from "./brand";
import {AsciiMartini} from "./martini";

const fullFrame: CSSProperties = {
  alignItems: "stretch",
  display: "flex",
  flexDirection: "column",
  height: "100%",
  justifyContent: "center",
  width: "100%",
};

export const HookScene = () => {
  const frame = useCurrentFrame();
  const firstExit = interpolate(frame, [76, 91], [0, -160], {
    ...clamp,
    easing: CRISP_EASE,
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.steel,
        color: COLORS.concrete,
        fontFamily: FONT_FAMILY,
        overflow: "hidden",
        padding: "78px 74px 70px",
      }}
    >
      <div
        style={{
          backgroundColor: COLORS.signal,
          height: interpolate(frame, [0, 18], [0, 14], {
            ...clamp,
            easing: CRISP_EASE,
          }),
          left: 0,
          position: "absolute",
          top: 0,
          width: "100%",
        }}
      />

      <div
        style={{
          display: "flex",
          justifyContent: "space-between",
          opacity: interpolate(frame, [2, 18], [0, 1], {
            ...clamp,
            easing: CRISP_EASE,
          }),
        }}
      >
        <span style={{fontSize: 22, letterSpacing: "0.05em"}}>OPENING_LINE / 01</span>
        <span style={{color: COLORS.signal, fontSize: 22}}>■■□□□</span>
      </div>

      <div style={{flex: 1, position: "relative"}}>
        <div
          style={{
            bottom: 126,
            left: 0,
            position: "absolute",
            right: 0,
            translate: `0 ${firstExit}px`,
          }}
        >
          <Reveal delay={8} distance={80} duration={28}>
            <div
              style={{
                fontSize: 103,
                letterSpacing: "-0.075em",
                lineHeight: 0.93,
                maxWidth: 930,
              }}
            >
              A SMALL LANGUAGE MODEL
            </div>
          </Reveal>
          <Reveal delay={24} distance={80} duration={28}>
            <div
              style={{
                color: COLORS.signal,
                fontSize: 103,
                letterSpacing: "-0.075em",
                lineHeight: 0.93,
                marginTop: 24,
              }}
            >
              WALKS INTO A BAR.
            </div>
          </Reveal>
        </div>

        <div
          style={{
            bottom: 108,
            left: 0,
            opacity: interpolate(frame, [82, 95], [0, 1], {
              ...clamp,
              easing: CRISP_EASE,
            }),
            position: "absolute",
            right: 0,
            translate: `0 ${interpolate(frame, [82, 105], [90, 0], {
              ...clamp,
              easing: CRISP_EASE,
            })}px`,
          }}
        >
          <div style={{fontSize: 31, letterSpacing: "0.04em", textTransform: "uppercase"}}>
            So I taught it to
          </div>
          <div
            style={{
              color: COLORS.signal,
              fontSize: 118,
              letterSpacing: "-0.08em",
              lineHeight: 0.92,
              marginTop: 18,
            }}
          >
            MIX ANSWERS.
          </div>
        </div>
      </div>

      <div
        style={{
          alignItems: "center",
          borderTop: `1px solid rgba(240,238,233,0.35)`,
          display: "flex",
          height: 68,
          justifyContent: "space-between",
          opacity: interpolate(frame, [91, 106], [0, 1], {
            ...clamp,
            easing: CRISP_EASE,
          }),
        }}
      >
        <Wordmark color={COLORS.concrete} size={34} />
        <span style={{fontSize: 20, letterSpacing: "0.05em"}}>QWEN2.5 / 1.5B / LoRA</span>
      </div>
    </AbsoluteFill>
  );
};

export const BrandScene = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.signal,
        color: COLORS.steel,
        fontFamily: FONT_FAMILY,
        overflow: "hidden",
        padding: "74px",
      }}
    >
      <div
        style={{
          border: `1px solid ${COLORS.steel}`,
          height: "100%",
          padding: "54px 52px",
          position: "relative",
          scale: interpolate(frame, [0, 18], [1.05, 1], {
            ...clamp,
            easing: CRISP_EASE,
          }),
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            opacity: interpolate(frame, [0, 12], [0, 1], {
              ...clamp,
              easing: CRISP_EASE,
            }),
          }}
        >
          <span style={{fontSize: 21, letterSpacing: "0.05em"}}>HOUSE_SPECIAL / 001</span>
          <span style={{fontSize: 21}}>MIX.STIR.POUR.</span>
        </div>

        <div
          style={{
            left: 52,
            position: "absolute",
            right: 52,
            top: 290,
          }}
        >
          <div
          style={{
            overflow: "hidden",
            width: `${interpolate(frame, [8, 40], [0, 100], {
              ...clamp,
              easing: CRISP_EASE,
            })}%`,
          }}
        >
            <div style={{width: 820}}>
              <Wordmark accentColor={COLORS.steel} color={COLORS.steel} size={190} />
            </div>
          </div>
          <div
            style={{
              borderTop: `2px solid ${COLORS.steel}`,
              fontSize: 64,
              letterSpacing: "-0.06em",
              lineHeight: 1.03,
              marginTop: 42,
              opacity: interpolate(frame, [28, 48], [0, 1], {
                ...clamp,
                easing: CRISP_EASE,
              }),
              paddingTop: 34,
            }}
          >
            USEFUL ANSWERS,
            <br />
            MIXED DIFFERENTLY.
          </div>
        </div>

        <div
          style={{
            bottom: 50,
            display: "flex",
            fontSize: 22,
            justifyContent: "space-between",
            left: 52,
            letterSpacing: "0.04em",
            position: "absolute",
            right: 52,
          }}
        >
          <span>SPIRIT GUIDE / TASTING ROOM</span>
          <span>→</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

const Typewriter = ({text, start, end}: {text: string; start: number; end: number}) => {
  const frame = useCurrentFrame();
  const visibleCharacters = Math.floor(
    interpolate(frame, [start, end], [0, text.length], {
      ...clamp,
    }),
  );
  const showCursor = frame < end + 12 && Math.floor(frame / 6) % 2 === 0;

  return (
    <span>
      {text.slice(0, visibleCharacters)}
      <span style={{color: COLORS.signal, opacity: showCursor ? 1 : 0}}>▌</span>
    </span>
  );
};

const PromptPhase = () => (
  <div style={{...fullFrame, gap: 38, justifyContent: "center"}}>
    <Reveal delay={2}>
      <Kicker>Place your order</Kicker>
      <div
        style={{
          fontSize: 74,
          letterSpacing: "-0.07em",
          lineHeight: 0.96,
          marginTop: 20,
        }}
      >
        ASK A QUESTION.
      </div>
    </Reveal>

    <Reveal delay={14} distance={36}>
      <div
        style={{
          alignItems: "flex-end",
          border: `2px solid ${COLORS.outline}`,
          display: "flex",
          minHeight: 218,
          padding: "30px 30px 26px",
        }}
      >
        <div
          style={{
            flex: 1,
            fontSize: 38,
            letterSpacing: "-0.035em",
            lineHeight: 1.3,
            paddingRight: 20,
          }}
        >
          <Typewriter
            end={76}
            start={19}
            text="Explain why compound interest grows faster over time."
          />
        </div>
        <div
          style={{
            alignItems: "center",
            backgroundColor: COLORS.signal,
            color: COLORS.concrete,
            display: "flex",
            fontSize: 44,
            height: 74,
            justifyContent: "center",
            width: 74,
          }}
        >
          ↗
        </div>
      </div>
    </Reveal>

    <Reveal delay={70} distance={18} duration={14}>
      <div style={{display: "flex", fontSize: 22, justifyContent: "space-between"}}>
        <span>ORDER_01 / LOW-STAKES / SINGLE TURN</span>
        <span style={{color: COLORS.signal}}>MIX IT →</span>
      </div>
    </Reveal>
  </div>
);

const MixingPhase = () => (
  <div style={{...fullFrame, gap: 26, justifyContent: "center"}}>
    <div style={{display: "flex", justifyContent: "space-between"}}>
      <Kicker>Mixing your answer</Kicker>
      <span style={{color: COLORS.signal, fontSize: 23}}>■■■■■□□□□□</span>
    </div>
    <AsciiMartini revealAt={0} />
    <div style={{fontSize: 22, letterSpacing: "0.04em", textAlign: "center"}}>
      MIX / STIR / VALIDATE / GARNISH
    </div>
  </div>
);

const IngredientRow = ({amount, name}: {amount: string; name: string}) => (
  <div
    style={{
      borderTop: `1px solid ${COLORS.outline}`,
      display: "grid",
      fontSize: 26,
      gridTemplateColumns: "170px 1fr",
      lineHeight: 1.2,
      padding: "16px 0",
    }}
  >
    <span style={{fontVariantNumeric: "tabular-nums"}}>{amount}</span>
    <span>{name}</span>
  </div>
);

const RecipePhase = () => (
  <div style={{...fullFrame, justifyContent: "center"}}>
    <Reveal delay={0} distance={70} duration={25}>
      <article style={{border: `2px solid ${COLORS.outline}`}}>
        <header style={{borderBottom: `1px solid ${COLORS.outline}`, padding: "26px 30px 30px"}}>
          <Kicker>House recipe / schema valid</Kicker>
          <div
            style={{
              fontSize: 56,
              letterSpacing: "-0.065em",
              lineHeight: 0.96,
              marginTop: 18,
            }}
          >
            COMPOUNDING
            <br />
            SNOWBALL SWIZZLE
          </div>
        </header>

        <div style={{display: "grid", gridTemplateColumns: "0.92fr 1.08fr"}}>
          <section
            style={{
              borderRight: `1px solid ${COLORS.outline}`,
              padding: "24px 28px 22px",
            }}
          >
            <div style={{fontSize: 21, marginBottom: 18, textTransform: "uppercase"}}>
              Ingredients / 04
            </div>
            <IngredientRow amount="50 ml" name="starting principal" />
            <IngredientRow amount="25 ml" name="new interest" />
            <IngredientRow amount="15 ml" name="reinvested interest" />
          </section>

          <section style={{padding: "24px 28px 22px"}}>
            <div style={{fontSize: 21, textTransform: "uppercase"}}>Method / 01</div>
            <div
              style={{
                color: COLORS.signal,
                fontSize: 63,
                letterSpacing: "-0.07em",
                lineHeight: 1,
                marginTop: 48,
              }}
            >
              100 → 110 → 121
            </div>
            <div style={{fontSize: 27, lineHeight: 1.3, marginTop: 30}}>
              Interest earns interest.
              <br />
              That is the whole trick.
            </div>
          </section>
        </div>

        <footer
          style={{
            backgroundColor: COLORS.signal,
            color: COLORS.concrete,
            fontSize: 24,
            lineHeight: 1.3,
            padding: "20px 28px",
          }}
        >
          GARNISH / A WIDENING SPIRAL OF CITRUS ZEST.
        </footer>
      </article>
    </Reveal>
  </div>
);

export const SpiritGuideScene = () => {
  const frame = useCurrentFrame();

  return (
    <SceneShell chapter="Spirit Guide" index="03" label="Useful answers / cocktail structure">
      <div style={{flex: 1, position: "relative"}}>
        <AbsoluteFill
          style={{
            opacity: interpolate(frame, [0, 8, 83, 94], [0, 1, 1, 0], clamp),
            translate: `0 ${interpolate(frame, [84, 96], [0, -42], {
              ...clamp,
              easing: CRISP_EASE,
            })}px`,
          }}
        >
          <PromptPhase />
        </AbsoluteFill>

        <AbsoluteFill
          style={{
            opacity: interpolate(frame, [91, 101, 145, 156], [0, 1, 1, 0], clamp),
          }}
        >
          <MixingPhase />
        </AbsoluteFill>

        <AbsoluteFill
          style={{
            opacity: interpolate(frame, [151, 162], [0, 1], {
              ...clamp,
              easing: CRISP_EASE,
            }),
          }}
        >
          <RecipePhase />
        </AbsoluteFill>
      </div>
    </SceneShell>
  );
};

type SystemCardProps = {
  active?: boolean;
  code: string;
  model: string;
  prompt: string;
};

const SystemCard = ({active = false, code, model, prompt}: SystemCardProps) => (
  <div
    style={{
      backgroundColor: active ? COLORS.steel : "rgba(240,238,233,0.78)",
      border: `2px solid ${active ? COLORS.signal : COLORS.outline}`,
      color: active ? COLORS.concrete : COLORS.steel,
      display: "flex",
      flexDirection: "column",
      minHeight: 226,
      padding: "24px 26px",
    }}
  >
    <div style={{display: "flex", justifyContent: "space-between"}}>
      <span style={{color: active ? COLORS.signal : COLORS.muted, fontSize: 24}}>{code}</span>
      {active ? <span style={{color: COLORS.signal, fontSize: 18}}>PRIMARY</span> : null}
    </div>
    <div style={{fontSize: 36, letterSpacing: "-0.045em", lineHeight: 1, marginTop: "auto"}}>
      {model}
    </div>
    <div style={{fontSize: 23, lineHeight: 1.25, marginTop: 16}}>{prompt}</div>
  </div>
);

export const ExperimentScene = () => (
  <SceneShell chapter="The experiment" index="04" label="Same model / four systems / fair comparison">
    <div style={{...fullFrame, justifyContent: "center"}}>
      <Reveal delay={2} distance={52}>
        <Kicker>The real question</Kicker>
        <div
          style={{
            fontSize: 76,
            letterSpacing: "-0.075em",
            lineHeight: 0.95,
            marginTop: 18,
          }}
        >
          PROMPT IT?
          <br />
          <span style={{color: COLORS.signal}}>OR FINE-TUNE IT?</span>
        </div>
      </Reveal>

      <Reveal delay={24} distance={42}>
        <div style={{fontSize: 26, lineHeight: 1.35, marginTop: 30}}>
          ONE QWEN2.5–1.5B MODEL. FOUR CONTROLLED SYSTEMS.
        </div>
      </Reveal>

      <Reveal delay={38} distance={56} duration={30}>
        <div
          style={{
            display: "grid",
            gap: 12,
            gridTemplateColumns: "1fr 1fr",
            marginTop: 44,
          }}
        >
          <SystemCard code="A" model="BASE MODEL" prompt="Minimal prompt" />
          <SystemCard active code="B" model="BASE MODEL" prompt="Five worked examples" />
          <SystemCard active code="C" model="LoRA ADAPTER" prompt="Minimal prompt" />
          <SystemCard code="D" model="LoRA ADAPTER" prompt="Five worked examples" />
        </div>
      </Reveal>

      <Reveal delay={72} distance={22}>
        <div
          style={{
            alignItems: "center",
            display: "flex",
            fontSize: 22,
            justifyContent: "space-between",
            marginTop: 28,
          }}
        >
          <span>PRIMARY TEST / B ↔ C</span>
          <span style={{color: COLORS.signal}}>60 UNSEEN PROMPTS / NO REPAIRS</span>
        </div>
      </Reveal>
    </div>
  </SceneShell>
);

const StatRow = ({
  delay,
  detail,
  from,
  label,
  to,
}: {
  delay: number;
  detail: string;
  from: string;
  label: string;
  to: string;
}) => (
  <Reveal delay={delay} distance={44}>
    <div style={{borderTop: `1px solid ${COLORS.outline}`, padding: "26px 0 30px"}}>
      <div
        style={{
          alignItems: "center",
          display: "grid",
          gridTemplateColumns: "1fr auto",
          marginBottom: 18,
        }}
      >
        <div style={{fontSize: 23, textTransform: "uppercase"}}>{label}</div>
        <div style={{color: COLORS.signal, fontSize: 22}}>FIVE-SHOT → LoRA</div>
      </div>
      <div style={{alignItems: "baseline", display: "flex", gap: 30}}>
        <span style={{fontSize: 74, letterSpacing: "-0.07em", lineHeight: 1}}>{from}</span>
        <span style={{color: COLORS.signal, fontSize: 46}}>→</span>
        <span style={{color: COLORS.signal, fontSize: 92, letterSpacing: "-0.08em", lineHeight: 1}}>
          {to}
        </span>
      </div>
      <div style={{fontSize: 25, lineHeight: 1.3, marginTop: 14}}>{detail}</div>
    </div>
  </Reveal>
);

const ResultPhaseA = () => (
  <SceneShell chapter="Results" index="05" label="Evidence / 60 first attempts / frozen 17 July 2026">
    <div style={{...fullFrame, justifyContent: "center"}}>
      <Reveal delay={0} distance={60}>
        <Kicker>The model learned the form</Kicker>
        <div
          style={{
            fontSize: 79,
            letterSpacing: "-0.075em",
            lineHeight: 0.95,
            margin: "18px 0 48px",
          }}
        >
          STRUCTURE UP.
          <br />
          <span style={{color: COLORS.signal}}>PROMPT DOWN.</span>
        </div>
      </Reveal>
      <StatRow
        delay={22}
        detail="Schema-valid responses / +15 percentage points"
        from="43 / 60"
        label="Structural reliability"
        to="52 / 60"
      />
      <StatRow
        delay={44}
        detail="Average recurring input tokens / 98.8% fewer"
        from="2,576"
        label="Prompt context"
        to="32"
      />
    </div>
  </SceneShell>
);

const ResultPhaseB = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: COLORS.steel,
        translate: `${interpolate(frame, [112, 127], [1080, 0], {
          ...clamp,
          easing: CRISP_EASE,
        })}px 0`,
        zIndex: 5,
      }}
    >
      <SceneShell
        chapter="Results"
        index="05"
        inverse
        label="Mixed result / honest conclusion"
      >
        <div style={{...fullFrame, justifyContent: "center"}}>
          <Reveal delay={12} distance={55}>
            <Kicker inverse>The honest bit</Kicker>
            <div
              style={{
                fontSize: 70,
                letterSpacing: "-0.07em",
                lineHeight: 0.98,
                marginTop: 20,
              }}
            >
              DID IT LEARN
              <br />
              BETTER ANSWERS?
            </div>
          </Reveal>

          <Reveal delay={30} distance={55}>
            <div
              style={{
                color: COLORS.signal,
                fontSize: 108,
                letterSpacing: "-0.085em",
                lineHeight: 0.9,
                marginTop: 34,
              }}
            >
              NOT CLEARLY.
            </div>
          </Reveal>

          <Reveal delay={48} distance={38}>
            <div
              style={{
                borderBottom: `1px solid rgba(240,238,233,0.35)`,
                borderTop: `1px solid rgba(240,238,233,0.35)`,
                marginTop: 70,
                padding: "30px 0 34px",
              }}
            >
              <div style={{fontSize: 23, textTransform: "uppercase"}}>
                Timed generation / five-shot → LoRA
              </div>
              <div style={{alignItems: "baseline", display: "flex", gap: 30, marginTop: 18}}>
                <span style={{fontSize: 73}}>3.92s</span>
                <span style={{color: COLORS.signal, fontSize: 46}}>→</span>
                <span style={{color: COLORS.signal, fontSize: 92}}>5.70s</span>
              </div>
              <div style={{fontSize: 27, lineHeight: 1.35, marginTop: 14}}>
                Shorter prompt. Slower generation.
              </div>
            </div>
          </Reveal>

          <Reveal delay={76} distance={24}>
            <div style={{fontSize: 30, lineHeight: 1.35, marginTop: 46}}>
              AI declined to be a tidy case study<span style={{color: COLORS.signal}}>.</span>
            </div>
          </Reveal>
        </div>
      </SceneShell>
    </AbsoluteFill>
  );
};

export const ResultsScene = () => {
  return (
    <AbsoluteFill>
      <ResultPhaseA />
      <ResultPhaseB />
    </AbsoluteFill>
  );
};

const TastingCard = ({
  active,
  answer,
  children,
  revealed,
  title,
}: {
  active: boolean;
  answer: string;
  children: ReactNode;
  revealed: string | null;
  title: string;
}) => (
  <div
    style={{
      backgroundColor: active ? COLORS.steel : "rgba(240,238,233,0.8)",
      border: `2px solid ${active ? COLORS.signal : COLORS.outline}`,
      color: active ? COLORS.concrete : COLORS.steel,
      display: "grid",
      gridTemplateColumns: "210px 1fr",
      minHeight: 230,
    }}
  >
    <div
      style={{
        borderRight: `1px solid ${active ? "rgba(240,238,233,0.35)" : COLORS.outline}`,
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
        padding: "24px",
      }}
    >
      <span style={{color: active ? COLORS.signal : COLORS.muted, fontSize: 22}}>{answer}</span>
      {revealed ? (
        <span style={{color: COLORS.signal, fontSize: 18, lineHeight: 1.3}}>{revealed}</span>
      ) : (
        <span style={{fontSize: 18}}>CONCEALED</span>
      )}
    </div>
    <div style={{display: "flex", flexDirection: "column", padding: "24px 28px"}}>
      <div style={{fontSize: 37, letterSpacing: "-0.045em", lineHeight: 1.05}}>{title}</div>
      <div style={{fontSize: 23, lineHeight: 1.35, marginTop: "auto"}}>{children}</div>
    </div>
  </div>
);

export const TastingRoomScene = () => {
  const frame = useCurrentFrame();
  const activeAnswer = frame < 77 ? 1 : 2;
  const revealed = frame >= 111;

  return (
    <SceneShell chapter="Tasting Room" index="06" label="Taste both / choose / reveal">
      <div style={{...fullFrame, justifyContent: "center"}}>
        <Reveal delay={0} distance={55}>
          <Kicker>Two answers / one fine-tune</Kicker>
          <div
            style={{
              fontSize: 76,
              letterSpacing: "-0.075em",
              lineHeight: 0.95,
              marginTop: 18,
            }}
          >
            CAN YOU SPOT
            <br />
            <span style={{color: COLORS.signal}}>THE FINE-TUNE?</span>
          </div>
        </Reveal>

        <Reveal delay={20} distance={32}>
          <div
            style={{
              borderBottom: `1px solid ${COLORS.outline}`,
              fontSize: 23,
              lineHeight: 1.35,
              marginTop: 32,
              padding: "18px 0",
            }}
          >
            ORDER_01 / How do I choose the first chore when the whole flat feels messy?
          </div>
        </Reveal>

        <Reveal delay={35} distance={54} duration={30}>
          <div style={{display: "grid", gap: 12, marginTop: 28}}>
            <TastingCard
              active={activeAnswer === 1}
              answer="ANSWER_01"
              revealed={revealed ? "FINE-TUNED" : null}
              title="THE CLEAR-SURFACE COLLINS"
            >
              15 minutes of uninterrupted focus / one clear worktop
            </TastingCard>
            <TastingCard
              active={activeAnswer === 2}
              answer="ANSWER_02"
              revealed={revealed ? "PROMPTED" : null}
              title="THE FIRST-WIN HIGHBALL"
            >
              One useful room / one quick visible win / permission to stop
            </TastingCard>
          </div>
        </Reveal>

        <div
          style={{
            backgroundColor: revealed ? COLORS.signal : "transparent",
            border: `2px solid ${COLORS.signal}`,
            color: revealed ? COLORS.concrete : COLORS.signal,
            fontSize: 23,
            marginTop: 18,
            opacity: interpolate(frame, [70, 82], [0, 1], {
              ...clamp,
              easing: CRISP_EASE,
            }),
            padding: "18px 22px",
            textAlign: "center",
            textTransform: "uppercase",
          }}
        >
          {revealed ? "Revealed / which would you have picked?" : "Choose answer 02 →"}
        </div>
      </div>
    </SceneShell>
  );
};

const NavRow = ({delay, text}: {delay: number; text: string}) => (
  <Reveal delay={delay} distance={36} duration={22}>
    <div
      style={{
        alignItems: "center",
        borderTop: `1px solid ${COLORS.outline}`,
        display: "flex",
        fontSize: 26,
        justifyContent: "space-between",
        padding: "17px 0",
        textTransform: "uppercase",
      }}
    >
      <span>{text}</span>
      <span style={{color: COLORS.signal}}>↗</span>
    </div>
  </Reveal>
);

export const FinalScene = ({url}: {url: string}) => {
  const frame = useCurrentFrame();

  return (
    <SceneShell chapter="Last orders" index="07" label="A LoRA experiment by Will Etheridge">
      <div style={{...fullFrame, justifyContent: "center"}}>
        <Reveal delay={0} distance={65}>
          <div
            style={{
              overflow: "hidden",
              width: `${interpolate(frame, [2, 30], [0, 100], {
                ...clamp,
                easing: CRISP_EASE,
              })}%`,
            }}
          >
            <div style={{width: 760}}>
              <Wordmark size={162} />
            </div>
          </div>
        </Reveal>

        <Reveal delay={20} distance={44}>
          <div
            style={{
              fontSize: 70,
              letterSpacing: "-0.07em",
              lineHeight: 0.98,
              marginTop: 28,
            }}
          >
            USEFUL ANSWERS,
            <br />
            <span style={{color: COLORS.signal}}>MIXED DIFFERENTLY.</span>
          </div>
        </Reveal>

        <div style={{marginTop: 58}}>
          <NavRow delay={40} text="Try the Spirit Guide" />
          <NavRow delay={49} text="Enter the Tasting Room" />
          <NavRow delay={58} text="Read the experiment + results" />
        </div>

        <Reveal delay={68} distance={24}>
          <Rule />
          <div
            style={{
              display: "flex",
              fontSize: 27,
              justifyContent: "space-between",
              marginTop: 22,
            }}
          >
            <span>{url}</span>
            <span style={{color: COLORS.signal}}>MIX IT →</span>
          </div>
        </Reveal>
      </div>
    </SceneShell>
  );
};
