const DEFAULT_SPECIALS = [
  "Help me prepare for a difficult conversation.",
  "Explain compound interest in plain English.",
  "Plan a focused afternoon of work.",
] as const;

export function HouseSpecials({
  items = DEFAULT_SPECIALS,
  orientation = "stacked",
}: Readonly<{ items?: readonly string[]; orientation?: "horizontal" | "stacked" }>) {
  const isHorizontal = orientation === "horizontal";

  return (
    <div>
      <p className="text-xs uppercase">House Specials</p>
      <div
        className={
          isHorizontal
            ? "mt-4 grid border border-outline sm:grid-cols-3"
            : "mt-4 grid h-72 grid-rows-3 border border-outline"
        }
      >
        {items.map((item) => (
          <button
            className={
              isHorizontal
                ? "flex min-h-32 w-full cursor-pointer items-start justify-between gap-6 border-b border-outline px-4 py-4 text-left text-sm leading-relaxed last:border-b-0 hover:bg-steel hover:text-concrete sm:border-b-0 sm:border-r sm:px-6 sm:last:border-r-0"
                : "flex h-full w-full cursor-pointer items-start justify-between gap-6 border-b border-outline px-4 py-4 text-left text-sm leading-relaxed last:border-b-0 hover:bg-steel hover:text-concrete sm:px-6"
            }
            key={item}
            type="button"
          >
            <span>{item}</span>
            <span aria-hidden="true">↗</span>
          </button>
        ))}
      </div>
    </div>
  );
}
