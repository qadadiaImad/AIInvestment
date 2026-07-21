"use client";

import { useSyncExternalStore } from "react";
import { SESSIONS, isSessionOpen, minutesToNextTransition } from "@/lib/sessions";

function fmtMinutes(m: number): string {
  const h = Math.floor(m / 60);
  const mm = m % 60;
  if (h <= 0) return `${mm}m`;
  return `${h}h ${mm}m`;
}

// Subscribes to the system clock via useSyncExternalStore (the sanctioned
// way to synchronize with an external, time-based system) rather than
// calling setState synchronously inside an effect. The snapshot is a
// once-per-minute tick counter; getServerSnapshot returns a fixed value so
// SSR never depends on wall-clock time.
function subscribeMinuteTick(callback: () => void) {
  const id = setInterval(callback, 60_000);
  return () => clearInterval(id);
}
function getMinuteTick() {
  return Math.floor(Date.now() / 60_000);
}
function getServerMinuteTick() {
  return 0;
}

// Sticky ticking Tokyo/London/NY session badges. Pure wall-clock math — no
// data dependency, renders even when ta_desk.json is absent.
export default function SessionClockStrip() {
  // Value itself is unused — re-render is triggered once per minute; `now`
  // below is computed fresh at render time from the real wall clock.
  useSyncExternalStore(subscribeMinuteTick, getMinuteTick, getServerMinuteTick);
  const now = new Date();

  return (
    <div className="sticky top-9 z-20 border-b border-term-border bg-[#0b0f17]/95 backdrop-blur px-3 py-1.5 flex items-center gap-3 overflow-x-auto">
      {SESSIONS.map((s) => {
        const open = isSessionOpen(s, now);
        const mins = minutesToNextTransition(s, now);
        return (
          <div
            key={s.key}
            className="flex items-center gap-1.5 shrink-0 text-[10.5px]"
          >
            <span
              className={`inline-block w-1.5 h-1.5 rounded-full ${
                open ? "bg-emerald-400" : "bg-zinc-600"
              }`}
              aria-hidden="true"
            />
            <span className={open ? "text-zinc-200" : "text-term-muted"}>
              {s.label}
            </span>
            <span className="text-term-muted tnum">
              {open
                ? `closes in ${fmtMinutes(mins)}`
                : `opens in ${fmtMinutes(mins)}`}
            </span>
          </div>
        );
      })}
      <span className="ml-auto text-[9px] text-term-muted whitespace-nowrap">
        UTC session hours, approximate
      </span>
    </div>
  );
}
