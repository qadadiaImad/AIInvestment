# How people pair Grok with Claude (Fable 5) — web research, 2026-08-02

5-agent research sweep (forums/GitHub, X+blogs, tutorials, official docs,
completeness critic). Findings are subagent-reported with sources; spot-verify
before relying on any single claim. Reddit itself was unreachable (WebFetch
refuses reddit.com; site-scoped queries returned nothing) — community signal
came via GitHub, HN and blogs instead.

## The dominant pattern: "Fable architect, Grok construction crew"

- Fable 5 writes the spec and reviews the diffs; Grok 4.5 does the bulk
  typing via the Grok CLI. Shared as a daily workflow on X
  (x.com/dr_cintas/status/2075630574069592251) and as a MindStudio tutorial
  (Fable writes a master JSON spec → Grok executes 50+ parallel jobs →
  Fable does final review).
- The economics behind it (Theo's benchmark, via finance.biggo.com):
  Grok 4.5 ≈ $0.31/task vs Fable 5 ≈ $2.75/task — ~9× cheaper, so judgment
  goes to Fable, volume goes to Grok.
- The reverse direction also exists: Grok Build as fast orchestrator
  delegating hard problems to Claude/Codex (x.com/arthurkatcher).
- Quality caveat (paddo.dev "Ten Findings, Two Real"): Grok-as-reviewer
  surfaced 10 findings, only 2 real — a Claude grading pass caught the
  false positives. Confidence ≠ correctness in the cheap lane.
- Skeptic file: Cognition's "Don't Build Multi-Agents" and production
  post-mortems argue chained multi-agent flows fail without a single
  source of truth for context (dev.to/crabtalk).

## The bridge tooling, by tier

| Tier | Tool | What it does |
|---|---|---|
| Official plugin | xai-org/grok-build-plugin-cc | Claude Code slash-commands shell out to the grok CLI: /review (read-only diff review), /critique, /delegate (write-capable), /import (transfer the Claude session INTO Grok) |
| Community plugins | thevibeworks/grok-plugin-cc, zachdunn (/grok-cc:rescue) | same delegation pattern, lighter |
| MCP servers | wynandw87/claude-code-grok-mcp (14 tools: chat, web/X search, code exec, image+video gen, TTS/STT), GuDaStudio/GrokSearch (replaces Claude's WebSearch with Grok live search), ashdatsiuk grok-x-research-mcp (native x_search) | Grok as callable tools inside a Claude session |
| Backend swap | claude-launcher (`claude-launcher -g`) | runs Grok 4.5 AS Claude Code's model via an X subscription — Grok's backend speaks the Anthropic API natively |
| Router | musistudio/claude-code-router | routes request TYPES (background/think/long-context) to different models incl. Grok — by category, not difficulty |
| Media | runapi-ai/grok-imagine skill; Vercel AI-gateway bridge (dev.to) | Grok Imagine as a generation backend for Claude Code |

Interop note from xAI's own docs (docs.x.ai): Grok Build CLI now reads
Claude Code marketplaces/skills/plugins with zero config — which supersedes
older community threads about manually transplanting .claude/ kits into
Grok custom instructions (repomix packing, ECC discussion #1077).

## Non-coding productivity patterns

- Grok for live X/web research feeding Claude for writing/synthesis —
  both tooled (GrokSearch MCP) and plain copy-paste (substack comments).
- Grok Imagine strictly as a media backend inside Claude-orchestrated
  content pipelines (YouTube automation writeups give Grok only the
  X-engagement/reply lane).
- Three-stage plan→build→refine handoffs for one-off artifacts
  (juliangoldie.com landing-page workflow).

## Read-across to this repo

Our pipeline is an instance of the dominant pattern, arrived at
independently: Fable 5 orchestrating; grok-cli for generation (video,
dialogue, TTS/STT); local GPU models where Grok lacks an API surface;
Remotion owning every number. Worth evaluating from the list:
GrokSearch/x_search MCP for the news vertical (live X sentiment), and
xai-org's plugin if we ever want /delegate-style bulk coding lanes.
