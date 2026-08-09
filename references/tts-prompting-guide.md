# The Chatterbox VO prompting guide — clean, vibrant, professional audio

> Engine: Chatterbox, run locally, fixed seed 1234, one committed reference clip per
> character (`remotion/public/audio/voice_refs/voice_ref_{rex,sol}.wav`), pitch-correction
> optional (`voice_canon.py`, off by default — see §6). Pipeline: `scripts/vector/make_all_vo_local.py`.
> Spoken text is *derived* from the on-screen `line`/`line2` string, so subtitle and audio
> cannot drift apart — but `say_as()` / `say()` / `perform()` in that file are a one-way
> transform layer allowed to change what the MODEL hears without touching what the viewer reads.
>
> Every rule below is checkable by a script or a probe. Where a rule has no script yet, that
> is stated explicitly and it is filed as a TODO, not asserted as house law.

---

## 0. Correction to the prior study — read this first

The handed-in study ranked "a PERFORM tag being partially vocalised" as **low likelihood**
for the stray-leading-consonant defect, based on `leading_burst.py`'s aggregate stat (all
four tags lumped together: tagged lines showed an *equal-or-lower* stray rate than untagged
lines in both episodes tested). That aggregate was the wrong grain to answer the question —
it averages a real effect together with a null one and the null dilutes the real one to
invisibility.

**Verified this session by reading the current (uncommitted) state of
`scripts/vector/make_all_vo_local.py:169-175` and `scripts/vector/tag_ab.py`:** a
tag-by-tag controlled A/B (fixed seed 1234, same line, tag toggled on/off) was run and is
now recorded directly in the source as a dated comment:

> `MEASURED 2026-08-09, controlled A/B at fixed seed (scripts/vector/tag_ab.py): [gasp] and
> [whisper] render as a clean single onset straight into the speech. [sigh] and
> [clear_throat] render as a short burst, then a GAP, then the line — a vocalised artefact
> sitting in FRONT of the words, which is what the owner heard as a stray "T" at the start
> of sentences. [clear_throat] alone adds a full second of it.`

The fix is already applied in `PERFORM` for ep.3: `b01_sol_machine`, `b29_sol_bottomblock`,
`b31_sol_broker`, `b50_sol_fifteen`, `s4_sol_time` had their `[sigh]`/`[clear_throat]` tags
**removed** (comment left in place: `# removed - vocalised artefact at the head`); ep.1 and
ep.2 keep their original tags so their owner-approved audio stays byte-identical. This is
uncommitted local work (`git status` shows `M scripts/vector/make_all_vo_local.py`,
`?? scripts/vector/tag_ab.py`) — verify it is committed before it's lost, but the finding
itself is real and measured, not speculative.

**This promotes hypothesis #1 below from "low" to "confirmed for `[sigh]`/`[clear_throat]`,
cleared for `[gasp]`/`[whisper]`"** — see §5 for the full re-ranked list. Rule 12 in §2 is
updated accordingly: **`[sigh]` and `[clear_throat]` are retired from new scripts.**

---

## 1. What is fixed canon (do not re-litigate)

| Setting | Value | Source |
|---|---|---|
| Seed | `1234`, set via `torch.manual_seed`/`cuda.manual_seed_all`/`np.random.seed` immediately before every `model.generate()` call | `make_all_vo_local.py:339-342` |
| Rex DELIVERY | `exaggeration=0.35, cfg_weight=0.4, temperature=0.7` | `make_all_vo_local.py:154`, chosen by owner from a 4-way A/B (`rex_voice_probe.py`) |
| Sol DELIVERY | `exaggeration=0.5, cfg_weight=0.5, temperature=0.8` (Chatterbox defaults) | `make_all_vo_local.py:155` — never touched, never asked to be |
| Reference clips | one committed `.wav` per character, `remotion/public/audio/voice_refs/` | `make_all_vo_local.py:345` |
| Pitch correction | **off by default**; `--canon` flag re-enables WSOLA correction against `voice_canon.py`'s target f0/rolloff, but costs quality (time-stretch smear) and was only needed to compensate for grok session drift, which local generation doesn't have | `make_all_vo_local.py:364-371` |

