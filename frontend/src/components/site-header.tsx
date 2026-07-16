import Link from "next/link";

const NAVIGATION = [
  { href: "/", label: "Spirit Guide" },
  { href: "/tasting-room", label: "Tasting Room" },
  { href: "/lab", label: "The Lab" },
  { href: "/results", label: "Results" },
] as const;

export type SitePath = (typeof NAVIGATION)[number]["href"];

export function SiteHeader({ activePath }: Readonly<{ activePath: SitePath }>) {
  return (
    <header className="relative border-b border-outline">
      <div className="mx-auto flex min-h-16 w-full max-w-5xl items-center justify-between gap-8 px-4 sm:px-6 lg:max-w-7xl">
        <Link className="text-base" href="/">
          ChatG<span className="text-signal">&amp;</span>T
        </Link>

        <Navigation activePath={activePath} className="hidden items-center gap-6 text-xs uppercase md:flex" />

        <details className="md:hidden">
          <summary className="cursor-pointer list-none text-xs uppercase">Menu</summary>
          <Navigation
            activePath={activePath}
            className="fixed left-0 right-0 top-16 z-10 grid border-b border-outline bg-concrete px-4 py-4 text-xs uppercase sm:px-6"
          />
        </details>
      </div>
    </header>
  );
}

function Navigation({ activePath, className }: Readonly<{ activePath: SitePath; className: string }>) {
  return (
    <nav aria-label="Main navigation" className={className}>
      {NAVIGATION.map((item) => {
        const isActive = item.href === activePath;

        return (
          <Link
            aria-current={isActive ? "page" : undefined}
            className={
              isActive
                ? "border-b border-outline py-3 text-signal md:py-0 md:text-steel"
                : "border-b border-outline py-3 md:border-b-0 md:py-0"
            }
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
