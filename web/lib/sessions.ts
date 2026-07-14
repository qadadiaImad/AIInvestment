// Client-safe session-clock pure functions — no node:fs, no server-only
// imports, so this module can be used from both Server and Client
// Components (mirrors the lib/conflict.ts / lib/news.ts client/server
// split documented there).
//
// MUST match scripts/aiinvest/ta.py's SESSION_WINDOWS_UTC exactly — 9h
// windows (Tokyo 00-09, London 08-17, New York 13-22 UTC). Keep these two
// tables in sync if either changes.
//
// Caveat (surface in the UI): fixed UTC hours, no DST adjustment.

export type SessionKey = "tokyo" | "london" | "new_york";

export interface SessionWindow {
  key: SessionKey;
  label: string;
  openUtcHour: number;
  closeUtcHour: number;
}

export const SESSIONS: SessionWindow[] = [
  { key: "tokyo", label: "Tokyo", openUtcHour: 0, closeUtcHour: 9 },
  { key: "london", label: "London", openUtcHour: 8, closeUtcHour: 17 },
  { key: "new_york", label: "New York", openUtcHour: 13, closeUtcHour: 22 },
];

// Whether `s` is open at `nowUtc`, using UTC wall-clock hours only
// (half-open interval [open, close)).
export function isSessionOpen(s: SessionWindow, nowUtc: Date): boolean {
  const h = nowUtc.getUTCHours() + nowUtc.getUTCMinutes() / 60;
  return h >= s.openUtcHour && h < s.closeUtcHour;
}

// Minutes until the next open/close transition for `s`, relative to
// `nowUtc`. Always positive; wraps to the next UTC day when needed.
export function minutesToNextTransition(
  s: SessionWindow,
  nowUtc: Date,
): number {
  const nowMinutes = nowUtc.getUTCHours() * 60 + nowUtc.getUTCMinutes();
  const openMinutes = s.openUtcHour * 60;
  const closeMinutes = s.closeUtcHour * 60;
  const open = isSessionOpen(s, nowUtc);
  const targetMinutes = open ? closeMinutes : openMinutes;

  let delta = targetMinutes - nowMinutes;
  if (delta <= 0) delta += 24 * 60;
  return delta;
}
