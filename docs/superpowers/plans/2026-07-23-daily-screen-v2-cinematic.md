# The Daily Screen v2 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use `- [ ]`.

**Goal:** hero-image spine + shocking factual intro + dedicated company carousel slide, built into the daily pipeline; showcase on WKEY.

**Architecture:** new `heroes.py` resolver + committed hero assets (placeholder-first); Remotion `HeroLayer`; `daily_copy` dramatize + intro rewrite + `lint_editorial`; a 4th carousel slide via `_build_v4`'s existing `hero_map`. `halal-reels/` untouched.

**Tech:** Python+pytest, Remotion 4+zod+TS, Chatterbox/whisper (unchanged), Higgsfield (heroes, separate step).

**Spec:** docs/superpowers/specs/2026-07-23-daily-screen-v2-cinematic-design.md

## Global Constraints
- Rails: screen phrasing only (never "is halal/haram"); footer `Computed methodology result — not a fatwa · not financial advice`; spoken `Educational, not financial or religious advice.`; never name the data vendor; "a read, not a call"; no signals/returns.
- NEW banned-word gate `lint_editorial` bans: dangerous, danger, trap, too much, overvalued, avoid, risky, terrible, crash, plummet, soar, guaranteed (case-insensitive, word-bounded).
- Verdict withheld: stamp second-to-last; NO pass/fail/review in pre-stamp VO — dramatize copy must respect this (use "under the limit"/"past the line", never "fails/passes").
- A and B props differ ONLY in beats[0] and vo[0].
- Hero assets committed at `remotion/public/heroes/<layer>.jpg` (+ `_default.jpg`); placeholder-first so nothing blocks on Higgsfield.
- Python: `cd scripts && python -m pytest -q` (baseline: 1 pre-existing `test_export_halal.py` failure, unrelated — expect it, nothing else). Remotion: `cd remotion && npx tsc --noEmit`.
- All subagents on Sonnet. Commit trailer `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`. Branch feat/multi-sector-research-platform; no push until the controller says.

---

### Task 1: Hero resolver + placeholder assets + provenance manifest

