import {Audio} from "@remotion/media";
import {Composition, Sequence, staticFile} from "remotion";
import {
  BrandScene,
  ExperimentScene,
  FinalScene,
  HookScene,
  ResultsScene,
  SpiritGuideScene,
  TastingRoomScene,
} from "./scenes";
import {ChatGntTeaser, TEASER_VIDEO} from "./Teaser";

export const VIDEO = {
  durationInFrames: 1260,
  fps: 30,
  height: 1350,
  width: 1080,
} as const;

const SCENES = {
  brand: {duration: 108, from: 126},
  experiment: {duration: 186, from: 510},
  final: {duration: 150, from: 1110},
  hook: {duration: 126, from: 0},
  results: {duration: 246, from: 696},
  spirit: {duration: 276, from: 234},
  tasting: {duration: 168, from: 942},
} as const;

export type ChatGntPromoProps = {
  url: string;
};

const Soundtrack = () => {
  const impactFrames = [0, 126, 234, 394, 510, 696, 808, 942, 1110];

  return (
    <>
      <Audio
        src={staticFile("audio/bed.wav")}
        volume={(frame) => {
          if (frame < 24) return (frame / 24) * 0.72;
          if (frame > VIDEO.durationInFrames - 60) {
            return ((VIDEO.durationInFrames - frame) / 60) * 0.72;
          }
          return 0.72;
        }}
      />

      {impactFrames.map((from) => (
        <Sequence from={from} key={`impact-${from}`} layout="none">
          <Audio
            src={staticFile("audio/impact.wav")}
            volume={() => (from === 0 ? 0.34 : 0.26)}
          />
        </Sequence>
      ))}

      <Sequence from={252} layout="none">
        <Audio src={staticFile("audio/typing.wav")} volume={() => 0.24} />
      </Sequence>
      <Sequence from={325} layout="none">
        <Audio src={staticFile("audio/shaker.wav")} volume={() => 0.62} />
      </Sequence>
      <Sequence from={394} layout="none">
        <Audio src={staticFile("audio/ding.wav")} volume={() => 0.34} />
      </Sequence>
      <Sequence from={1018} layout="none">
        <Audio src={staticFile("audio/switch.wav")} volume={() => 0.25} />
      </Sequence>
      <Sequence from={1053} layout="none">
        <Audio
          src={staticFile("audio/ding.wav")}
          toneFrequency={0.86}
          volume={() => 0.26}
        />
      </Sequence>
    </>
  );
};

export const ChatGntPromo = ({url}: ChatGntPromoProps) => (
  <>
    <Sequence
      durationInFrames={SCENES.hook.duration}
      from={SCENES.hook.from}
      name="01 — Opening line"
      premountFor={30}
    >
      <HookScene />
    </Sequence>
    <Sequence
      durationInFrames={SCENES.brand.duration}
      from={SCENES.brand.from}
      name="02 — Brand reveal"
      premountFor={30}
    >
      <BrandScene />
    </Sequence>
    <Sequence
      durationInFrames={SCENES.spirit.duration}
      from={SCENES.spirit.from}
      name="03 — Spirit Guide"
      premountFor={30}
    >
      <SpiritGuideScene />
    </Sequence>
    <Sequence
      durationInFrames={SCENES.experiment.duration}
      from={SCENES.experiment.from}
      name="04 — Experiment"
      premountFor={30}
    >
      <ExperimentScene />
    </Sequence>
    <Sequence
      durationInFrames={SCENES.results.duration}
      from={SCENES.results.from}
      name="05 — Results"
      premountFor={30}
    >
      <ResultsScene />
    </Sequence>
    <Sequence
      durationInFrames={SCENES.tasting.duration}
      from={SCENES.tasting.from}
      name="06 — Tasting Room"
      premountFor={30}
    >
      <TastingRoomScene />
    </Sequence>
    <Sequence
      durationInFrames={SCENES.final.duration}
      from={SCENES.final.from}
      name="07 — Last orders"
      premountFor={30}
    >
      <FinalScene url={url} />
    </Sequence>
    <Soundtrack />
  </>
);

export const MyComposition = () => (
  <>
    <Composition
      component={ChatGntTeaser}
      defaultProps={{url: "github.com/WillEtheridge/chatgandt", withAudio: true}}
      durationInFrames={TEASER_VIDEO.durationInFrames}
      fps={TEASER_VIDEO.fps}
      height={TEASER_VIDEO.height}
      id="ChatGntTeaser"
      width={TEASER_VIDEO.width}
    />
    <Composition
      component={ChatGntTeaser}
      defaultProps={{url: "github.com/WillEtheridge/chatgandt", withAudio: false}}
      durationInFrames={TEASER_VIDEO.durationInFrames}
      fps={TEASER_VIDEO.fps}
      height={TEASER_VIDEO.height}
      id="ChatGntTeaserSilent"
      width={TEASER_VIDEO.width}
    />
    <Composition
      component={ChatGntPromo}
      defaultProps={{url: "github.com/WillEtheridge/chatgandt"}}
      durationInFrames={VIDEO.durationInFrames}
      fps={VIDEO.fps}
      height={VIDEO.height}
      id="ChatGntPromo"
      width={VIDEO.width}
    />
  </>
);
