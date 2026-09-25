"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";

// Phone navigation (mobile audit, 2026-09-25). The header's 11-item strip is
// hidden below `sm`; this fixed bar carries the four tasks a phone reader
// opens the app for, and a "More" sheet lists every route. Desktop is untouched.
const TABS = [
  { href: "/", label: "Home" },
  { href: "/screener", label: "Screener" },
  { href: "/map", label: "Map" },
  { href: "/news", label: "News" },
];

const MORE = [
  { href: "/terminal", label: "TA desk" },
  { href: "/resiliency", label: "Resiliency" },
  { href: "/chokepoints", label: "Chokepoints" },
  { href: "/strategies", label: "Strategies" },
  { href: "/congress", label: "Congress" },
  { href: "/halal", label: "Halal" },
  { href: "/about", label: "About" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") return pathname === "/";
  return pathname === href || pathname.startsWith(href + "/");
}

export default function MobileTabBar() {
  const pathname = usePathname() ?? "/";
  const [open, setOpen] = useState(false);
  const moreActive = MORE.some((m) => isActive(pathname, m.href));

  return (
    <div className="sm:hidden">
      {open ? (
        <div className="fixed inset-0 z-40" onClick={() => setOpen(false)}>
          <div className="absolute inset-0 bg-black/60" />
          <nav
            aria-label="All sections"
            className="absolute bottom-14 left-0 right-0 bg-[#0e131d] border-t border-term-border pb-[env(safe-area-inset-bottom)]"
            onClick={(e) => e.stopPropagation()}
          >
            {MORE.map((m) => (
              <Link
                key={m.href}
                href={m.href}
                onClick={() => setOpen(false)}
                className={`flex items-center min-h-[48px] px-4 text-[13px] uppercase tracking-wider border-b border-term-border/60 ${
                  isActive(pathname, m.href) ? "text-emerald-400" : "text-zinc-200"
                }`}
              >
                {m.label}
              </Link>
            ))}
          </nav>
        </div>
      ) : null}
      <nav
        aria-label="Primary"
        className="fixed bottom-0 left-0 right-0 z-50 grid grid-cols-5 border-t border-term-border bg-[#0b0f17]/95 backdrop-blur pb-[env(safe-area-inset-bottom)]"
      >
        {TABS.map((t) => {
          const active = isActive(pathname, t.href);
          return (
            <Link
              key={t.href}
              href={t.href}
              aria-current={active ? "page" : undefined}
              className={`flex items-center justify-center min-h-[56px] text-[11px] font-semibold uppercase tracking-wider ${
                active ? "text-emerald-400" : "text-term-muted"
              }`}
            >
              {t.label}
            </Link>
          );
        })}
        <button
          type="button"
          onClick={() => setOpen((o) => !o)}
          aria-expanded={open}
          className={`flex items-center justify-center min-h-[56px] text-[11px] font-semibold uppercase tracking-wider ${
            moreActive || open ? "text-emerald-400" : "text-term-muted"
          }`}
        >
          More {open ? "▾" : "▴"}
        </button>
      </nav>
    </div>
  );
}
