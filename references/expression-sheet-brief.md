# Expression sheet — the character's FACE library (Higgsfield task)

## Why this exists

The owner's note on the cam reel: *"too many actions under one frame … use more
smooth facial express - max granularity so u have the possibility to use them
while building a clip."*

That is exactly right, and it is the one thing the current pipeline cannot
synthesize. The character exists as 13 full-body pose drawings
(`remotion/public/meme_reel/poses/`). Every emotion we show is a *body* pose,
because that is all there is — so emotional beats get carried by cuts and
travel, which is what read as hyperactivity. Real limited animation carries the
quiet beats on the FACE and saves the body for the loud ones.

Faces cannot be extracted or edited out of the painted PNGs (head-swaps on
painted drawings show seams), and I will not generate new art of the character
without the generator that made him. **This is a Higgsfield job** — it needs
character-consistent image generation off the existing drawings as reference,
and Higgsfield auth is interactive, so it runs on the laptop.

## What to generate

**Nine upper-body drawings** of the same character — the rounded bald man in
the blue polo — same painting style, same outline weight, same palette, same
camera angle as the existing sheet, transparent background, one drawing per
image, framed from the waist up (the cam format crops at the waist, so
full-body versions waste resolution on legs we never show).

Body language NEARLY IDENTICAL across all nine — a relaxed three-quarter
stance, hands out of frame or resting — so that consecutive drawings differ
ONLY in the face. That is what makes them cuttable as *facial* animation: if
the shoulders move between two drawings, a cut reads as a body action again.

| # | name | face |
|---|---|---|
| 1 | `calm` | neutral, soft eyes, mouth relaxed |
| 2 | `focused` | slight squint, brows level, mouth flat — reading the chart |
| 3 | `intrigued` | one brow up, slight head tilt, small o-mouth |
| 4 | `confident` | easy half-smile, brows relaxed — just placed the trade |
| 5 | `tense` | brows pinched, lips pressed thin |
| 6 | `worried` | brows up at the middle, eyes wide, corners of mouth down |
| 7 | `gritted` | teeth clenched, jaw set, eyes narrowed — watching it chop |
| 8 | `deflated` | lids heavy, gaze down, everything sagging — just stopped out |
| 9 | `resolved` | calm again but firmer than #1 — small nod energy, learned it |

Generate with the existing pose PNGs attached as the character reference
(`idle.png`, `notices.png`, `facepalm.png` triangulate him well). Reject any
take where the polo colour, head shape, brow weight or outline width drifts —
consistency beats beauty here; one off-model drawing poisons every cut into it.

## Integration (back in the sandbox — no Higgsfield needed)

1. Drop the nine PNGs in `remotion/public/meme_reel/faces/`.
2. `python scripts/meme_reel/pose_anchors.py` measures ground-contact anchors —
   for upper-body drawings the anchor is the torso base; the script's ink-bottom
   logic handles it, but eyeball the contact sheet.
3. `python scripts/meme_reel/head_anchors.py` measures the heads (sweat drop +
   FX anchoring).
4. The cut sheets in `cam_staging.json` then interleave face cuts with body
   cuts: quiet stretches become `focused → intrigued → tense → gritted` at the
   FACE level with the body still, and the body poses fire only on the loud
   beats (the take, the stagger, the facepalm).
5. `python scripts/btc_reel/check_overlaps.py` re-verifies the no-overlap
   guarantee with the new drawings in the sheet.

## The paste-ready prompt (laptop, Claude Code, repo root)

---

> Read `references/expression-sheet-brief.md` and generate the nine-expression
> sheet it specifies, using the `higgsfield-generate` skill with
> `remotion/public/meme_reel/poses/idle.png`, `notices.png` and `facepalm.png`
> as character references. One image per expression, upper body from the waist
> up, transparent background, identical stance across all nine — only the face
> changes. Reject and regenerate any take that drifts off-model (polo colour,
> head shape, outline weight). Save as
> `remotion/public/meme_reel/faces/<name>.png` using the table's names, run
> `python scripts/meme_reel/pose_anchors.py` and
> `python scripts/meme_reel/head_anchors.py`, show me the contact sheet, and
> commit to `claude/refresh-data-import-stock-story-svya0l`.

---

*Educational content only — not financial advice.*
