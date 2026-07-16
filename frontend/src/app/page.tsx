import Link from "next/link";

const NAVIGATION = [
  { href: "/", label: "Spirit Guide" },
  { href: "/tasting-room", label: "Tasting Room" },
  { href: "/free-pour", label: "Free Pour" },
  { href: "/lab", label: "The Lab" },
  { href: "/results", label: "Results" },
] as const;

export default function SpiritGuidePage() {
  return (
    <main className="min-h-screen bg-concrete text-steel">
      <header className="relative border-b border-current">
        <div className="mx-auto flex min-h-16 w-full max-w-5xl items-center justify-between gap-8 px-4 sm:px-6 lg:max-w-7xl">
          <Link className="text-base" href="/">
            ChatG<span className="text-signal">&amp;</span>T
          </Link>

          <Navigation className="hidden items-center gap-6 text-xs uppercase md:flex" />

          <details className="md:hidden">
            <summary className="cursor-pointer list-none text-xs uppercase">Menu</summary>
            <Navigation className="fixed left-0 right-0 top-16 z-10 grid border-b border-current bg-concrete px-4 py-4 text-xs uppercase sm:px-6" />
          </details>
        </div>
      </header>

      <section className="mx-auto max-w-5xl px-4 pb-20 pt-12 sm:px-6 sm:pb-32 sm:pt-20 lg:max-w-7xl">
        <h1 className="max-w-5xl text-4xl leading-none tracking-tighter sm:text-7xl lg:text-8xl">
          Useful answers, <br /> <span className="text-signal">mixed differently.</span>
        </h1>
        <div className="mt-8 max-w-2xl text-base leading-relaxed sm:text-lg">
          <p>
            An experiment in teaching a small language model to answer questions as cocktail recipes.
          </p>
          <p className="mt-4">Built for low-stakes questions and fun.</p>
        </div>

        <div className="mt-16 grid gap-16 lg:grid-cols-3 lg:gap-8">
          <form className="lg:col-span-2">
            <label className="block text-xs uppercase" htmlFor="order">
              Place your order
            </label>
            <textarea
              className="mt-4 h-72 w-full resize-y border border-current bg-transparent p-4 text-base leading-relaxed outline-none placeholder:text-steel focus-visible:border-signal focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-signal sm:p-6 sm:text-lg"
              id="order"
              name="order"
              placeholder="Ask a low-stakes question…"
              required
              rows={7}
            />
            <button
              className="mt-4 flex w-full items-center justify-between bg-signal px-4 py-4 text-left text-base uppercase sm:w-64"
              type="submit"
            >
              <span>Mix it</span>
              <span aria-hidden="true">→</span>
            </button>
          </form>

          <div>
            <p className="text-xs uppercase">House Specials</p>
            <div className="mt-4 grid h-72 grid-rows-3 border border-current">
              <Suggestion>Help me prepare for a difficult conversation.</Suggestion>
              <Suggestion>Explain compound interest in plain English.</Suggestion>
              <Suggestion>Plan a focused afternoon of work.</Suggestion>
            </div>
          </div>
        </div>
      </section>

      <aside className="grid border-t border-current text-xs uppercase sm:grid-cols-2">
        <p className="border-b border-current px-4 py-6 sm:border-b-0 sm:border-r sm:px-6">Scope / 01</p>
        <p className="px-4 py-6 leading-relaxed sm:px-6">
          English-language / Single-turn / Low-stakes / No live information
        </p>
      </aside>
    </main>
  );
}

function Navigation({ className }: Readonly<{ className: string }>) {
  return (
    <nav aria-label="Main navigation" className={className}>
      {NAVIGATION.map((item) => (
        <Link
          className={item.href === "/" ? "border-b border-current py-3 md:py-0" : "border-b border-current py-3 md:border-b-0 md:py-0"}
          href={item.href}
          key={item.href}
        >
          {item.label}
        </Link>
      ))}
    </nav>
  );
}

function Suggestion({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <button
      className="flex h-full w-full cursor-pointer items-start justify-between gap-6 border-b border-current px-4 py-4 text-left text-sm leading-relaxed last:border-b-0 hover:bg-steel hover:text-concrete sm:px-6"
      type="button"
    >
      <span>{children}</span>
      <span aria-hidden="true">↗</span>
    </button>
  );
}
