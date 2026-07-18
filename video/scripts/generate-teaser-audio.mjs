import {mkdirSync, writeFileSync} from "node:fs";
import {dirname, resolve} from "node:path";
import {fileURLToPath} from "node:url";

const SAMPLE_RATE = 48_000;
const DURATION = 20;
const SAMPLE_COUNT = SAMPLE_RATE * DURATION;
const TAU = Math.PI * 2;

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const outputDirectory = resolve(scriptDirectory, "../public/audio");

mkdirSync(outputDirectory, {recursive: true});

const noise = new Float32Array(SAMPLE_COUNT + 20_000);
let randomState = 0x5eed1234;

for (let index = 0; index < noise.length; index++) {
  randomState = (Math.imul(randomState, 1_664_525) + 1_013_904_223) >>> 0;
  noise[index] = (randomState / 0xffffffff) * 2 - 1;
}

const createStereoBuffer = () => ({
  left: new Float32Array(SAMPLE_COUNT),
  right: new Float32Array(SAMPLE_COUNT),
});

const beat = createStereoBuffer();
const effects = createStereoBuffer();

const panGains = (pan) => {
  const angle = ((Math.max(-1, Math.min(1, pan)) + 1) * Math.PI) / 4;
  return {left: Math.cos(angle), right: Math.sin(angle)};
};

const addSignal = (buffer, start, duration, generator, gain = 1, pan = 0) => {
  const firstSample = Math.max(0, Math.round(start * SAMPLE_RATE));
  const numberOfSamples = Math.min(
    Math.round(duration * SAMPLE_RATE),
    SAMPLE_COUNT - firstSample,
  );
  const stereo = panGains(pan);

  for (let localSample = 0; localSample < numberOfSamples; localSample++) {
    const absoluteSample = firstSample + localSample;
    const time = localSample / SAMPLE_RATE;
    const value = generator(time, localSample, absoluteSample) * gain;
    buffer.left[absoluteSample] += value * stereo.left;
    buffer.right[absoluteSample] += value * stereo.right;
  }
};

const addKick = (buffer, time, gain = 1, pan = 0) => {
  let phase = 0;
  addSignal(
    buffer,
    time,
    0.52,
    (localTime, _localSample, absoluteSample) => {
      const frequency = 47 + 118 * Math.exp(-localTime * 29);
      phase += (TAU * frequency) / SAMPLE_RATE;
      const body = Math.sin(phase) * Math.exp(-localTime * 8.2);
      const knock = Math.sin(TAU * 93 * localTime) * Math.exp(-localTime * 25) * 0.25;
      const click = noise[absoluteSample + 71] * Math.exp(-localTime * 92) * 0.22;
      return body + knock + click;
    },
    gain,
    pan,
  );
};

const addSnare = (buffer, time, gain = 1, pan = 0) => {
  let previousNoise = 0;
  addSignal(
    buffer,
    time,
    0.34,
    (localTime, _localSample, absoluteSample) => {
      const rawNoise = noise[absoluteSample + 4_913];
      const highNoise = rawNoise - previousNoise * 0.82;
      previousNoise = rawNoise;
      const clapEnvelope =
        Math.exp(-localTime * 14) +
        (localTime > 0.014 ? Math.exp(-(localTime - 0.014) * 26) * 0.35 : 0) +
        (localTime > 0.029 ? Math.exp(-(localTime - 0.029) * 31) * 0.22 : 0);
      const body = Math.sin(TAU * 184 * localTime) * Math.exp(-localTime * 20) * 0.34;
      return highNoise * clapEnvelope * 0.7 + body;
    },
    gain,
    pan,
  );
};

const addHat = (buffer, time, gain = 1, pan = 0, open = false) => {
  let previousNoise = 0;
  addSignal(
    buffer,
    time,
    open ? 0.32 : 0.095,
    (localTime, _localSample, absoluteSample) => {
      const rawNoise = noise[absoluteSample + 9_271];
      const highNoise = rawNoise - previousNoise;
      previousNoise = rawNoise;
      const decay = open ? 13 : 55;
      return highNoise * Math.exp(-localTime * decay);
    },
    gain,
    pan,
  );
};

