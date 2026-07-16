import { mkdtempSync, mkdirSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { dirname, join, resolve } from "node:path";
import { spawnSync } from "node:child_process";
import { fileURLToPath } from "node:url";

const WIDTH = 127;
const HEIGHT = 50;
const CENTER = Math.floor(WIDTH / 2);
const PROFILE = {
  bowlTop: 6,
  bowlBottom: 21,
  bowlWidth: 30,
  stemBottom: 39,
  baseWidth: 14,
};
const VOCABULARY = "MIX.STIR.POUR.TASTE.REVISE.REPEAT.";

const CANVAS_WIDTH = 1024;
const CANVAS_HEIGHT = 640;
const TEXT_X = 49;
const TEXT_Y = 20;
const LINE_HEIGHT = 12;
const FRAME_DELAY = 4;
const HOLD_DELAY = 70;

const STEEL = "#020D13";
const SIGNAL = "#CD533B";

const scriptDirectory = dirname(fileURLToPath(import.meta.url));
const frontendDirectory = resolve(scriptDirectory, "..");
const fontPath = join(frontendDirectory, "src/app/fonts/PPNeueMontrealMono-Book.woff2");
const outputDirectory = join(frontendDirectory, "public");
const outputPath = join(outputDirectory, "martini-loader.gif");
const frameDirectory = mkdtempSync(join(tmpdir(), "martini-loader-"));

function inGlass(x, y) {
  if (y >= PROFILE.bowlTop && y <= PROFILE.bowlBottom) {
    const progress = (y - PROFILE.bowlTop) / (PROFILE.bowlBottom - PROFILE.bowlTop);
    const halfWidth = Math.max(1, Math.round(PROFILE.bowlWidth * (1 - progress)));
    return Math.abs(x - CENTER) <= halfWidth;
  }

  if (y > PROFILE.bowlBottom && y <= PROFILE.stemBottom) {
    return x === CENTER;
  }

  if (y === PROFILE.stemBottom + 1) {
    return Math.abs(x - CENTER) <= PROFILE.baseWidth;
  }

  return false;
}

const rows = Array.from({ length: HEIGHT }, (_, y) =>
  Array.from({ length: WIDTH }, (_, x) => {
    if (inGlass(x, y)) return " ";
    return VOCABULARY[(x + y * (WIDTH + 7)) % VOCABULARY.length];
  }).join(""),
);

function runMagick(arguments_) {
  const result = spawnSync("magick", arguments_, { encoding: "utf8" });

  if (result.status !== 0) {
    throw new Error(result.stderr || "ImageMagick failed to render the loader.");
  }
}

try {
  mkdirSync(outputDirectory, { recursive: true });

  const masterPath = join(frameDirectory, "master.png");
  runMagick([
    "-size",
    `${CANVAS_WIDTH}x${CANVAS_HEIGHT}`,
    `xc:${STEEL}`,
    "-fill",
    SIGNAL,
    "-font",
    fontPath,
    "-pointsize",
    "12",
    "-interline-spacing",
    "-4",
    "-gravity",
    "northwest",
    "-annotate",
    `+${TEXT_X}+${TEXT_Y}`,
    rows.join("\n"),
    masterPath,
  ]);

  const frames = Array.from({ length: HEIGHT + 1 }, (_, visibleLineCount) => {
    const framePath = join(frameDirectory, `frame-${String(visibleLineCount).padStart(3, "0")}.png`);
    const firstVisibleLine = HEIGHT - visibleLineCount;

    if (visibleLineCount === 0) {
      runMagick(["-size", `${CANVAS_WIDTH}x${CANVAS_HEIGHT}`, `xc:${STEEL}`, framePath]);
    } else {
      const coverBottom = TEXT_Y + firstVisibleLine * LINE_HEIGHT - 1;
      const arguments_ = [masterPath];

      if (coverBottom >= 0) {
        arguments_.push("-fill", STEEL, "-draw", `rectangle 0,0 ${CANVAS_WIDTH},${coverBottom}`);
      }

      arguments_.push(framePath);
      runMagick(arguments_);
    }

    return framePath;
  });

  runMagick([
    "-delay",
    String(FRAME_DELAY),
    ...frames,
    "-delay",
    String(HOLD_DELAY),
    frames.at(-1),
    "-loop",
    "0",
    "-colors",
    "64",
    "-layers",
    "Optimize",
    outputPath,
  ]);

  process.stdout.write(`Rendered ${outputPath}\n`);
} finally {
  rmSync(frameDirectory, { recursive: true, force: true });
}