**Files:** Create `scripts/aiinvest/heroes.py`, `scripts/tests/test_heroes.py`, `remotion/public/heroes/<layer>.jpg` ×8 + `_default.jpg`, `data/heroes/manifest.json`. Modify `.gitignore` (ensure `remotion/public/heroes/` is NOT ignored — it's committed brand assets; `remotion/public/daily/` stays ignored).

**Interfaces (produces):**
- `heroes.LAYER_HEROES: dict[str,str]` — the 8 live layer values → `"heroes/<layer>.jpg"`. Layer values (from live bundle): `L0-energy, L1-chips, L2-infra, L4-application, Q1-hardware, Q3-software, Q5-applications, Q4-security`.
- `heroes.hero_for_layer(layer: str|None) -> str` — returns `LAYER_HEROES[layer]` or `"heroes/_default.jpg"`. Pure. Path is staticFile-relative (no leading slash).
- `heroes.hero_abs_path(layer, remotion_public_dir) -> pathlib.Path` — resolves to the on-disk file (for carousel/daily_post copy steps).

- [ ] Step 1: failing tests — `hero_for_layer("Q4-security")=="heroes/Q4-security.jpg"`; unknown/None → `"heroes/_default.jpg"`; every path in `LAYER_HEROES` values + `_default` exists under `remotion/public/`.
- [ ] Step 2: run → fail.
- [ ] Step 3: implement `heroes.py`. Generate the 9 placeholder JPGs (1080×1920) with a small one-off script — try Pillow (`from PIL import Image`); write a solid near-black `#0A0D12` frame with a faint layer-tinted radial (tint per layer from a small map; `_default` = amber). If Pillow is unavailable, install it into the repo python (`pip install pillow`) — it's a dev-time asset generator, allowed. Write `data/heroes/manifest.json` = `{"<layer>": {"source":"placeholder","style":null,"generated_at":null,"prompt":null}, ...}` for all 8 + `_default`.
- [ ] Step 4: run → pass; full suite.
- [ ] Step 5: commit `feat(heroes): layer→hero resolver + placeholder brand assets + provenance manifest`.

---

### Task 2: Remotion HeroLayer + `heroSrc` prop

**Files:** Modify `remotion/src/slides/slideProps.ts`, `remotion/src/compositions/SlideStoryReel.tsx`.

**Interfaces:** consumes `heroSrc` (staticFile-relative like `"heroes/Q4-security.jpg"`); Task 3 sets it on props.

- [ ] Step 1: add `heroSrc: z.string().optional()` to `slideStoryPropsSchema`; `npx tsc --noEmit` clean (additive).
- [ ] Step 2: read `SlideStoryReel.tsx` fully. Add a `HeroLayer` rendered BEHIND beat content and the `Bg` motes, only when `heroSrc` present. Behavior via `useCurrentFrame()`+`useVideoConfig()`:
  - Frames within the first (hook) beat's span [0, beats[0].durationInFrames): hero at opacity ~0.92 full-bleed (`<Img src={staticFile(heroSrc)} style={{objectFit:'cover',width,height}}/>`) under a scrim `linear-gradient(180deg, #0A0D1200 0%, #0A0D12CC 62%, #0A0D12 100%)` so headline/sub stay legible.
  - After the hook beat: opacity eases to ~0.14, `filter: blur(6px)`, staying as a dim backdrop.
  - Slow scale 1.0→1.06 across the whole reel (Ken-Burns), deterministic.
  Use the theme's `C.bg` for the scrim color. Keep `<Bg>` mounted above the hero.
- [ ] Step 3: `npx tsc --noEmit` clean. Regression: render 60 frames of `src/fixtures/wulf_slides.json` (no heroSrc) — unchanged, no errors; then a scratchpad copy of it with `"heroSrc":"heroes/_default.jpg"` — renders with the hero visible on the hook; delete MP4s. Report what you saw.
- [ ] Step 4: commit `feat(remotion): HeroLayer — full-bleed hook, dimmed backdrop after`.

---

### Task 3: `daily_copy` dramatize + shocking intro + `lint_editorial` + `company_def`

**Files:** Modify `scripts/aiinvest/halal_lint.py`, `scripts/aiinvest/daily_copy.py`, `scripts/aiinvest/kit_md.py`; tests `scripts/tests/test_halal_lint.py`, `scripts/tests/test_daily_copy.py`.

**Interfaces:**
- `halal_lint.lint_editorial(lines: list[str]) -> list[str]` — one violation per line containing a banned judgment word (word-bounded, case-insensitive; list in Global Constraints).
- `daily_copy.dramatize(card: dict) -> str` — factual-extreme line from the binding standard row (`card["standards_rows"]`, pick the min-margin numeric row = the binding one). Severity from `ratio/threshold`:
  - mult ≥ 3 → `"It owes {mult:.1f} times what the whole company is worth — the screen's ceiling is {threshold:.0f}%, and it isn't close."` (only valid for a mcap-relative debt row; detect via row label containing "mcap"/"market"/"cap")
  - 1 < mult < 3 → `"Its {label} sits at {ratio} — past the {threshold} line."`
  - else (pass/under) → `"Every debt line lands under the limit."`
  Must contain a `$`/%/limit anchor (pass `lint_visceral`) and NO banned word and NO pass/fail/review token.
- `daily_copy.build_daily(...)` additions: props gain `heroSrc = heroes.hero_for_layer(verdict.get("layer"))`; `vo[0]`/hook rewrite = `"{TICKER} — {descriptor}. But here's the shock: {dramatize}"` (variant A) and the contrarian B keeps its hook but ALSO drops the double-ticker; `beats[0].sub` = descriptor, plus carry the dramatize line for the hero shock sub (add to the hook beat as a new field the composition already tolerates, or fold into sub two-line). `kit_fields["company_def"]` = the descriptor sentence. Run `lint_editorial` + existing lints as hard gate.
- `kit_md.parse_cfg` gains `"company_def"`.

- [ ] Step 1: failing tests — lint_editorial flags "this is dangerous leverage"/"a debt trap", passes the factual-extreme WKEY line; dramatize on WKEY (561% mcap, 30% limit) yields a ≥3× "owes 5.x times" line with no banned word and no pass/fail/review; heroSrc on WKEY props == "heroes/Q4-security.jpg"; company_def in kit_fields; A/B still differ only beats[0]/vo[0]; 128-ticker sweep stays lint-clean under ALL lints incl. editorial; verdict-withheld holds.
- [ ] Step 2: run → fail.
- [ ] Step 3: implement (import `from aiinvest import heroes`). Keep pure.
- [ ] Step 4: run → pass; full suite.
- [ ] Step 5: commit `feat(daily): dramatize shock intro + editorial-word guard + hero + company_def kit`.

---

### Task 4: Carousel company-definition slide + `daily_post` wiring

**Files:** Modify `higgs/_build_v4.py`, `scripts/daily_post.py`; tests `scripts/tests/test_daily_post.py` (+ a `_build_v4` unit test if a test file exists — else a scratchpad smoke).

**Interfaces:** consumes `company_def` kit field (Task 3) + layer hero (Task 1).

- [ ] Step 1: read `_build_v4.py` `build_slides`/`build_halal_frames`/`header`/`_screen_body` fully. Add a **define slide** as the FIRST slide when `company_def` is present in the parsed kit for the ticker: big ticker + exchange (reuse `header`), the `company_def` descriptor, a one-line leverage teaser (from `screen_head` or a short derived line), hero image as full-bleed background with a dark scrim. Backward-compat: when `company_def` absent (the old July-21 kits), slide set is unchanged (3 slides) — gate on the field.
- [ ] Step 2: `daily_post.py` — `build_kit_md` includes a `company_def:` line from `copy_result["kit_fields"]["company_def"]`; the carousel step resolves `heroes.hero_abs_path(layer, remotion_public_dir)` and passes it into `_build_v4`'s `hero_map` for the ticker (copy the layer hero to wherever `_build_v4` expects hero files, or pass the path — follow `_build_v4`'s hero_map contract you read in Step 1). Degrade gracefully (existing carousel_note path) if the hero file is missing.
- [ ] Step 3: tests — `build_kit_md` output round-trips `company_def` through `kit_md.parse_cfg`; daily_post helper tests still green. Scratchpad smoke: build the WKEY kit md + run `_build_v4` main for WKEY → 4 PNGs, first is the define slide (open it, confirm ticker+descriptor+hero visible); delete PNGs. (Use existing placeholder hero.)
- [ ] Step 4: full suite; commit `feat(carousel): dedicated company-definition slide + layer hero wiring`.

---

### Task 5 (controller-driven, NOT an SDD subagent): hero generation via Workflow
After T1–T4 land: controller presents 2 Higgsfield style directions to the owner (two-suggestions rule), then a Workflow fan-out generates the ≥7 layer heroes in the chosen style, quality-checks each (on-theme? legible with scrim? no text artifacts?), and overwrites `remotion/public/heroes/<layer>.jpg` + updates `data/heroes/manifest.json`. Commit the real assets.

### Task 6 (controller-driven): WKEY showcase + verify
Regenerate `python daily_post.py --ticker WKEY --skip-refresh`; verify stills: hero full-bleed on the shocking intro, dimmed backdrop on data beats, 4-slide carousel with define slide, sync intact, no editorial words, disclaimer present. Report to owner.

## Self-Review
1. Spec coverage: hero library → T1+T5; reel hero → T2; shock intro+dramatize+editorial guard → T3; company slide → T4; showcase → T6; rails+withheld → constraints+T3 tests. 2. No placeholders in briefs — T1/T4 direct the implementer to read the in-tree hero_map/_build_v4 contract, exact strings/tiers spelled out. 3. Types: `heroSrc` string consistent T1→T2→T3; `company_def` consistent T3→T4; dramatize returns str used in vo[0].
