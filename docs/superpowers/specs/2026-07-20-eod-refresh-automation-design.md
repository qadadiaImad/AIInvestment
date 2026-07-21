# EOD refresh automation — design

**Date:** 2026-07-20
**Status:** manifest/verification/notification built; scheduled task pending
**Closes:** `ROADMAP.md:37` — "Scheduled refresh (data decays)"

---

## 1. Problem

The site's data must be refreshed every trading day across the **entire** scope,
with nothing silently missing. Two things stood between us and that, and only
one of them was the scheduler.

### 1.1 The real problem: success is reported, data is absent

Every refresh driver reports **per-step exit codes**. None checked whether the
artifacts a step should produce actually landed. A *guarded* step — one that
skips cleanly when an input is missing — exits 0 and writes nothing, so a run
prints `failures: none` while the site breaks.

This occurred three times, at three different layers, in a single day:

| # | Symptom | Reality |
|---|---|---|
| 1 | `refresh_daily.py`: `steps run: 15 / failures: none` | `ta_desk.json`, `congress.json`, `backtests.json` all absent |
| 2 | Site deployed and "working" | `/strategies` 500, `/stocks/[symbol]` 500, `/terminal/[symbol]` 404 |
| 3 | Fair-value: `requested=108 ok=108 failed=[]` after 49 min | `margin_of_safety_pct` null and series empty in all 128 records |

Each is the same defect at a different depth: **step-level success is not
evidence of data.** A scheduler layered on top would have reproduced all three
faithfully, every night, silently.

### 1.2 Why the step list cannot be the source of truth

Auditing the step list would not have caught #1. `run_backtest.py` *was* in
`refresh_daily.py`'s plan — it ran, reported no failure, and produced nothing.
A step being present and green is not evidence its artifact exists.

Therefore the requirements must come from the **consumer** (what the web app
loads), not from the producer's step list.

---

## 2. Decisions

| Question | Decision | Rationale |
|---|---|---|
| Where does it run? | **Local Windows Task Scheduler** | `data/` holds accumulated history (dated snapshots, congress back to 2015, fundamentals) and is gitignored. A cloud runner starts from a fresh clone with none of it and would need a persistence layer first. Owner confirms the PC stays awake overnight. Already prescribed in `how_to_update.md:200-208`. |
| Include GuruFocus? | **Yes** | It works. See §4. |
| Strictness | **Fail on missing/corrupt; warn on stale** | Adoptable on day one. A gate that fails constantly gets bypassed. |
| Failure notification | **Windows toast + status file** | The run takes ~61 min; a failure at 06:50 is otherwise noticed last. |
| Notify on success? | **No, unless `--notify-success`** | A nightly success toast is noise, and noise is how alerts get ignored. |

---

## 3. Architecture

Four layers, each catching what the one above cannot.

```
web/lib/*.ts  ── declares what the site loads
      │  (drift guard: tests/test_bundles_drift.py)
      ▼
aiinvest/bundles.py ── manifest: 14 bundles, 2 roots, per-bundle cadence
      │
      ├─► verify_bundles.py         standalone CLI (--fix, --json, --only)
      └─► each driver's _summary()  automatic, folded into exit code
              │
              ├─► aiinvest/fundamental_quality.py   fields, not just files
              └─► aiinvest/notify.py                toast + status file
```

### 3.1 Manifest (`aiinvest/bundles.py`)

Declares each artifact's **root**, **producer**, **required/optional**,
**max age**, and **minimum size**.

Two roots, deliberately: `web/public/data` is served statically, while
`portfolio.json` lives in `web/data` so positions are never a public asset
bypassing the `/terminal` gate. A test asserts `portfolio.json` is never
declared public — the privacy invariant is enforced structurally.

Cadence is **per bundle**, encoding each feature's intent rather than one
blanket rule: daily 30h (24h + slack), backtests 192h, congress 744h,
hand-curated chokepoints 2160h.

`required=False` means *may be absent*, never *may be corrupt*. An optional
bundle that fails to parse is still a failure.

Freshness prefers the bundle's own `generated_at` and falls back to file
mtime, recording which was used (`age_source`) so an unknown age is never
reported as confidently fresh. It reuses `merge.is_stale()` so both layers
agree on what "stale" means.

### 3.2 Drift guard

The manifest alone is another hand-maintained list that rots. A test reads the
real loaders in `web/lib/*.ts` and fails if any bundle they load is undeclared.
Adding a page that reads `foo.json` without declaring it fails at commit time
rather than 500-ing in production.

`web/lib/data.ts` is **UTF-8 with BOM**: ripgrep calls it binary and plain grep
skips it silently. That is precisely how the missing bundles went unnoticed.
The guard reads with `encoding="utf-8-sig"`.

### 3.3 Driver ownership

Each driver verifies **only what it owns** (`Bundle.driver`):

| Driver | Owns |
|---|---|
| `refresh_daily.py` | site, quantum, news, macro, risk, archetypes, graph_analysis, backtests, chokepoints, portfolio |
| `refresh_ta.py` | ta_desk |
| `refresh_congress.py` | congress, congress_stocks |
| `refresh_all.py` | all 14 (unscoped) |
| *(none)* | extra_stocks — no driver builds it, so no driver is blamed |

