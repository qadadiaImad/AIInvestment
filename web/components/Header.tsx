import Link from "next/link";

const NAV = [
  { href: "/", label: "HOME" },
  { href: "/terminal", label: "TA DESK" },
  { href: "/map", label: "MAP" },
  { href: "/resiliency", label: "RESILIENCY" },
  { href: "/chokepoints", label: "CHOKEPOINTS" },
  { href: "/screener", label: "SCREENER" },
  { href: "/strategies", label: "STRATEGIES" },
  { href: "/congress", label: "CONGRESS" },
  { href: "/news", label: "NEWS" },
  { href: "/about", label: "ABOUT" },
];

export default function Header({ generatedAt }: { generatedAt: string }) {
  return (
    <header className="sticky top-0 z-30 border-b border-term-border bg-[#0b0f17]/95 backdrop-blur">
      <div className="flex items-center gap-3 px-3 h-9">
        <Link
          href="/"
          className="font-bold tracking-tight text-[13px] whitespace-nowrap shrink-0"
        >
          AI<span className="text-emerald-400">STACK</span>
          <span className="text-term-muted">·TERMINAL</span>
        </Link>
        {/* Nav scrolls horizontally instead of wrapping — at 9 items this
            collides with the wordmark on narrow phones otherwise (the
            header row has a fixed height, so wrapped items would overlap
            rather than push the row taller). */}
        <nav className="flex items-center gap-3 text-[11px] overflow-x-auto whitespace-nowrap min-w-0 [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="text-term-muted hover:text-emerald-400 transition-colors shrink-0"
            >
              {n.label}
            </Link>
          ))}
        </nav>
        <span className="hidden lg:inline text-[10.5px] text-term-muted truncate ml-auto shrink-0">
          Energy · Chips · Infra · Models · Apps
        </span>
      </div>
      <div className="px-3 py-0.5 text-[9.5px] text-term-muted border-t border-term-border/60 flex items-center gap-2">
        <span className="text-emerald-500">●</span>
        <span>Updated {generatedAt} · Educational research only — not financial advice.</span>
      </div>
    </header>
  );
}