const addBass = (buffer, time, frequency, duration, gain = 1) => {
  let phase = 0;
  addSignal(
    buffer,
    time,
    duration,
    (localTime) => {
      const attack = Math.min(1, localTime / 0.018);
      const releaseStart = Math.max(0, duration - 0.13);
      const release =
        localTime < releaseStart
          ? 1
          : Math.max(0, 1 - (localTime - releaseStart) / (duration - releaseStart));
      const glide = frequency * (1 + 0.035 * Math.exp(-localTime * 18));
      phase += (TAU * glide) / SAMPLE_RATE;
      const wave =
        Math.sin(phase) * 0.76 +
        Math.sin(phase * 2) * 0.18 +
        Math.sin(phase * 3) * 0.06;
      return Math.tanh(wave * 1.35) * attack * release;
    },
    gain,
  );
};

const addPluck = (buffer, time, frequency, gain = 1, pan = 0) => {
  let phase = 0;
  addSignal(
    buffer,
    time,
    0.48,
    (localTime) => {
      phase += (TAU * frequency) / SAMPLE_RATE;
      const attack = Math.min(1, localTime / 0.006);
      const envelope = attack * Math.exp(-localTime * 7.5);
      const wave =
        Math.sin(phase) * 0.64 +
        Math.sin(phase * 2) * 0.2 +
        Math.sin(phase * 3) * 0.1 +
        Math.sin(phase * 5) * 0.06;
      return wave * envelope;
    },
    gain,
    pan,
  );
};

const addPad = (buffer, time, frequencies, duration, gain = 1) => {
  frequencies.forEach((frequency, noteIndex) => {
    let phase = noteIndex * 0.63;
    addSignal(
      buffer,
      time,
      duration,
      (localTime) => {
        phase += (TAU * frequency) / SAMPLE_RATE;
        const attack = Math.min(1, localTime / 0.16);
        const release = Math.min(1, Math.max(0, (duration - localTime) / 0.38));
        const shimmer = 0.82 + Math.sin(TAU * (0.22 + noteIndex * 0.07) * localTime) * 0.18;
        return (
          (Math.sin(phase) * 0.75 + Math.sin(phase * 2.003) * 0.25) *
          attack *
          release *
          shimmer
        );
      },
      gain / Math.sqrt(frequencies.length),
      -0.55 + (noteIndex / Math.max(1, frequencies.length - 1)) * 1.1,
    );
  });
};

const sectionGain = (time) => {
  if (time < 2.6) return 0.28;
  if (time < 4.2) return 1;
  if (time < 5.6) return 0.58;
  if (time < 11.2) return 0.92;
  if (time < 13.6) return 0.82;
  if (time < 17.2) return 0.88;
  if (time < 19.25) return 1.08;
  return 0.35;
};

// Sparse cold-open pulse under the three-part joke.
[0, 0.8, 1.6, 2.4].forEach((time, index) => {
  addKick(beat, time, 0.34 + index * 0.035);
  addBass(beat, time, 36.71, 0.5, 0.12);
});

for (let time = 0.2, index = 0; time < 2.6; time += 0.4, index++) {
  addHat(beat, time, 0.09, index % 2 === 0 ? -0.35 : 0.35);
}

// 150 BPM, half-time electro groove. Each 1.6-second bar is harmonically voiced in D minor.
const barLength = 1.6;
const drop = 2.6;
const bassNotes = [73.42, 65.41, 58.27, 55];
const pluckNotes = [293.66, 261.63, 233.08, 220];

