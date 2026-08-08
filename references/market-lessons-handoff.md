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

### Still waiting on the owner

- **Music bed** — built for all five, demoed on ep.2, never approved and
  never wired. `scripts/audio/mux_bed.py` applies it to a finished master
  in seconds with no re-render, so approval is cheap to act on.
- **Whether to continue the JoJo art direction** (see §4).

---

## 3. Open defects, in priority order

1. **Two ep.1 exhibits never appear.** At 46s and 68s the wall shows a
   politician photo instead of `committee_room` / `two_podiums`. Those
   beats carry a `tvPose`, and the wall's content chain in
   `FairMarketEp1.tsx` tests `shot?.tvPose` **before** `cur.exhibit`, so
   the photo wins. The wiring is correct; the branch order defeats it.
   Fix: move the `cur.exhibit` test above `tvPose`, or drop `tvPose` on
   those two beats.

2. **The "45 DAYS" callout is unreadable** at ep.1 77s — teal text on the
   cream calendar. Needs a dark plate behind the label in
   `motion/ExhibitPlate.tsx`.

3. **Eight wall exhibits need regenerating** — see §4.

4. *(cosmetic, pre-existing, owner already approved the episode)* ep.1
   beat 123 reports one marginal off-frame in the staging audit: Rex's
   shoulder crops 32px at k=1.14.

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

### The routing rule to apply next

Send **everything on the wall to Z-Image**. The hypothesis that
"Illustrious draws people well" is only half true: it draws a *portrait*
well and a *specific readable action* badly, and heavy manga style tags
push it toward abstract composition plus fake lettering. Get the JoJo feel
from the code layer instead — floating words, halftone overlay, hard rim
light — where it is controllable and legible.

Note the gate could not have caught this: it reviewed **prompts**, not
**images**. Any future art pass needs a *visual* gate on the output, which
is what the viseme pipeline already does (sonnet agents reading the
generated sheets).

---

## 5. Things proven by measurement — do not re-derive

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

1. Regenerate the 8 failed exhibits through **Z-Image**, using the gated
   cards already in `_cards.json`. Gate the results **visually**.
2. Fix the two branch-order beats and the "45 DAYS" label (§3).
3. Re-render ep.1, verify frames + audio, deliver.
4. Build the **code-drawn floating words** (`DEAL`, `FORTUNE`, ゴゴゴゴ) in
   a `MangaWords` layer over `ExhibitPlate`, keyed to beat frames so each
   lands on its syllable. Generated lettering is garbage — this must be
   code, and it is also the house rule.
5. Apply the same exhibit + SFX treatment to ep.2, deliver both for the
   owner's approval of the recipe.
6. Only then: rewrite ep.3–5 scripts to ep.1/ep.2 density, regenerate
   their VO, re-time, apply the recipe, render.
7. Separately, when asked: build the **recurring caricature figure** by
   inpainting from one approved base.

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