Changing a DELIVERY tuple is a **character-level decision** requiring a fresh controlled
A/B at fixed seed (mirror `rex_voice_probe.py`), never a per-line workaround.

---

## 2. Checkable rules for `line`/`line2` text

Each rule states its check. Rules 1-9 are unchanged from the prior study (already
grep/probe-verified against the shipped corpus); rules marked **[REVISED]** were weakened,
tightened, or demoted per the critique; rules marked **[NEW]** close a gap the critique
identified and are implementable as scripts today.

1. **No digits/`%`/`$` in spoken text except calendar years and small day-counts.**
   Numbers, currency, percentages are spelled as words ("two point six billion", "ninety-five
   percent"). *Check:* `grep -E "%|\$" ` over every `line:`/`line2:` string in
   `remotion/src/compositions/*.tsx` must return 0 hits; a digit run not matching `\b(19|20)\d{2}\b`
   (a year) or `\b\d{1,2}\s+days?\b` must return 0.

2. **ALL-CAPS in the script is a writer/screen-only cue.** It is title-cased before reaching
   Chatterbox (`CAPS_TOKEN` regex + `.title()`, `_KEEP={"I","A","OK"}` —
   `make_all_vo_local.py:244-254`). Real emphasis comes from sentence shape, ellipses and
   DELIVERY, not shouting caps. *Check:* none needed beyond rule 3 — this is enforced in code,
   not by writer discipline.

3. **Any institutional initialism in dialogue (SEC, CFTC, FBI, IPO, ETF, FOMC, CEO, CFO...)
   must have an explicit entry in `SPOKEN` or `SAY_AS`, or be added to `_KEEP`** — otherwise it
   silently title-cases into a non-word and the model invents a pronunciation for it. *Check:*
   extract every 2+-letter ALL-CAPS token from `line:`/`line2:`, subtract `_KEEP` and every
   key already covered by `SPOKEN`/`SAY_AS`, and flag any survivor against a hardcoded
   initialism list (SEC, CFTC, FBI, CIA, IPO, ETF, GDP, FOMC, CEO, CFO, ...). **Not yet a
   script — build `scripts/vector/check_initialisms.py`.** This exact gap shipped once
   (`CFTC` in `FairMarketEp2.tsx:354`, never treated).

4. **Ellipses (`…`/`...`) are the pause primitive** — used for comic/dramatic timing (a beat
   before the punchline), not decoration. **[REVISED per critique]** — this had no
   falsifiable spec; give it one: *Check:* an ellipsis-bearing line must sit **immediately
   before a punchline or reveal beat** (the next line in the same speaker's turn, or the
   next speaker's payoff line per rule 6) — not mid-explanation. Budget: **no more than one
   ellipsis-bearing line per 4-5 beats** (ep.1 measured: 1 per ~5 beats). A script can grep
   ellipsis count per episode and flag density above that ratio; it cannot yet judge
   *placement* — that stays an editorial read until a beat-classifier exists.

5. **Words/line: target ~10-11 avg, cap the longest at ~25, at least a fifth of beats ≤6
   words.** *Check:* `scripts/vector/voice_texture.py`, already built — prints avg/longest/%short
   per episode against ep.1's approved profile (10.9/25/21%). Run before recording, not after.

6. **The reacting character gets an echo-move payoff** (repeat the other speaker's word back
   and drop or subvert it), not a lecture. *Check:* no script yet flags this structurally —
   **[NEW, not yet built]** `scripts/vector/echo_move_probe.py`: for each beat, check whether
   a content word (>3 letters, not a stopword) from speaker A's immediately-prior line
   reappears in speaker B's line — this is a necessary-not-sufficient proxy (echo moves reuse
   the word; not every word-reuse is an echo move), so treat a 0% hit rate as a hard fail and
   anything above ~15% of beats (ep.1's measured rate: ~7/38 ≈ 18%) as passing, but confirm
   by reading flagged beats, not by the count alone.

7. **State the topic in one plain sentence within the first 3-4 beats.** **[REVISED per
   critique — demoted from rule to hypothesis.]** The prior study's own justification
   admitted this is "inferred... not confirmed... a hypothesis to test," yet it sat in the
   numbered rules list beside grep-verified items. Moved to §4 (structural hypotheses) below.
   It is not asserted as house law until a beat-position scan is run and shows ep.1 clears a
   threshold that ep.3-5's rejected drafts miss.

8. **Reserve `!`/`?!` for genuine surprise; not every line ends in one.** **[REVISED per
   critique]** — the prior "why" undercut the rule: the actual fix for Rex's yelping was a
   DELIVERY retune (exaggeration/cfg_weight/temperature), not a punctuation rewrite. Keep the
   rule but correct its causal claim: *punctuation and DELIVERY compound, they don't
   substitute for each other* — heavy `!`/`?!` density on top of expressive DELIVERY settings
   makes yelping worse; on calmer DELIVERY (Rex's current tuple) it's lower-risk but still
   worth budgeting. *Check:* count `!`/`?!` as a fraction of a character's lines per episode;
   flag if a character exceeds ~70% (ep.1 Rex's ep.1-era rate, the one the owner called
   "too high, like a child" **before** the DELIVERY fix — treat this as an upper bound, not a
   target). **Not yet scripted** — add a counter to `voice_texture.py`.

9. **No stage directions/markdown/bracketed tokens in `line`/`line2` other than the four
   proven PERFORM tags.** Smart quotes are silently *stripped to nothing*, not converted
   (`make_all_vo_local.py:108-110` unicode-normalisation table only maps em-dash, ellipsis,
   and curly quotes — anything else falls through raw to the model). *Check:* grep every
   `line:`/`line2:` string for `[^\x00-\x7F]` minus the known-safe set `{…, —, ', ', ", "}`
   and for any `[...]` bracket token not in `{sigh, clear_throat, whisper, gasp}` — **not yet
   scripted**, straightforward to add as a lint on the same regex `LINE_RE` already used to
   parse the compositions.

10. **Contractions are the norm** ("that's", "doesn't", "it's") — formalized written-report
    English is a measured defect (cited as one of three causes of ep.3's "reads as narration"
    complaint). *Check:* contraction rate per episode (count `'` inside word-boundary tokens
    ÷ total lines) — **not yet scripted**, add to `voice_texture.py`.

11. **PERFORM tag budget: ~a fifth to a third of lines, one tag per line, trailing space
    baked into the dict value, never on back-to-back lines from the same character.** *Check:*
    `voice_texture.py` prints `tagged/n`; the back-to-back constraint needs a positional check
    — **not yet scripted**, add: walk `BEATS` in file order, flag any two consecutive beats
    from the same `speaker` where both `vo` stems are in `PERFORM`.

12. **[REVISED — this is the load-bearing update from §0] Only `[gasp]` and `[whisper]` are
    approved for new lines.** `[sigh]` and `[clear_throat]` are retired — confirmed by
    `tag_ab.py`'s controlled A/B to render as burst-then-gap-then-speech, the measured shape
    of the owner's "stray T" complaint. `[laughter]` and `[UM]` remain unused (no audible
    change, per the original probe). *Check:* `scripts/vector/check_perform_tags.py`
    (**not yet built** — one line: assert no `PERFORM` value contains `sigh` or
    `clear_throat`).

13. **Any `SPOKEN`/`SAY_AS` override is exact-string-keyed and must be re-verified on
    rewrite** — it does not carry over by resemblance. *Check:* the source comment states
    this is exactly how "HA!" broke in ep.3 (matched none of ep.1's entries, shipped as
    "aitch-ay", commit `e3afcdc`). No automated check possible for "does this new HA! line
    need an override" other than running `detect_spelled.py`/`onset_probe.py` on the fresh
    render before it ships (§5).

---

## 3. Structural rules the critique found missing

The critique correctly identified that every rule above operates at the line/beat level,
while "boring," "lectures," "ambiguous," and "not smooth" are complaints about the *shape of
the episode*. None of these have scripts yet; each is written here with a concrete,
buildable check so they stop being vibes.

- **Turn-taking cap.** A speaker holding the floor for many consecutive short beats still
  reads as a monologue even if each beat individually passes the word-count rule (rule 5).
  *Proposed check:* `scripts/vector/turn_taking_probe.py` — walk `BEATS`, count the longest
  run of consecutive beats from one `speaker`; flag runs >3 (ep.1's approved max — verify by
  running once ep.1 is measured, don't assume the number).
- **Stakes-clarity.** No rule requires the two characters' opposing positions to be stated
  before the debate proceeds (what Rex wrongly believes vs. what Sol is about to correct).
  *Proposed check:* not mechanically checkable by regex — this needs a human/LLM
  classification pass (does beat ≤4 contain a claim attributable to speaker A and a
  contradiction attributable to speaker B?), logged as a manual gate in the script-review
  checklist, not a probe.
- **Transition motivation.** The echo-move check (rule 6) only tests joke beats; the same
  connective-tissue idea — the next line reacts to a word/claim in the previous line rather
  than jump-cutting to a new fact — is what would make topic transitions read as
  conversation. *Proposed check:* generalize `echo_move_probe.py` (rule 6) to run on every
  adjacent beat pair, not just reaction beats, and report the corpus-wide word-carry-over
  rate as a diagnostic (not yet a pass/fail threshold — establish ep.1's baseline first).
- **Topic stated early** (formerly rule 7) — belongs here, not in §2, until a beat-position
  scan of ep.1 vs. the rejected ep.3-5 drafts is actually run and produces a number.
  *Proposed check:* scan the first 4 beats of each episode for a declarative sentence not
  tied to an in-universe event noun (a generalization of the "let me tell you about the
  so-called fair market" pattern) — needs a small keyword/POS heuristic, not pure regex; file
  as a probe to build before asserting this as a rule again.
- **Joke density/spacing/escalation.** Only the echo move is validated. Rule-of-three
  escalation, per-character comic register, and joke spacing across an episode are
  unmeasured. No proposed check yet — flagged as an open gap, not invented here.

---

## 4. The stray-leading-"T" — ranked hypotheses with exact experiments

Ranked by current evidence, strongest first. Re-ranked from the handed-in study using the
finer-grained `tag_ab.py` result found this session (§0).

### 1. PERFORM tag partially vocalised — **CONFIRMED for `[sigh]`/`[clear_throat]`, CLEARED for `[gasp]`/`[whisper]`**
- **Evidence:** `scripts/vector/tag_ab.py` — same text, same seed (1234), tag toggled on/off,
  four cases (`clear_throat`/sol, `sigh`/sol, `whisper`/sol, `gasp`/rex). Result recorded in
  `make_all_vo_local.py:169-175`: `[sigh]`/`[clear_throat]` render as burst-then-gap-then-speech
  (a vocalised fragment in front of the words); `[gasp]`/`[whisper]` render as a clean single
  onset.
- **Why the earlier aggregate test (`leading_burst.py`) missed it:** it lumped all four tags
  into one "tagged" bucket per episode. Two of the four tags are clean and two are not; averaged
  together the effect washes out to "equal or lower than untagged," which is what the prior
  study measured and correctly reported as weak evidence *for that test*. The lesson: when a
  suspected cause is categorical (tag X vs tag Y), test per-category before trusting an
  aggregate.
- **Action taken (uncommitted, verify before losing):** `[sigh]`/`[clear_throat]` removed from
  ep.3's `PERFORM` dict; ep.1/ep.2 left untouched (approved audio, don't regenerate).
- **Remaining falsification step:** rerun `leading_burst.py` on ep.3 audio regenerated with the
  new `PERFORM` dict — the stray-onset rate on the (now `[gasp]`/`[whisper]`-only) tagged
  subset should drop toward the clean untagged baseline. **Not yet run — the audio for
  ep.3 hasn't been regenerated with this dict change.**

### 2. Content-agnostic cold-start bleed from the reference clip — medium, untested
- **Hypothesis:** the first ~100-300ms of any Chatterbox zero-shot generation is the region
  least conditioned on the text, independent of tags.
- **Experiment (unrun):** take the untagged lines `leading_burst.py` already flagged this
  session (ep.1: `a3_sol_speaker`, `v12_rex_both`, `a2_rex_six`, `a2_sol_edge`,
  `a5_rex_dowhat`, `a7_rex_oilthing`; Bubbles: `b20_sol_partthree`, `b21_rex_crowbar`,
  `b29_sol_bottomblock`, `b41_sol_witht`, `b49_rex_fifteen`, `b50_sol_fifteen`) and regenerate
  each at the same seed/DELIVERY against an alternate reference clip. If the stray onset
  moves/weakens/disappears with the reference clip while text+seed stay fixed, confirmed;
  if identical, killed.
- **Note:** now a lower-priority test than before hypothesis 1 was confirmed — some of these
  flagged untagged lines may simply be genuine word-initial obstruents (hypothesis 3).

### 3. Genuine word-initial obstruent acoustics (false positive on the detector, not a defect) — medium
- **Evidence so far:** of 12 untagged flagged lines measured this session, first letters split
  T:3, S:2, W:2, F:2, B:1, P:1, L:1 — T/Th-initial is the largest cluster but not a majority.
- **Experiment (unrun):** synthesize a minimal-pair phoneme sweep at shipping DELIVERY/seed —
  "Time.", "Pie.", "Cot.", "Sea.", "We.", "Bee.", "Fifteen." — run `leading_burst.py`'s
  `stray()` detector on each. If only voiceless-stop-initial words (Time/Pie/Cot) flag, this is
  confirmed and the fix is editorial (avoid/soften T/P/K-initial line openers) rather than a
  pipeline bug.

### 4. Title-casing rule mishandling a bare capital next to punctuation (e.g. "T-bill") — low
- **Static check (run this session):** grepped every `line:`/`line2:` string for `T[+-]` and
  for any line whose first token is a bare capital letter — zero matches. Mechanically real as
  a latent risk (`CAPS_TOKEN` requires 2+ uppercase letters, so a bare "T" sails through
  untouched) but not present in the current corpus, so it cannot be the cause of the *current*
  complaint.
- **Action:** add the grep as a permanent pre-VO check (folds into rule 9's lint); separately
  generate "T-bill." with and without a `SPOKEN` override once, to confirm the failure mode is
  real before treating it as an active risk.

### 5. An intentional spoken "T" bleeding across an edit boundary — low
- **Evidence:** two lines deliberately embed a spoken letter "T" mid-sentence — "Trillion? With
  a T?" (`Bubbles.tsx:472`) and "With a T, kid." (stem `b41_sol_witht`, itself flagged by
  `leading_burst.py`). This is a real, intentional "T" in the finished audio — just not at a
  sentence head and not a synthesis artifact.
- **Experiment (unrun, and no script can do it):** human listens to `b41_sol_witht` in context
  and confirms whether the complaint is this joke bleeding into an adjacent beat during
  playback/retiming (an editing-timing question) rather than a synthesis defect. No probe in
  this repo does perceptual/blind listening — flagged as a permanent gap (§5).

---

## 5. Automated detection — catch a bad read before a render ships, not after the owner hears it

| Detector | What it catches | Command |
|---|---|---|
| `scripts/vector/detect_spelled.py [b\|s\|1\|2]` | Any line where `seconds/syllable` > 1.5x the episode median, or that contains a short (≤4-letter) ALL-CAPS token — the "aitch-ay" defect. Writes `data/bubbles/spelled_<ep>.json`. | `python scripts/vector/detect_spelled.py b` |
| `scripts/vector/onset_probe.py <wav...>` | Counts energy onsets in the first 1s and compares against the owner-approved reference ("Hah! ...Fundamentals." = 1 onset per real word). 3 onsets where 1 is expected = spelled out letter-by-letter. | `python scripts/vector/onset_probe.py content/probe/x.wav` |
| `scripts/vector/leading_burst.py [b\|s\|1]` | Splits an episode's rendered lines into PERFORM-tagged vs untagged and reports the % showing burst-then-gap-then-speech at the head — **run per-tag, not just per tagged/untagged bucket, per §0's correction**. | `python scripts/vector/leading_burst.py b` |
| `scripts/vector/tag_ab.py` | Regenerates one fixed line with/without its PERFORM tag at fixed seed 1234 — the correct falsification tool for "does *this specific tag* cause artifact X." Writes `content/probe/tag_ab/`. | `chatterbox-venv/Scripts/python.exe scripts/vector/tag_ab.py` |
| `scripts/vector/voice_texture.py` | Scores a script (words/line, ALL-CAPS/beat, ellipsis count, %short lines, PERFORM-tag count) against ep.1's approved profile **before a single line is recorded**. | `python scripts/vector/voice_texture.py` |

### Gate order (run before render, cheapest first)

1. **Script-level, pre-recording** (no audio needed): `voice_texture.py` against ep.1's
   profile; the rule-9 bracket/unicode lint; the rule-3 initialism check (once built); the
   rule-12 `[sigh]`/`[clear_throat]` assertion (once built).
2. **Audio-level, post-recording, pre-mux**: `detect_spelled.py` on the freshly rendered `.wav`
   set; `leading_burst.py` per-tag; `onset_probe.py` on any line touching a new `SAY_AS`/`SPOKEN`
   override or a fresh PERFORM tag placement.
3. **Perceptual gap (not automatable today):** nothing in this repo does blind/perceptual
   listening. Every "flagged" result above is a *lead for a human listener*, not a confirmed
   defect, until someone actually opens the specific `.wav` and labels it. Treat this as
   permanent — envelope-shape detectors can be fooled by legitimate acoustic variation
   (hypothesis 3 in §4), so a human pass on flagged lines stays in the loop.

### New checks this guide proposes but that don't exist yet (build before next episode)

- `scripts/vector/check_initialisms.py` (rule 3)
- `scripts/vector/check_perform_tags.py` (rule 12 — one-line assertion, cheapest to add first)
- Bracket/unicode lint folded into an existing parser (rule 9)
- Contraction-rate + `!`/`?!`-density counters added to `voice_texture.py` (rules 8, 10)
- `scripts/vector/turn_taking_probe.py` (§3)
- `scripts/vector/echo_move_probe.py`, generalized to all adjacent beats for the
  transition-motivation diagnostic (rule 6, §3)

---

## 6. Quick reference — the full spoken-text transform chain

For any line, the text the model actually receives is:

```
perform(stem, say(stem, say_as(text)))
```

i.e. `say_as()` (SAY_AS table substitutions) → `say()` (SPOKEN override, else CAPS_TOKEN
title-casing) → `perform()` (PERFORM tag prefix, if any). All three are one-way: they can
change what Chatterbox hears without ever touching the `line`/`line2` string the viewer reads
on screen. When writing new dialogue, assume nothing downstream of the raw string is visible
to you unless you check these three tables — that invisibility is exactly how CFTC and "HA!"
shipped untreated twice.