Checking all 14 from `refresh_ta.py` would report `congress.json` missing on a
machine that simply has not run the monthly job. False alarms are how people
learn to ignore output, which would defeat the entire mechanism.

### 3.4 Data quality (`aiinvest/fundamental_quality.py`)

The manifest catches a missing *file*. This catches a present file with empty
*fields* — failure #3 above.

---

## 4. GuruFocus

GuruFocus is **not** blocked wholesale. It has two retrieval paths that fail
independently:

| Field | Path | State |
|---|---|---|
| `fundamental_value` (GF Value) | server-rendered `innerText` | **working — 128/128** |
| `margin_of_safety_pct` | intercepted chart XHR | gated |
| `fundamental_value_series` | intercepted chart XHR | gated |

`fundamental_fetch.py` uses **Python Playwright** (`sync_playwright`), not
Playwright MCP — so it is fully scriptable and safe for an unattended job.
Per attempt it launches a fresh stealth Chromium and closes it, satisfying the
Mode B rotation rule in `CLAUDE.md`. Navigation stays serial.

> **Note for future readers.** `source: "fundamental-model"` in these records is
> a **hardcoded constant**, not a fallback marker — it is GuruFocus's own name
> for the metric. A *null* `fundamental_value`, not this string, indicates a
> blocked fetch. Misreading it led to a wrong conclusion that GuruFocus was
> dead and should be removed from the pipeline.

The two paths are therefore **thresholded separately**: GF-value coverage below
80% fails (the reliable path broke — a real outage); empty chart fields only
warn (that is the wall's normal state). Collapsing them into one number would
either cry wolf nightly or hide a genuine outage.

---

## 5. Schedule

### 5.1 Timing and the EOD assumption

**06:00 local publishes the _prior_ session's close.** US markets close 16:00
ET = 22:00 Paris; a 06:00 run is ~8 hours after close, well past settlement.

This assumption was previously implicit. No market-close or EOD-finality rule
exists anywhere in the repo — only conventions (`retrieved_at` in UTC ISO-8601,
brief samples stamped 21:00 UTC). Stating it here makes it reviewable.

### 5.2 Jobs

| Task | Cadence | Command |
|---|---|---|
| `AIInvest-Daily` | daily 06:00 | `refresh_all.py --deploy` |
| `AIInvest-Congress` | monthly, day 1, 07:00 | `refresh_congress.py --deploy` |

Observed durations (2026-07-20): fair-value 2921s, daily 494s, congress 205s,
TA 3s — **~61 min total**, 80% of it GuruFocus.

`refresh_all.py` must invoke `refresh_ta.py`, which it does not yet do. TA is
deliberately a separate driver (`how_to_update.md:85-95`), but "deliberately
separate" must not mean "never runs".

### 5.3 Constraints (from `CLAUDE.md`)

- Gated navigation stays **serial**; parallelism applies only to parse/write.
- EDGAR ≤10 req/s with a descriptive User-Agent; Yahoo soft limit, polite jitter.
- Every datum carries `retrieved_at` (UTC) and its source.

---

## 6. Failure notification

- `data/status/last_run.json` — always written. A stale `ok` timestamp is
  itself the signal that last night never ran.
- **Windows toast** — persists in Action Center, so a 06:00 failure is still
  waiting at 08:00.

Mechanism chosen by testing the machine, not assumption: BurntToast and
`msg.exe` are absent; WinRT works, with a .NET NotifyIcon balloon fallback.
The payload goes over `-EncodedCommand` (UTF-16LE base64) to avoid quoting and
codepage problems; toast XML is escaped so an `&` in a filename cannot break it.

Notification is observability, not the job: every path degrades to a return
value so a broken notifier can never fail a refresh that succeeded.

---

## 7. Open items

1. **`--deploy` on every nightly run pushes to production automatically.**
   `/terminal` is currently ungated in production (`TERMINAL_KEY` unset), so the
   analyst desks — including the portfolio page — are publicly reachable. Set
   `TERMINAL_KEY` before enabling nightly auto-deploy.
2. **`refresh_all.py` does not call `refresh_ta.py`** (§5.2).
3. **`how_to_update.md:200-208` has stale paths** (`C:\Users\imadq\...`). The
   registration should be a committed script, not copy-paste prose.
4. **Chart-XHR gate not diagnosed.** `gurufocus.detect_gate()` exists but is
   not surfaced; we do not know whether the XHR block is fixable.
5. **`web/public/data/prices/`** is a directory of per-symbol history, not a
   single bundle, and is unverified by the manifest.

---

## 8. Status

| Component | State |
|---|---|
| Manifest + verifier + drift guard | done — `7ca99ee` |
| Driver wiring, exit-code aware | done — `dd25618` |
| Fundamental quality checks | done — `1e0b966` |
| Failure notification | done — `665f03d` |
| Scheduled task registration | **pending** |

1064 tests passing.

*Educational/research only — not investment advice.*
