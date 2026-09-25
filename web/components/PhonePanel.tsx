"use client";

import { useEffect, useState } from "react";

// A stock-page panel that is collapsed by default on phones and always open on
// wider screens (mobile audit, 2026-09-25). No media query is needed for the
// visibility: the body is `hidden sm:block` until tapped, so the server render
// is correct for both. `lazy` additionally defers mounting the children on a
// phone until the panel is opened, for heavy embeds such as the TradingView
// widget; on wide screens (and before hydration) children always mount.
const PHONE = "(max-width: 639px)";

export default function PhonePanel({
  title,
  children,
  className = "",
  id,
  lazy = false,
}: {
  title: string;
  children: React.ReactNode;
  className?: string;
  id?: string;
  lazy?: boolean;
}) {
  const [open, setOpen] = useState(false);
  const [phone, setPhone] = useState(false);

  useEffect(() => {
    if (!lazy) return;
    const mq = window.matchMedia(PHONE);
    const apply = () => setPhone(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, [lazy]);

  const mountChildren = !lazy || !phone || open;

  return (
    <section
      id={id}
      className={`border border-term-border rounded-sm bg-[#0e131d] ${className}`}
    >
      <button
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        className="sm:hidden w-full flex items-center justify-between min-h-[44px] px-3 text-left text-[11px] font-semibold uppercase tracking-wider text-term-muted border-b border-term-border"
      >
        <span>{title}</span>
        <span className="text-emerald-400 text-[13px]">{open ? "−" : "+"}</span>
      </button>
      <div className="hidden sm:block px-3 py-1.5 border-b border-term-border text-[10.5px] font-semibold uppercase tracking-wider text-term-muted">
        {title}
      </div>
      <div className={`${open ? "block" : "hidden"} sm:block p-3`}>
        {mountChildren ? children : null}
      </div>
    </section>
  );
}