for (let barStart = drop, barIndex = 0; barStart < 19.3; barStart += barLength, barIndex++) {
  const root = bassNotes[barIndex % bassNotes.length];
  const top = pluckNotes[barIndex % pluckNotes.length];
  const gain = sectionGain(barStart);

  addKick(beat, barStart, 0.82 * gain);
  addSnare(beat, barStart + 0.4, 0.54 * gain, 0.08);
  addKick(beat, barStart + 0.8, 0.72 * gain);
  addKick(beat, barStart + 1.0, 0.42 * gain, -0.08);
  addSnare(beat, barStart + 1.2, 0.58 * gain, -0.05);

  addBass(beat, barStart, root, 0.55, 0.42 * gain);
  addBass(beat, barStart + 0.8, root, 0.38, 0.36 * gain);
  addBass(beat, barStart + 1.0, root * 1.5, 0.3, 0.26 * gain);

  for (let eighth = 0; eighth < 8; eighth++) {
    const hatTime = barStart + eighth * 0.2;
    const open = eighth === 5;
    addHat(
      beat,
      hatTime,
      (open ? 0.17 : eighth % 2 === 0 ? 0.13 : 0.1) * gain,
      eighth % 2 === 0 ? -0.48 : 0.48,
      open,
    );
  }

  [0.2, 0.6, 1.0, 1.4].forEach((offset, noteIndex) => {
    const intervals = [1, 1.5, 1.2, 2];
    addPluck(
      beat,
      barStart + offset,
      top * intervals[noteIndex],
      0.12 * gain,
      noteIndex % 2 === 0 ? -0.42 : 0.42,
    );
  });
}

addPad(beat, 4.2, [146.83, 174.61, 220, 293.66], 1.45, 0.12);
addPad(beat, 13.6, [73.42, 87.31, 110], 1.2, 0.1);
addPad(beat, 17.2, [146.83, 174.61, 220, 293.66], 2.75, 0.21);

const addImpact = (buffer, time, gain = 1, pan = 0, pitch = 1) => {
  let phase = 0;
  let previousNoise = 0;
  addSignal(
    buffer,
    time,
    0.72,
    (localTime, _localSample, absoluteSample) => {
      const frequency = (39 + 92 * Math.exp(-localTime * 19)) * pitch;
      phase += (TAU * frequency) / SAMPLE_RATE;
      const sub = Math.sin(phase) * Math.exp(-localTime * 5.8);
      const rawNoise = noise[absoluteSample + 12_101];
      const crack = (rawNoise - previousNoise) * Math.exp(-localTime * 42);
      previousNoise = rawNoise;
      return sub * 0.9 + crack * 0.28;
    },
    gain,
    pan,
  );
};

const addWhoosh = (buffer, time, duration, gain = 1, pan = 0) => {
  let lowPass = 0;
  let phase = 0;
  addSignal(
    buffer,
    time,
    duration,
    (localTime, _localSample, absoluteSample) => {
      const progress = localTime / duration;
      const rawNoise = noise[absoluteSample + 15_971];
      const alpha = 0.025 + progress * 0.34;
      lowPass += alpha * (rawNoise - lowPass);
      const highNoise = rawNoise - lowPass;
      const frequency = 190 + progress * progress * 1_900;
      phase += (TAU * frequency) / SAMPLE_RATE;
      const envelope = Math.pow(progress, 1.7) * Math.pow(1 - progress, 0.2);
      return (highNoise * 0.72 + Math.sin(phase) * 0.16) * envelope;
    },
    gain,
    pan,
  );
};

const addClick = (buffer, time, gain = 1, pan = 0, frequency = 1_450) => {
  addSignal(
    buffer,
    time,
    0.09,
    (localTime) => {
      const primary = Math.sin(TAU * frequency * localTime);
      const overtone = Math.sin(TAU * frequency * 2.37 * localTime) * 0.3;
      return (primary + overtone) * Math.exp(-localTime * 58);
    },
    gain,
    pan,
  );
};

