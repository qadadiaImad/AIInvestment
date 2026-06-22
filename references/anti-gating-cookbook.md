# Anti-Gating Cookbook

Concrete recipes to defeat ad-walls and free-tier view limits, derived from the
[`GuruTrade`](https://github.com/qadadiaImad/GuruTrade) scraper and hardened. Use with
`playwright-mcp-protocol.md`.

## Core insight: gates count state, so deny them state

A free-tier "N views then pay" limit is a **counter** keyed on one or more of:
**cookies**, **localStorage/sessionStorage**, **IndexedDB**, **IP address**, occasionally a
**device fingerprint**. GuruTrade beat GuruFocus by giving each symbol a pristine,
cookie-less, history-less browser. We do the same — proactively, and with detection.

---

## Recipe 1 — Hard reset (rotate the instance)

The strongest reset. Use between gated hits (Mode B).

**Via MCP:** `browser_close()` → next `browser_navigate(url)` relaunches fresh.

**In-place wipe (when full relaunch is overkill):**
```js
// browser_run_code_unsafe
const ctx = page.context();
await ctx.clearCookies();
await page.evaluate(() => {
  try { localStorage.clear(); sessionStorage.clear(); } catch (e) {}
  try { (indexedDB.databases ? indexedDB.databases() : Promise.resolve([]))
        .then(dbs => dbs.forEach(d => d.name && indexedDB.deleteDatabase(d.name))); } catch (e) {}
});
```

**Python batch equivalent (GuruTrade-style):** new `launch()` + `new_context()` per hit, or
disk-wipe the profile dir (`shutil.rmtree` of `Cookies`, `Local Storage`, `Cache`,
`IndexedDB`, `Session Storage`, …) before `launch_persistent_context`. One OS process per
symbol gives the hardest isolation.

---

## Recipe 2 — Stealth bundle (look like a human's Chrome)

GuruTrade's hand-rolled stealth (no plugin). Inject before page scripts run.

**Launch flags (Python batch):**
```python
ignore_default_args=["--enable-automation"],
args=["--disable-blink-features=AutomationControlled",
      "--disable-popup-blocking", "--disable-notifications", "--no-sandbox"]
user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
           "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
viewport={"width": 1920, "height": 1080}
```

**Init script (inject via `browser_run_code_unsafe` → `context.addInitScript(...)`):**
```js
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
Object.defineProperty(navigator, 'plugins',   { get: () => [1,2,3,4,5] });
Object.defineProperty(navigator, 'languages', { get: () => ['en-US','en'] });
window.chrome = { runtime: {} };
const orig = navigator.permissions.query;
navigator.permissions.query = (p) => p && p.name === 'notifications'
  ? Promise.resolve({ state: 'granted' }) : orig(p);
```
> **Upgrade over GuruTrade:** rotate the UA string and jitter the viewport (±a few hundred px)
> per run. GuruTrade used static values everywhere → fingerprintable at scale.

---

## Recipe 3 — Detect the gate (GuruTrade lacked this)

Decide to rotate *before* harvesting garbage. Check, in order:

1. **Network status:** `browser_network_requests()` → any `402 / 403 / 429`?
   `429` = rate-limited (back off); `402/403` = paywall/forbidden (rotate / abandon).
2. **DOM/text signals** (`browser_snapshot` or `innerText`): case-insensitive search for
   `sign in`, `log in`, `subscribe`, `upgrade`, `free limit`, `premium`, `paywall`,
   `you have reached`, `register to continue`, consent/CMP overlays (`Accept all cookies`).
3. **Missing-data heuristic:** the metric you expected is absent or blurred → likely gated.

On gate → rotate (Recipe 1), optional polite back-off, retry on fresh instance.

### Evidence: the guru chart API is IP/session-throttled, not page-gated (verified 2026-06-01)

The historical fundamental-value **series** comes from the chart endpoint
`https://www.gurufocus.com/reader/_api/chart/{SYM}/valuation?v=1.8.61`. Two transports give
opposite results against the *same URL* — proof the gate keys on the **client's
IP/session**, not on the page or the symbol:

| Transport | Result against the chart endpoint |
|---|---|
| **Local headless python-playwright** (`scripts/fundamental_fetch.py`, fresh clean profile, single IP) | **HTTP 403 for EVERY ticker** — incl. NVDA, which already has a series. 38/38 series backfills failed both at 4-way concurrency **and** with gentle serial pacing. (The server-rendered *current value* is unaffected — it still works locally.) |
| **Playwright MCP browser** (orchestrator-owned real browser, real profile/session/IP) | **HTTP 200** — verified on NVDA; the page even prefetches peers AVGO/MU/AMD at 200. Defeats the gate. |

**Doctrine:** because a fresh clean profile from our IP is **already 403** before any view
count accrues, this is **IP/session reputation throttling**, not a free-view counter —
state-wiping (Recipe 1) does NOT help the local path. **SERIES retrieval must therefore use
the Playwright MCP real-browser session**, not local headless. Run it under the Mode-B gated
contract: isolated, **serial** MCP navigation (the one browser is shared), harvest-in-one-pass
via same-origin `fetch` from the authenticated page, rotate per budget, and confirm the chart
request is `200` (not `403`) before trusting any series. Exact sequence:
`playwright-mcp-protocol.md` § *Historical fundamental (guru) series — Mode B via MCP*. The
local `fundamental_fetch.py` path stays valid for the current **value** only.

> **Owner's rule (7-day free-trial wall):** if a source shows a **7-day free-trial / signup /
> "subscribe to premium" wall**, **restart the instance** (fresh browser / `browser_close` →
> relaunch, or new local Chromium) and retry — **never store a value read from behind the
> wall.** Detect via text: `free trial`, `7-day`, `sign up to view`, `create a free account`,
> `subscribe to premium`, `unlock all`. Implemented in `scripts/fundamental_fetch.py`
> (`_is_trial_wall` → up to 3 fresh-instance rotations). This is why the fundamental-value
> sweep hit 97/97 with zero gated reads.

---

## Recipe 4 — Polite throttling & back-off

GuruTrade fired one IP at 4019 symbols and survived only because the page was lenient.
Don't assume that. Defaults:
- Randomized delay **2–5 s** between hits to the same host (jitter, not fixed).
- Exponential back-off on `429`: 30s → 60s → 120s, then rotate IP/abandon.
- Identify with a real UA; never spoof a fake bot identity that violates ToS.
- **Proxy hook (for scale only):** pass `proxy={server, username, password}` to
  `launch()`/`new_context()` in batch; rotate residential proxies per N hits. Off by
  default — single IP for normal volumes.

---

## Recipe 5 — Consent / cookie banners (EU CMP walls)

Yahoo and others throw a "Accept all" consent interstitial. Handle, don't fight:
- `browser_snapshot()` → find the accept button → `browser_click`.
- Or set the consent cookie directly via `browser_run_code_unsafe` (`context.addCookies`).
- Or append known consent query params where the provider supports them.

---

## Recipe 6 — Clean extraction (don't repeat the `"."` bug)

GuruTrade's `innerText`-regex produced dirty values (`current_ratio: "."`). Mitigate:
- **Prefer structured sources** (Recipe order in `../CLAUDE.md` §5): XHR-JSON > embedded
  JSON > DOM selectors > innerText regex.
- **Validate** every extracted value:
  - numeric fields parse to a finite number; reject `""`, `"."`, `"N/A"`, `"-"`.
  - sanity ranges (e.g. P/E within plausible bounds; price > 0; percentages 0–100 or signed).
  - keep the raw string AND the parsed value; flag `dirty: true` when validation fails
    rather than silently storing junk.

---

## What NOT to do
- Don't solve CAPTCHAs or defeat hard auth — that crosses ToS/legal lines. GuruTrade only
  *waited out* Cloudflare; it never solved it. Match that restraint.
- Don't run a gated source concurrently with anything (poisons the counter).
- Don't redistribute scraped premium data; this engine is for the owner's research only.
