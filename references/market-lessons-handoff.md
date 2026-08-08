# Market Lessons with Sol — handoff

**Written 2026-08-08.** State of the five-episode series, what is decided,
what is broken, and what to do next. Read this before touching the
episodes; several things below were learned by getting them wrong, and
the notes exist so the next session does not repeat the cost.

---

## 1. Where the series actually is

Five episodes exist, all in the **round-desk panel format** (video wall
behind, cast seated, curved news crawl over the table). All render clean.

| ep | runtime | state |
|----|---------|-------|
| 1 | 3:16 | **owner-confirmed** pacing/script · voice v3 · 12 animated wall exhibits · SFX wired |
| 2 | 2:30 | **owner-confirmed** pacing/script · voice v3 |
| 3 | 2:47 | panel format + reaction cuts · **script rejected** |
| 4 | 2:20 | panel format + reaction cuts · **script rejected** |
| 5 | 2:22 | panel format + reaction cuts · **script rejected** |

Masters: `content/probe/ep{1..5}_panel.mp4` (CRF 19), previews alongside
as `_preview.mp4` (720×1280, CRF 27, under the 30 MB chat cap).

Delivery is via Higgsfield **storage only** — upload, confirm, post the
CloudFront link. Never Higgsfield *generation* (owner stopped paying for
it). Never push media to git.

---

## 2. Decisions the owner has already made — do not re-litigate

