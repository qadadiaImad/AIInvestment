import Link from "next/link";

const NAV = [
  { href: "/", label: "TERMINAL" },
  { href: "/map", label: "MAP" },
  { href: "/resiliency", label: "RESILIENCY" },
  { href: "/screener", label: "SCREENER" },
  { href: "/strategies", label: "STRATEGIES" },
  { href: "/congress", label: "CONGRESS" },
  { href: "/news", label: "NEWS" },
  { href: "/about", label: "ABOUT" },
];

export default function Header({ generatedAt }: { generatedAt: string }) {
  return (
    <header className="sticky top-0 z-30 border-b border-term-border bg-[#0b0f17]/95 backdrop-blur">
      <div className="flex items-center justify-between px-3 h-9">
        <div className="flex items-center gap-4 min-w-0">
          <Link href="/" className="font-bold tracking-tight text-[13px] whitespace-nowrap">
            AI<span className="text-emerald-400">STACK</span>
            <span className="text-term-muted">·TERMINAL</span>
          </Link>
          <span className="hidden sm:inline text-[10.5px] text-term-muted truncate">
            Energy · Chips · Infra · Models · Apps
          </span>
        </div>
        <nav className="flex items-center gap-3 text-[11px]">
          {NAV.map((n) => (
            <Link
              key={n.href}
              href={n.href}
              className="text-term-muted hover:text-emerald-400 transition-colors"
            >
              {n.label}
            </Link>
          ))}
        </nav>
      </div>
      <div className="px-3 py-0.5 text-[9.5px] text-term-muted border-t border-term-border/60 flex items-center gap-2">
        <span className="text-emerald-500">●</span>
        <span>Updated {generatedAt} · Educational research only — not financial advice.</span>
      </div>
    </header>
  );
}
