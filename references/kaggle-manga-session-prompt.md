# Handoff prompt — Kaggle × Congress-manga session (written 2026-08-03)

Paste the block below into a fresh session to continue the Kaggle exploration
with the congress-manga product. Context: the local ComfyUI backend was built
2026-08-03 (scripts/comfy/, spec in docs/superpowers/specs/); the owner linked
Kaggle's official MCP the same day (may need an authorize click in the new
session), and no Kaggle API token existed on the machine yet.

---

Continue the Kaggle exploration from 2026-08-03, now with a concrete product:
"Congress Panels" (working title) — a JoJo-inspired manga/comic series that
storytells congressional stock trades from this repo's data engine.

LOAD CONTEXT FIRST
- Congress data layer: scripts/pull_congress.py, pull_congress_stocks.py,
  pull_member_profiles.py (House Clerk PTR ZIP; party/ideology via Voteview
  DW-NOMINATE; policy-area enrichment). Memories: congress-trading-sources,
  social-copy-rules, social-narrative-style.
- Local gen backend (built 2026-08-03, working): scripts/comfy/ —
  ComfyClient.generate() against local ComfyUI on the RTX 4070 Super 12GB;
  installed: Z-Image-Turbo (images, 14s/1024px), Wan 2.2 TI2V-5B + I2V-A14B
  GGUF (video). Spec: docs/superpowers/specs/2026-08-03-comfyui-local-gen-design.md,
  ledger: .superpowers/sdd/2026-08-03-comfyui-local-gen/progress.md.
- Kaggle lane: official MCP server at https://www.kaggle.com/mcp. First step:
  ToolSearch "kaggle" to see if the connector reached this session (owner
  linked it 2026-08-03; may need one authorize click). If absent, fall back to
  the Kaggle CLI — ask the owner to place an API token at
  C:\Users\imadq\.kaggle\kaggle.json (none existed as of 2026-08-03).
  Once connected: inventory the MCP's tools — specifically whether it can
  CREATE/RUN notebooks with GPU, manage datasets/models — and report.

EDITORIAL FORMAT (owner's brief)
- Each episode = one real, freshly detected congressional trade → news-story
  arc (hook → tension → reveal → so-what): trade direction, the member's
  committee/policy leverage over that sector, party-orientation subtext
  (e.g. a pro-tech-industry line softening a China-hawk posture and favoring
  trade), and an honest "does this move matter or not" verdict.
- Style: JoJo-adjacent high-drama manga (poses, speedlines, dramatic panels).
- BINDING RAILS: no first person; attribute to "filings"/"reports"; frame as
  "oversees X, traded X" — never an accusation of wrongdoing; amounts are
  range buckets; label filed vs reported vs rumored; educational, not advice.
  Real members appear as stylized editorial caricatures (public figures,
  parody/commentary) — non-defamatory, with an on-image "parody, based on
  public filings" disclosure.

STUDY BEFORE BUILDING (live web research — models move fast; then brainstorm
per house rules):
1. Base model for manga style, inferable locally on 12GB: compare
   Z-Image-Turbo (installed — check LoRA trainability/ecosystem), the
   SDXL anime lineage (Illustrious-XL / NoobAI class — largest anime LoRA
   ecosystem, cheapest to train/run), Qwen-Image, FLUX-family + style LoRAs.
2. Character-consistency strategy for a recurring cast: per-character LoRA
   vs one series-style LoRA + edit-model identity passes
   (Qwen-Image-Edit-2511 was the Aug-2026 research pick) vs IPAdapter
   (comfyui_ipadapter_plus already installed) — likely hybrid: style LoRA
   for the series + per-character LoRAs only for the recurring main cast.
3. Kaggle LoRA training pipeline: curate character sheets locally → upload
   as Kaggle dataset → training notebook (kohya / ai-toolkit / diffusers —
   pick for T4x2) → pull .safetensors back into
   Documents\ComfyUI\models\loras. Verify current GPU quotas/session limits.
4. Division-of-labor rule: local = interactive panels; Kaggle = training +
   overflow batch renders when the local GPU is busy (owner games on it).
   Design one prompt-spec that renders on either backend.
5. Pilot: pick one real recent filing (hot-topics skill), write the episode
   script under the rails, storyboard, render 3-4 test panels locally,
   and SHOW them in chat as this session's deliverable.

Owner constraints: content is non-commercial (NC weights fine); orchestrator
only on the top model, ALL subagents model:'sonnet'; prefer Workflow-tool
orchestration for the research sweep; verification-before-completion.
