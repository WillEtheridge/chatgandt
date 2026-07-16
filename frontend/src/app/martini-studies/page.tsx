import Link from "next/link";

const WIDTH = 127;
const HEIGHT = 50;
const CENTER = Math.floor(WIDTH / 2);

type GlassProfile = {
  bowlTop: number;
  bowlBottom: number;
  bowlWidth: number;
  stemBottom: number;
  baseWidth: number;
};

type FieldStyle = "block" | "contour" | "bands" | "echo" | "dissolve";

const PROFILES: Record<string, GlassProfile> = {
  balanced: { bowlTop: 6, bowlBottom: 21, bowlWidth: 30, stemBottom: 39, baseWidth: 14 },
  shallow: { bowlTop: 9, bowlBottom: 21, bowlWidth: 34, stemBottom: 39, baseWidth: 15 },
  deep: { bowlTop: 5, bowlBottom: 23, bowlWidth: 28, stemBottom: 41, baseWidth: 13 },
  longStem: { bowlTop: 7, bowlBottom: 21, bowlWidth: 30, stemBottom: 44, baseWidth: 14 },
  compact: { bowlTop: 8, bowlBottom: 23, bowlWidth: 29, stemBottom: 37, baseWidth: 13 },
};

function hash(x: number, y: number) {
  return (x * 37 + y * 71 + x * y * 3) % 101;
}

function inGlass(x: number, y: number, profile: GlassProfile, expansion = 0) {
  const centre = CENTER;

  if (y >= profile.bowlTop && y <= profile.bowlBottom) {
    const progress = (y - profile.bowlTop) / (profile.bowlBottom - profile.bowlTop);
    const halfWidth = Math.max(1, Math.round(profile.bowlWidth * (1 - progress)) + expansion);
    return Math.abs(x - centre) <= halfWidth;
  }

  if (y > profile.bowlBottom && y <= profile.stemBottom) {
    return Math.abs(x - centre) <= expansion;
  }

  if (y === profile.stemBottom + 1) {
    return Math.abs(x - centre) <= profile.baseWidth + expansion;
  }

  return false;
}

function inField(x: number, y: number, style: FieldStyle, profile: GlassProfile) {
  if (style === "block") return true;

  if (style === "contour") {
    const edge = 3 + Math.abs(((y * 7) % 17) - 8);
    if (x < edge || x >= WIDTH - edge) return false;
    return x > edge + 5 && x < WIDTH - edge - 5 ? true : hash(x, y) > 24;
  }

  if (style === "bands") {
    if (y === 3 || y === 28 || y === 42) return false;
    return !(y < 6 && hash(x, y) < 18);
  }

  if (style === "echo") {
    if (inGlass(x - 3, y, profile, 1) && !inGlass(x, y, profile)) {
      return hash(x, y) > 62;
    }
    return true;
  }

  if (inGlass(x, y, profile, 5) && !inGlass(x, y, profile)) {
    return hash(x, y) > 48;
  }

  const edge = Math.min(x, WIDTH - x - 1, y, HEIGHT - y - 1);
  return edge > 3 || hash(x, y) > (4 - edge) * 18;
}

function negativeGlass(profile: GlassProfile, vocabulary: string, fieldStyle: FieldStyle) {
  return Array.from({ length: HEIGHT }, (_, y) =>
    Array.from({ length: WIDTH }, (_, x) => {
      if (inGlass(x, y, profile) || !inField(x, y, fieldStyle, profile)) return " ";
      return vocabulary[(x + y * (WIDTH + 7)) % vocabulary.length];
    }).join(""),
  ).join("\n");
}

const STUDIES = [
  {
    number: "01",
    title: "Balanced",
    note: "A narrower bowl, a fine stem, and a base held to half the rim.",
    colour: "bg-steel text-signal",
    value: negativeGlass(PROFILES.balanced, "MIX.STIR.POUR.TASTE.REVISE.REPEAT.", "block"),
  },
  {
    number: "02",
    title: "Shallow",
    note: "A wider rim and lower bowl sit above a longer run of stem.",
    colour: "bg-steel text-signal",
    value: negativeGlass(PROFILES.shallow, "PROMPT.GUESS.COMPARE.REVEAL.REVISE.", "contour"),
  },
  {
    number: "03",
    title: "Deep",
    note: "A tighter rim falls through a deeper bowl before meeting the stem.",
    colour: "bg-steel text-signal",
    value: negativeGlass(PROFILES.deep, "050ML.025ML.015ML.002DSH.STIR.30SEC.", "bands"),
  },
  {
    number: "04",
    title: "Long stem",
    note: "The balanced bowl is lifted higher to make the silhouette more severe.",
    colour: "bg-steel text-signal",
    value: negativeGlass(PROFILES.longStem, "FREE.POUR.FREE.POUR.FREE.POUR.REPEAT.", "echo"),
  },
  {
    number: "05",
    title: "Compact",
    note: "A shorter stem and close-set base compress the same essential geometry.",
    colour: "bg-steel text-signal",
    value: negativeGlass(PROFILES.compact, ".,:;/MIX/STIR/STRAIN/POUR/REVISE/", "dissolve"),
  },
] as const;

export default function MartiniStudiesPage() {
  return (
    <main className="bg-steel text-concrete">
      <header className="flex min-h-16 items-center justify-between gap-6 border-b border-concrete px-4 text-xs uppercase sm:px-6">
        <Link className="underline decoration-1 underline-offset-4" href="/typography">
          ← Type / Colour
        </Link>
        <div className="flex items-center gap-6">
          <span>Martini studies / 01–05</span>
          <Link className="underline decoration-1 underline-offset-4" href="/martini-loader">
            Loader →
          </Link>
        </div>
      </header>

      {STUDIES.map((study) => (
        <Study key={study.number} {...study} />
      ))}
    </main>
  );
}

function Study({
  number,
  title,
  note,
  colour,
  value,
}: Readonly<{
  number: string;
  title: string;
  note: string;
  colour: string;
  value: string;
}>) {
  return (
    <section id={`study-${number}`} className={`min-h-screen border-b border-current ${colour}`}>
      <div className="grid border-b border-current sm:grid-cols-2">
        <div className="flex justify-between px-4 py-6 text-xs uppercase sm:border-r sm:px-6">
          <span>{title}</span>
          <span>{number} / 05</span>
        </div>
        <p className="border-t border-current px-4 py-6 text-sm leading-relaxed sm:border-t-0 sm:px-6">{note}</p>
      </div>
      <div className="flex min-h-screen items-center justify-center overflow-hidden px-4 py-20 sm:px-6">
        <pre
          id={`art-${number}`}
          aria-label={`${title} martini glass formed from negative space`}
          className="max-w-full overflow-x-auto text-xs leading-none"
          role="img"
        >
          {value}
        </pre>
      </div>
    </section>
  );
}