const addGlassPing = (buffer, time, gain = 1, pan = 0) => {
  addSignal(
    buffer,
    time,
    0.9,
    (localTime) => {
      const envelope = Math.exp(-localTime * 5.3);
      return (
        Math.sin(TAU * 1_760 * localTime) * 0.55 +
        Math.sin(TAU * 2_417 * localTime) * 0.3 +
        Math.sin(TAU * 3_121 * localTime) * 0.15
      ) * envelope;
    },
    gain,
    pan,
  );
};

const addGlitch = (buffer, time, gain = 1, pan = 0) => {
  addSignal(
    buffer,
    time,
    0.18,
    (localTime, localSample, absoluteSample) => {
      const gate = Math.floor(localTime / 0.018) % 2 === 0 ? 1 : 0.18;
      const stepped = Math.floor(Math.sin(TAU * (96 + localTime * 430) * localTime) * 6) / 6;
      const grit = noise[absoluteSample + 6_113] * (localSample % 7 === 0 ? 0.22 : 0.04);
      return (stepped * 0.75 + grit) * gate * Math.exp(-localTime * 6);
    },
    gain,
    pan,
  );
};

const addShakerRoll = (buffer, time, duration, gain = 1) => {
  for (let offset = 0; offset < duration; offset += 0.075) {
    const progress = offset / duration;
    addHat(
      buffer,
      time + offset,
      gain * (0.45 + progress * 0.55),
      Math.sin(offset * 37) * 0.72,
      false,
    );
  }
};

// Joke setup: three differently weighted slams.
addImpact(effects, 0, 0.62, 0, 0.86);
addWhoosh(effects, 0.47, 0.2, 0.38, 0.38);
addImpact(effects, 0.667, 0.48, 0.28, 1.08);
addWhoosh(effects, 1.2, 0.233, 0.5, -0.35);
addImpact(effects, 1.433, 0.78, 0, 0.78);
addGlassPing(effects, 1.52, 0.14, 0.55);

// Tiny tape-stop glitch into “No, really”, then the main beat drop.
addGlitch(effects, 2.44, 0.28, -0.2);
addImpact(effects, 2.6, 0.9, 0, 0.73);
addWhoosh(effects, 3.98, 0.22, 0.42, 0.2);
addImpact(effects, 4.2, 0.52, 0, 1.18);
addGlassPing(effects, 4.24, 0.32, 0.42);

// Spirit Guide UI and the extended “mixing” sequence.
addWhoosh(effects, 5.37, 0.23, 0.4, -0.22);
addImpact(effects, 5.6, 0.48, 0, 1.08);
addClick(effects, 6.55, 0.34, 0.58, 1_260);
addWhoosh(effects, 6.62, 0.18, 0.28, -0.4);
addGlitch(effects, 6.76, 0.25, -0.5);
addImpact(effects, 6.8, 0.36, 0, 1.28);
addShakerRoll(effects, 6.8, 2.6, 0.1);
addClick(effects, 7.02, 0.15, -0.62, 1_180);
addClick(effects, 7.6, 0.24, 0, 1_510);
addClick(effects, 8.12, 0.14, -0.35, 1_320);
addClick(effects, 8.533, 0.26, 0.62, 1_820);
addClick(effects, 9.02, 0.14, 0.2, 1_440);
addGlitch(effects, 9.13, 0.2, 0.3);
addWhoosh(effects, 9.18, 0.22, 0.42, 0.35);
addImpact(effects, 9.4, 0.5, 0, 1.18);
addGlassPing(effects, 9.5, 0.25, 0.3);

// Experiment setup and the prompted/fine-tuned split.
addWhoosh(effects, 10.96, 0.24, 0.5, -0.35);
addImpact(effects, 11.2, 0.64, 0, 0.9);
addGlitch(effects, 12.16, 0.22, 0.4);
addImpact(effects, 12.2, 0.36, 0.22, 1.25);

