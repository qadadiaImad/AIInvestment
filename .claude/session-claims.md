# Session claims — read this before taking a shared resource

Two or more Claude sessions run against this machine and this repo. Several
resources here are **single-instance**: taking one while another session holds it
does not queue, it corrupts. This file is the coordination point. It is advisory —
it only works if every session reads it before claiming and clears its own rows
when done.

**Before claiming:** read this file, then verify the resource is actually free
(commands below). A stale row is possible; a live process is evidence.

---

## Live claims

| Resource | Held by | Since | Until | Notes |
|---|---|---|---|---|
| _(none currently held by this session)_ | | | | |

## Recently released

| Resource | Session | Released | Notes |
|---|---|---|---|
| Remotion render + ffmpeg | reel/trading-quiz | 2026-08-12 17:37Z | SPY cup-and-handle zoom reel, v3 shipped |
| git branch `feat/multi-sector-research-platform` | reel/trading-quiz | 2026-08-12 17:37Z | commits `1bee89c`, `e0c548b` |
| grok-cli TTS | reel/trading-quiz | 2026-08-12 17:33Z | 26 syntheses (2 script passes × 13 segments) |
| Higgsfield media upload | reel/trading-quiz | 2026-08-12 17:38Z | 2 videos uploaded |

---

## The resources, and why each one bites

### Playwright MCP browser — STRICTLY ONE OWNER
The contract is in CLAUDE.md §3. One browser process, shared cookies/storage.
A gated source (GuruFocus etc.) requires `browser_close` to reset its counter —
**which destroys whatever the other session was doing in that browser.**

Do not call `browser_close`, `browser_navigate` on a fresh instance, or
`context.clearCookies()` while another session holds it. Check first:

```bash
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='chrome.exe'\" | Where-Object { \$_.CommandLine -like '*ms-playwright-mcp*' } | Select-Object ProcessId,CreationDate"
```

Non-empty output = someone has it open. Claim it in the table above before use.

### Remotion renders — concurrent renders corrupt each other
A render is one node process plus a fleet of headless Chrome workers, and it
saturates the CPU. Two at once thrash, and per the standing note in memory,
stopping one kills the *shell* but not node/chrome, so orphans keep writing.
Verify before starting:

```bash
powershell -NoProfile -Command "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | Where-Object { \$_.CommandLine -like '*remotion*' } | Select-Object ProcessId,CreationDate"
```

### GPU / ComfyUI — exclusive
`nvidia-smi` preflight, and never GUI + headless together (see the ComfyUI note
in memory). Port 8000 answering means a backend is already up — do not start a
second.

```bash
nvidia-smi --query-gpu=memory.used,memory.total,utilization.gpu --format=csv
curl -s -m 3 -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/system_stats
```

### git — one branch, no worktrees
Everything currently runs in `C:/Users/imadq/AIInvestment` on
`feat/multi-sector-research-platform`. There is no second worktree, so two
sessions committing interleave on the same branch and can race the index.
If both sessions need to write code at once, the second should take a worktree
(`git worktree add`) rather than sharing the checkout.

### Shared quota / credentials
- **grok-cli** — one OAuth session, usage metered in `~/.grok-cli/session.db`.
- **Higgsfield** — shared credits and media library.
- **IBKR MCP** — not authorized in this session; authorizing is a user action.

These do not corrupt, but they do deplete. Say what you spent in the released
table so the other session isn't surprised by a quota wall.

---

## Not ours to touch

Processes belonging to other projects on this machine. Leave them running:

- `C:\Test\Cv-Helper` — a Next.js dev server (`pnpm -w run dev:app`). Different
  repo entirely. Seen holding node PIDs and contributing to GPU/CPU load.