- **Rex's delivery = setting "B"** (Chatterbox `exaggeration 0.35,
  cfg_weight 0.4, temperature 0.7`). Chosen from a 4-way A/B.
- **Performance tags: weave them in.** 13 placed across ep.1/ep.2.
- **Wall content = hybrid.** Generated art for objects and concepts;
  code-drawn for every number, chart and label. A generated image may
  never carry a figure.
- **Ep.1 + ep.2 get the full treatment first**, owner approves, and only
  then does the same recipe go to 3–5.
- **Ep.3–5 need a full script rewrite**, not a re-time. Measured: they are
  46–49% silent against ep.1/ep.2's 25–28%. The dead air is padding thin
  scripts to length, so a rewrite will make them LONGER, not shorter.
- **Rig acting stays off.** `RIG_OFF = true` in all five. The owner judged
  character body-motion worse than stillness. Do not re-enable unasked.
- **Content is non-commercial**, which is what permits the meme SFX below.

### The stingmap is the authority on sound (2026-08-08)

`scripts/audio/stingmap.json` is canonical for every sting in the series.
It caps density at **≤3 scored stings per minute**, fixes the volume band
at **0.24–0.34**, allows **one sting per beat**, and names three kinds of
beat that must be **silent** — including, on compliance grounds, any line
stating a real named person's specific disclosed trade or timing.

This session learned the hard way that it outranks a passing instruction.
Asked for "more transition audio", an earlier pass put a transition on
nearly every beat: ~12 stings/min, hold beats at 0.15 (below the floor),
two sounds on one beat, and a sting on *"July 2022. The Speaker's
household sold NVIDIA…"* — the exact line the map names as silence-only.
`scripts/audio/score_from_stingmap.py` now scores the episode from the map
and is the only thing that should place a sting. Ep.1 sits at 10 stings,
3.06/min, zero violations.

Two frictions worth knowing:

- **The spec contradicts itself slightly.** Its taxonomy explicitly
  assigns stings to beats 299/393 and 2537, which are consecutive, and
  10 entries over a 3.27-minute runtime is 3.06/min against a stated cap
  of 3. The taxonomy entries are specific and reasoned, so they were
  followed and the overage flagged rather than silently dropping a sting
  the spec asks for. **Owner call needed** if the cap is meant to be hard.
- **Motion foley is not a sting.** `sfx_whip` on a head turn, `sfx_poof`
  on a vanish and `sfx_pop` are anchored to drawings under §10.8 and are
  deliberately left alone by the scorer.

### Still waiting on the owner

- **Music bed** — built for all five, demoed on ep.2, never approved and
  never wired. `scripts/audio/mux_bed.py` applies it to a finished master
  in seconds with no re-render, so approval is cheap to act on.
- **Whether to continue the JoJo art direction** (see §4).

---

## 3. Open defects, in priority order

1. ~~**Two ep.1 exhibits never appear.**~~ **FIXED 2026-08-08.** Both
   beats declared an `exhibit` *and* a `tvPose`, and the wall's content
   chain tested `tvPose` first, so the caricature won and the exhibit had
   nowhere to land. The obvious fix — reorder the branches so `exhibit`
   wins — was **rejected**: `congress2_*` appears on these two beats and
   nowhere else in the episode, so making the exhibit authoritative would
   have deleted the second politician caricature outright, and the beat's
   own comment says that archetype is why the line is worded as it is.
   Instead each beat now **opens on the caricature and cuts to its
   exhibit**: beat 1301's second shot dropped its `tvPose`, and the plate's
   clock starts at that cut (`exhibitFrom` in `FairMarketEp1.tsx`) so it
   does not enter half-animated. `WallFrame`'s glow was made beat-scoped at
   the same time, or it would blink off at the cut.

2. ~~**The "45 DAYS" callout is unreadable.**~~ **FIXED 2026-08-08.** The
   label was bare SVG `<text>` in pale mint with nothing behind it. It is
   now an HTML element on a dark plate with an accent border — HTML rather
   than `<text>` so the plate sizes itself to the string instead of
   guessing Impact's metrics, and it flips below the ring if there is no
   room above. Same fix covers "THE DEAL" on `deal_handshake`.

3. ~~**Eight wall exhibits need regenerating.**~~ **DONE 2026-08-08**, and
   the art direction changed while doing it — see §4.

4. *(cosmetic, pre-existing, owner already approved the episode)* ep.1
   beat 123 reports one marginal off-frame in the staging audit: Rex's
   shoulder crops 32px at k=1.14.

5. **`chip_gavel` is wired to no beat.** It is the twelfth card and no
   composition references it. Either give it a beat or drop it.

---

## 4. The art-direction state, and the trap in it

The owner asked for **JoJo-style caricatures** on the wall — "politicians
and big corpo shaking hands, combining political and economic ambitions" —
with **restrained colour** ("not too much aggressive").

A workflow authored and adversarially gated 12 prompt cards; they are saved
at `remotion/public/characters/cast_ep1/exhibits/_cards.json` and are
**good work worth reusing**. The generation that followed split hard:

- **The 4 routed to Z-Image came back excellent** (`calendar_late`,
  `index_basket`, `oil_tanker_strait`, `two_podiums`) — consistent,
  readable, restrained palette. These are on disk and ship as-is.
- **The 8 routed to Illustrious-XL all failed.** Subjects unreadable
  (`chip_gavel` a blob, `deal_handshake` one man and no handshake), the
  palette collapsed to sepia, and two — `copy_homework`, `watching_chart` —
  came back with **garbled Japanese lettering baked across the frame**
  despite the negative prompt forbidding text.

**Currently on disk, `exhibits/` holds the 8 broken JoJo images.** The
earlier flat-vector set that IS in the shipped ep.1 render was overwritten.
Regenerate before re-rendering ep.1, or the wall will show the failures.

### The routing rule — applied 2026-08-08, and what it actually took

Everything now goes to **Z-Image**. Rerouting alone was **not enough**: the
two models want different *prompt grammar*. Illustrious is SDXL and eats
danbooru tag soup (`1man, solo, dark navy suit, ...`); Z-Image Turbo is
driven by a **Qwen-3-4B text encoder** and wants flowing prose. The eight
cards were rewritten as prose (the tag versions are kept on each card as
`prompt_illustrious_orig`), which fixed the mush.

That produced a second, sharper failure, and it is the important one.
A visual gate on the actual pixels returned **5 fail / 2 borderline /
1 pass**, and **four of the five failures were the same defect: the figure
had become a recognisable Jotaro Kujo** — pompadour, popped gakuran
collar, peaked cap, star earring.

The cause is structural. "JoJo's Bizarre Adventure" is load-bearing for
the style and cannot be dropped. But an **unnamed "generic adult man"
leaves an identity vacuum**, and the style tag fills it with the
franchise's most famous character. Piling on negative tokens does not
help. Every human figure needs an identity of its own:

- a **named real politician**, drawn as caricature (see §4a); or
- an ordinary person pinned down by concrete, un-JoJo specifics — "short
  neatly combed hair", "an ordinary flat shirt collar"; or
- **no face at all** — a back-turned silhouette, with an *object* as the
  subject. Z-Image draws symbolic still life extremely well, and the two
  strongest exhibits in the set (`capitol_ticker`, `options_leverage`) are
  both object-forward with a tiny figure for scale.

The prompt-only gate could not have caught any of this: it reviewed
**prompts**, not **images**. `scripts/vector/contact_sheet.py` +
a sonnet fan-out reading the PNGs is now the required last step of any art
pass. It is worth its cost — it caught the Jotaro drift, a legible
numeral, and a white matte border that all read as "fine" in the prompt.

**Do not obey that gate blindly, though.** On the second run it started
enforcing prompt-literalism and rules the owner has since overridden: it
failed `deal_handshake` for "naturalistic colour" when a recognisable
Trump *requires* a red tie and skin tones, and failed `watching_chart`
because the bars did not rise monotonically — which for a price chart is
correct and desirable. Treat it as a very good reviewer with no editorial
authority.

---

## 4a. Real politicians (owner decision, 2026-08-08)

The owner's instruction: *"it should be caricatures of real politicians in
jojo style."* This **supersedes** the older rail written into
`scripts/vector/gen_congress.py`, which deliberately said the figures were
"a generic senior-lawmaker ARCHETYPE … not a likeness of any named
individual". That older rail is now wrong for new work; the docstring
should be corrected the next time that file is touched.

What stays: caricature (never a likeness presented as a photograph), **no
on-screen name**, no accusation, and the parody / public-record /
educational footer on every frame. The ranking exhibit is staged as
"people watch these disclosures", never as a claim about whose returns
were best.

Casting used in ep.1: **Trump** on `deal_handshake` (the owner's original
brief — "politicians and big corpo shaking hands"), **Pelosi** on
`leaderboard_suits` (the episode's own "Speaker's household" line).
`committee_room` was deliberately **left as a faceless authority figure**:
it passed its gate, and a president behind a *congressional committee*
dais is a factual mismatch the script explicitly guards against.

## 4b. The arcade-fighter direction (open, owner asked)

Looking at the politician probes, the owner noted they read like **arcade
games** rather than JoJo, and asked whether that could be used
deliberately — arcade movement to land jokes and opinions. Three probes
are in `exhibits/_probe/` (`arc_select`, `arc_versus`, `arc_stance`) via
`scripts/vector/arcade_probe.py`. It is a genuinely strong fit and solves
three things this repo keeps paying for:

- **Numbers.** An arcade HUD — health bar, timer, score, combo counter, VS
  plate — is a *code layer by nature*. The art becomes stage and fighters;
  Remotion draws the whole interface on top, sharp and correct. That is
  the house rule rather than a workaround for it.
- **IP leak.** "1990s arcade fighting game" is a **genre, not one
  rights-holder's character**, so the style anchor does not arrive with a
  person attached. This is the direct cure for the Jotaro drift above.
- **Motion.** The house animation rules in §10.8 of `CLAUDE.md` already
  *are* sprite rules — anticipation, volume-preserving squash/stretch,
  2-frame smears, three-beat holds. Arcade sprites are a handful of
  extreme poses held hard and cut between.

`arc_stance` is isolated on a plain stage, which is exactly what the
existing Z-Image → vtracer → SVG rig pipeline wants. Recommendation: run
it as a **distinct recurring segment** (a VS screen, a health-bar gag) and
leave the wall exhibits on the current direction — two art directions
fighting for the same wall would read as incoherent.

## 5. Things proven by measurement — do not re-derive

**Z-Image prompt grammar, measured this session.** Four rules, each paid
for with a failed image:

1. **Name first, describe barely.** At fixed seed, "Nancy Pelosi" plus
   "distinctive dark bob, angular face" returned a generic glamorous woman
   who is not her; "Nancy Pelosi, former Speaker of the House" with *no*
   physical description returned a clean likeness. A description that
   contradicts the real face **overrides the name**. Biden, Obama and
   Clinton all resolve name-only too. Only add a feature if it is true.
2. **Negation does not work — twice over.** `zimage_t2i` samples at
   **cfg=1**, so there is no classifier-free guidance and the negative
   prompt is **inert** (stated in `scripts/comfy/templates.py`). Worse,
   writing "no hat, no cap, no fedora" inside the *positive* prose just
   feeds the model the concept: that exact card came back wearing a peaked
   cap. State the positive instead — "bare-headed, short hair swept back".
3. **Never use a domain term with a literal homonym.** "An abstract
   candlestick chart rendered as glowing bars and **wicks**" produced a man
   standing among lit **wax candles**, no chart at all. Two candle words
   beat the finance sense. Describe the geometry: narrow vertical bars,
   each crossed by a thin line running above and below it.
4. **Watch for iconography that drags numerals in.** A card saying "no
   numbers" still printed **1 / 2 / 3**, because "three-tier winner's
   podium" summons the Olympic podium whole. Say "three plain rectangular
   pedestal blocks of different heights, front faces smooth and unmarked".
   Same class of bug: asking for a tape "printed with plain rectangles and
   small arrows" produced a legible **7**. A prop that must carry nothing
   should be described as *completely blank*, not as blank-ish marks.

**Illustrious-XL is a character checkpoint.** Six of eight object prompts
came back unusable (`calendar_late` a blank grey canvas). It cannot draw
symbolic still life or architecture. Z-Image, same machine, drew all of
them cleanly first try.

**Naming "JoJo" is load-bearing and dangerous.** Remove it and the style
collapses into abstract colour noise (tested twice). Keep it and it drags
in the IP — Jotaro's hat, a Stardust Crusaders cover logo. The workflow's
gate caught the subtlest instance: a requested "low angle, fist thrust at
viewer" pose IS the Stardust cover composition, a leak no negative-prompt
token could block.

**Prompt + fixed seed CANNOT hold a character's identity.** Same seed,
same lock prompt, three poses → three different people, skin drifting to
grey. This is the same wall that made per-beat pose cycling change Sol's
haircut mid-sentence. For a **recurring caricature** (the owner wants a
consistent Trump figure — same suit, hair, proportions) the answer is
**masked inpainting from one approved base**, which is proven here: 66
visemes and 8 arm positions with identity pixel-identical outside the mask.
See `scripts/vector/arm_mask_probe.py` — leak outside the mask 0.11%.

**Chatterbox has controls nobody had used.** `exaggeration`, `cfg_weight`,
`temperature` — every line ever generated shipped at defaults. Its
tokenizer also carries 49 bracket tokens; tested with/without at fixed
seed: `[sigh]` +0.7s, `[clear_throat]` +1.2s, `[whisper]` +1.3s **render**;
`[laughter]` and `[UM]` do **not** — do not use them.

**The VO pipeline pitch-corrects to a ~151 Hz canon**, so delivery settings
barely move measured pitch (Rex 124.6 → 125.5 Hz). What changes is
delivery character. The two voices are separated by **timbre**, not pitch
(rolloff 4580 Hz Rex vs 7530 Sol). A future "make him sound younger/older"
request needs a different reference clip, not more parameter tuning.

**The chatterbox venv is CPU-only** (`torch 2.6.0+cpu`). ~7s/line, fine.
Full ep.1+ep.2 regeneration is ~10–15 min — run it in the background, it
exceeds a foreground timeout.

**`retime_beats.py` derives every beat start from measured audio** and
still lands on exact TOTAL frames. Never hand-adjust timings after
regenerating VO; run it with `--write`.

**Switching ComfyUI model family inside one server process** is a known
VRAM-eviction corruption risk. Order generation jobs so it happens once,
or restart the server.

**The staging audit is now panel-aware** but honest about a blind spot:
its face-coverage check is a **catastrophe guard only** (threshold 0.60)
and does not catch crowding — the metric flagged six *confirmed-good* ep.1
beats harder than the known-bad case. Two-shots still have to be looked at.

**Use the Write/Edit tools for quote-heavy code.** Bash heredocs broke on
escaping four separate times this session.

---

## 6. Suggested order of work

1. ~~Regenerate the 8 failed exhibits through Z-Image.~~ **DONE** — and
   twice, because the first Z-Image pass drifted into Jotaro (§4). Seven
   are regenerated, `committee_room` was left alone because it passed, and
   `chip_gavel` was skipped because no beat uses it.
2. ~~Fix the two branch-order beats and the "45 DAYS" label.~~ **DONE**
   (§3).
3. ~~Re-render ep.1, verify, deliver.~~ **DONE** →
   `content/probe/ep1_panel_v2.mp4`.
4. **Next: get the owner's call on the arcade direction (§4b)** before
   building more wall art. It changes what step 5 should contain.
5. Build the **code-drawn floating words** (`DEAL`, `FORTUNE`, ゴゴゴゴ) in
   a `MangaWords` layer over `ExhibitPlate`, keyed to beat frames so each
   lands on its syllable. Generated lettering is garbage — this must be
   code, and it is also the house rule. *(If the arcade direction is
   taken, this layer becomes the arcade HUD instead, which is the same
   idea with a better excuse.)*
6. Apply the same exhibit + SFX treatment to ep.2, deliver both for the
   owner's approval of the recipe.
7. Only then: rewrite ep.3–5 scripts to ep.1/ep.2 density, regenerate
   their VO, re-time, apply the recipe, render.
8. Separately, when asked: build the **recurring caricature figure** by
   inpainting from one approved base. Note this is now *less* urgent for
   politicians specifically — Z-Image resolves named figures well enough
   name-only (§5) that consistency is the only remaining reason for it.

---

## 7. Where things live

```
remotion/src/compositions/FairMarketEp{1..5}.tsx   the episodes
remotion/src/motion/Set.tsx                        studio, RoundDesk, NewsBand
remotion/src/motion/ExhibitPlate.tsx               animated wall plate
remotion/src/motion/Infographic.tsx                charts + code-drawn exhibits
remotion/public/characters/cast_ep1/exhibits/      wall art + _cards.json
remotion/public/audio/fairmarket{,_ep2..5}/        VO per episode
remotion/public/audio/viral_real/                  the 10 downloaded SFX
remotion/public/audio/v_*.wav                      the 5 wired into ep.1
remotion/public/audio/bed_ep*.wav                  music beds (unapproved)