// Tasting Room: stereo choices bounce left, then right, without revealing the answer.
addWhoosh(effects, 13.36, 0.24, 0.48, 0.3);
addImpact(effects, 13.6, 0.62, 0, 1.05);
addWhoosh(effects, 14.6, 0.2, 0.24, -0.65);
addClick(effects, 14.82, 0.3, -0.72, 1_330);
addWhoosh(effects, 15.55, 0.18, 0.22, 0.7);
addClick(effects, 15.75, 0.32, 0.72, 1_610);
addClick(effects, 16.68, 0.18, 0, 1_180);

// Final call-to-action: biggest hit, resolved chord, bright button ping.
addWhoosh(effects, 16.88, 0.32, 0.66, 0);
addImpact(effects, 17.2, 1, 0, 0.68);
addGlassPing(effects, 17.46, 0.26, 0.52);
addClick(effects, 17.46, 0.18, -0.45, 1_020);
addGlassPing(effects, 18.25, 0.2, 0.4);
addGlassPing(effects, 19.08, 0.14, -0.4);

const applyFade = (buffer, start, end) => {
  const firstSample = Math.round(start * SAMPLE_RATE);
  const finalSample = Math.min(SAMPLE_COUNT, Math.round(end * SAMPLE_RATE));

  for (let index = firstSample; index < finalSample; index++) {
    const gain = 1 - (index - firstSample) / Math.max(1, finalSample - firstSample);
    buffer.left[index] *= gain;
    buffer.right[index] *= gain;
  }
};

applyFade(beat, 19.35, 20);
applyFade(effects, 19.72, 20);

const masterBuffer = (buffer, peakDb, drive) => {
  const targetPeak = 10 ** (peakDb / 20);
  let peak = 0;

  for (let index = 0; index < SAMPLE_COUNT; index++) {
    buffer.left[index] = Math.tanh(buffer.left[index] * drive) / Math.tanh(drive);
    buffer.right[index] = Math.tanh(buffer.right[index] * drive) / Math.tanh(drive);
    peak = Math.max(peak, Math.abs(buffer.left[index]), Math.abs(buffer.right[index]));
  }

  const gain = peak === 0 ? 1 : targetPeak / peak;
  for (let index = 0; index < SAMPLE_COUNT; index++) {
    buffer.left[index] *= gain;
    buffer.right[index] *= gain;
  }
};

masterBuffer(beat, -5.2, 1.16);
masterBuffer(effects, -5.5, 1.08);

const writeWave = (filePath, buffer) => {
  const channels = 2;
  const bytesPerSample = 2;
  const dataSize = SAMPLE_COUNT * channels * bytesPerSample;
  const wave = Buffer.alloc(44 + dataSize);

  wave.write("RIFF", 0);
  wave.writeUInt32LE(36 + dataSize, 4);
  wave.write("WAVE", 8);
  wave.write("fmt ", 12);
  wave.writeUInt32LE(16, 16);
  wave.writeUInt16LE(1, 20);
  wave.writeUInt16LE(channels, 22);
  wave.writeUInt32LE(SAMPLE_RATE, 24);
  wave.writeUInt32LE(SAMPLE_RATE * channels * bytesPerSample, 28);
  wave.writeUInt16LE(channels * bytesPerSample, 32);
  wave.writeUInt16LE(bytesPerSample * 8, 34);
  wave.write("data", 36);
  wave.writeUInt32LE(dataSize, 40);

  for (let index = 0; index < SAMPLE_COUNT; index++) {
    const offset = 44 + index * 4;
    const left = Math.round(Math.max(-1, Math.min(1, buffer.left[index])) * 32_767);
    const right = Math.round(Math.max(-1, Math.min(1, buffer.right[index])) * 32_767);
    wave.writeInt16LE(left, offset);
    wave.writeInt16LE(right, offset + 2);
  }

  writeFileSync(filePath, wave);
};

const beatPath = resolve(outputDirectory, "teaser-beat.wav");
const effectsPath = resolve(outputDirectory, "teaser-sfx.wav");

writeWave(beatPath, beat);
writeWave(effectsPath, effects);

console.log(`Generated ${beatPath}`);
console.log(`Generated ${effectsPath}`);
