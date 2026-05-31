# Playwright MCP Protocol — exact tool sequences

How to drive the Playwright MCP server for both retrieval modes. Tool names below are the
MCP tools available in this environment (prefix `mcp__plugin_playwright_playwright__`,
abbreviated here as `browser_*`).

## Tool cheat-sheet (what each is for)

| Tool | Use for |
|---|---|
| `browser_navigate(url)` | Launch (first call) + go to URL. **The orchestrator's "init Playwright MCP."** |
| `browser_snapshot()` | Accessibility tree — PRIMARY way to *read* page structure & find selectors. Prefer over screenshots. |
| `browser_evaluate(fn)` | Run JS in page: read `innerText`, embedded JSON (`__NEXT_DATA__`), JSON-LD, or `fetch()` an API. |
| `browser_network_requests()` | List all requests — **find the XHR/JSON endpoint** the page used. |
| `browser_network_request(url)` | Get one request's response body — clean structured data. |
| `browser_run_code_unsafe(code)` | Full Playwright API: create incognito contexts, `context.clearCookies()`, add init scripts. Use for hard state-resets & stealth injection. |
| `browser_tabs(action)` | list / new / close / select tabs — the unit of Mode-A concurrency. |
| `browser_close()` | Close the browser — **the rotation primitive** for Mode B. Next `browser_navigate` relaunches fresh. |
| `browser_wait_for(text/time)` | Wait for content (lazy-loaded metrics) or a fixed delay. |
| `browser_click/type/fill_form/select_option/press_key/hover` | Interactions (consent banners, search boxes, tabs). |
| `browser_handle_dialog` | Dismiss native dialogs/popups. |
| `browser_take_screenshot` | Evidence / debugging only — not the primary read path. |

---

## Mode A — Concurrent, ungated (one tab per sub-agent)

**Orchestrator setup**
1. `browser_navigate("about:blank")` (or first real source) → launches the shared browser.
2. For each ungated source, create a tab: `browser_tabs(action="new")`; note its index.
3. Dispatch one sub-agent per source via the Agent tool (`superpowers:dispatching-parallel-agents`).
   Each sub-agent prompt MUST include: **"You are confined to tab index N. Select it with
   `browser_tabs(action='select', index=N)` before any action. Do NOT open/close other tabs,
   do NOT call `browser_close`."**

**Per sub-agent, on its tab**
1. `browser_tabs(select, N)` → `browser_navigate(sourceUrl)`.
2. Prefer JSON: `browser_network_requests()` → spot the data XHR → `browser_network_request(thatUrl)`.
   - Or replay it: `browser_evaluate(() => fetch('/api/...').then(r=>r.json()))`.
3. Fallback: `browser_snapshot()` to locate labeled fields; or `browser_evaluate` for
   `__NEXT_DATA__` / JSON-LD; `innerText` regex only as last resort.
4. Validate + stamp (see `data-schema.md`). Return structured result to orchestrator.

**Converge:** orchestrator collects results, closes spare tabs (`browser_tabs(close, N)`).

> Shared context caveat: all Mode-A tabs share cookies/storage. Acceptable because these
> sources don't meter on accumulated state. If a "Mode A" source unexpectedly shows a
> consent/limit wall, **promote it to Mode B** and stop sharing.

---

## Mode B — Isolated, gated (the GuruFocus / "Guru" case)

Run **alone**. No other tabs active. No parallel agents on the browser.

**1. Quiesce.** Finish/pause Mode-A. Close extra tabs: enumerate with `browser_tabs(list)`,
   `browser_tabs(close, …)` until only one remains.

**2. Plan the harvest.** List EVERY datum needed from this source for the symbol(s) now.
   GuruFocus free ≈ 3 page views per fresh instance → **budget ≤2 navigations per instance**,
   then rotate. (See `../providers/gurufocus.md` once created, or `providers/README.md`.)

**3. Fresh instance.** Start clean:
   - `browser_close()` then `browser_navigate(url)` — relaunches a fresh browser, **or**
   - reset state in place:
     ```
     browser_run_code_unsafe(`
       const ctx = page.context();
       await ctx.clearCookies();
       await page.evaluate(() => { try { localStorage.clear(); sessionStorage.clear(); } catch(e){} });
     `)
     ```
   - (Optional hardening) inject the stealth init script — see `anti-gating-cookbook.md` §Stealth.

**4. Navigate + detect the gate** BEFORE trusting data:
   - `browser_network_requests()` — any `402/403/429`? → gate hit, rotate.
   - `browser_snapshot()` / `browser_evaluate(()=>document.body.innerText)` — search for
     `sign in`, `upgrade`, `free limit`, `subscribe`, paywall overlays, consent banners.
   - If gated → `browser_close()` → fresh instance (step 3), optionally back off / wait.

**5. Extract** (XHR-JSON first; see extraction priority in `../CLAUDE.md` §5).

**6. Rotate on budget.** After ≤2 hits (or on any detected gate), `browser_close()` →
   fresh instance for the next symbol. Repeat **serially**.

**7. Done →** close, hand control back to the orchestrator, resume Mode A.

---

## Sub-agent dispatch template (paste into Agent prompt)

```
You are a data-retrieval sub-agent for the AIInvestment engine.
- TRANSPORT: Playwright MCP only.
- CONCURRENCY: You own ONLY tab index {N}. Select it first; never touch other tabs;
  never call browser_close. (Mode A)
  [OR, for gated:] You have EXCLUSIVE use of the browser. Run alone. Rotate via
  browser_close between hits. Budget ≤2 navigations per fresh instance. (Mode B)
- EXTRACTION: prefer network_requests → JSON; then snapshot/embedded-JSON; innerText regex last.
- VALIDATE every value (numeric ranges; reject "", ".", "N/A").
- STAMP: retrieved_at (UTC ISO-8601), source URL, source_class.
- RETURN: JSON matching references/data-schema.md. Report any gate hit + what you did.
```
