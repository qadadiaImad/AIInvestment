import Link from "next/link";

// Server component — terminal-scoped sub-nav (TA DESK / RISK / MACRO /
// ARCHETYPES). Deliberately
// NOT usePathname()/a client component: the active tab is passed down as a
// plain prop from each server page, matching layout.tsx's own reasoning for
// staying server-rendered (avoid a one-frame hydration flash / chrome
// flicker on first paint). This stays scoped to /terminal/* pages only — it
// does NOT touch components/Header.tsx's global NAV array.
const SUB_NAV = [
  { href: "/terminal", label: "TA DESK" },
  { href: "/terminal/risk", label: "RISK" },
  { href: "/terminal/macro", label: "MACRO" },
  { href: "/terminal/archetypes", label: "ARCHETYPES" },
] as const;

export default function TerminalSubNav({
  currentPath,
}: {
  currentPath: string;
}) {
  return (
    <nav className="flex items-center gap-4 px-3 h-8 border-b border-term-border text-[11px] overflow-x-auto whitespace-nowrap [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
      {SUB_NAV.map((item) => {
        const active = currentPath === item.href;
        return (
          <Link
            key={item.href}
            href={item.href}
            className={
              active
                ? "shrink-0 py-1.5 border-b-2 border-emerald-400 text-emerald-400 font-semibold tracking-wider"
                : "shrink-0 py-1.5 border-b-2 border-transparent text-term-muted hover:text-emerald-400 tracking-wider"
            }
          >
            {item.label}
          </Link>
        );
      })}
    </nav>
  );
}