scripts/vector/make_all_vo_local.py    VO gen — DELIVERY + PERFORM tables
scripts/vector/retime_beats.py         beat starts from measured audio
scripts/vector/stage_audit.py          staging audit (panel-aware)
scripts/vector/gen_exhibits.py         wall art generator
scripts/vector/gen_jojo_exhibits.py    generates from the gated cards
scripts/vector/_panelize.py            episode -> panel format
scripts/vector/_populate_desk.py       reaction-cut grammar
scripts/vector/_wire_exhibits.py       attach exhibits + SFX to beats
scripts/vector/arm_mask_probe.py       proof that narrow masks isolate parts
scripts/vector/rex_voice_probe.py      Chatterbox delivery A/B
scripts/vector/vo_tag_probe.py         performance-tag A/B
scripts/audio/make_desk_bed.py         music bed generator
scripts/audio/mux_bed.py               lay bed on a master, no re-render
scripts/audio/fetch_viral_sfx.py       download the real meme SFX
scripts/audio/make_viral_sfx.py        synthesised, rights-clean fallback
```

**Licence note:** the meme SFX (`viral_real/`) have no clean rights chain —
Among Us is InnerSloth's audio, Vine Boom is a sample of unclear origin,
Faah is someone's voice. Fine for this non-commercial series; never ship
them in anything sold. `make_viral_sfx.py` is the clean alternative.
