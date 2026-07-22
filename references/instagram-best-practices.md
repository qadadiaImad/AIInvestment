# Instagram Best Practices — AI STACK content

The house rules for everything we publish to Instagram (carousels + Reels).
Written 2026-07-22, from platform knowledge as of mid-2026 — re-validate
quarterly; Instagram's algorithm and format preferences drift. This guide is
the single reference the carousel factory (`remotion/`), the reel packages
(`higgsfield_*.txt`), and any future content pipeline should follow.

Educational content only — every deliverable also follows the repo's
compliance rails (§7).

---

## 1. Formats & dimensions

| Format | Size | Use |
|---|---|---|
| Carousel slide | **1080×1350 (4:5)** | our KurzSlide default — max feed real estate |
| Reel | **1080×1920 (9:16)** | video stories, talking-head UGC |
| Cover frame | same as content | designed title card, readable as a grid thumbnail |

- 4:5 beats 1:1 for feed reach (more screen height). Never letterbox.
- Carousels: **4–7 slides** is the sweet spot. Every extra swipe = an
  engagement signal; past ~7, completion drops. 10 is the hard cap.
- Reels: **30–45s** sweet spot, 90s hard ceiling. Retention % of first 3s is
  the strongest ranking input.

## 2. The hook (first 1.5 seconds / first slide)

- Reels: the hook line lands **inside 1.5s**, spoken AND on screen.
- Carousels: slide 1 is a headline card — one tension, one number. The
  reader should *have* to swipe ("That math shouldn't work." / "It moved
  before the keynote.").
- A paradox or contrast outperforms a statement of fact. Lead with the gap,
  not the news.

## 3. Sound-off & safe zones

- Assume **muted autoplay**: every load-bearing number appears as on-screen
  text, high-contrast, big.
- Keep critical text out of the **bottom ~15%** (caption/UI overlay) and the
  **right edge** (action rail) on Reels; keep a 60–90px margin on carousel
  slides (our engine's padding already respects this).
- One idea per slide / per beat. If a slide needs two reads, split it.

## 4. Native feel — what NEVER goes on an image

- **No watermarks, no borders, no cross-platform logos** (TikTok watermarks
  actively suppress reach).
- **No internal/meta commentary on the image**: sourcing notes,
  "cross-checked vs IBKR", "cached bundle", "data pipeline" language —
  that's QA text, it reads as cringe on a public post. Provenance lives in
  the repo (`brief.md`, git history), never on the slide. A quiet
  "Figures as of <date>" line is the only acceptable data stamp.
- Dates on figures are good ("as of July 11") — phrased naturally, not as
  engineering jargon ("cached 7/11" ❌).
- Brand consistency: same palette (`remotion/src/slides/theme.ts`), same
  fonts, corporate logo chip on every slide of a company carousel.
- The "not financial advice" footer stays — it's a compliance rail, not
  commentary (§7).

## 5. Captions & hashtags

- **First line = the hook restated** — it's what shows before the "…more"
  fold and it's weighed by search. Front-load it.
- Structure: hook line → 1–2 sentences of substance → soft CTA → disclaimer
  → hashtags.
- **3–5 targeted hashtags.** Hashtag walls (15–30) read as spam and add
  nothing post-2024; IG treats captions as search text now, so real
  keywords in the caption matter more than tags.
- CTA: **save/share/follow** ("Save this for earnings Thursday"). Saves and
  shares are the top-weighted signals; comments next; likes last. Never
  hard-sell, never "link in bio" spam on educational posts.

## 6. Reels specifics

- Trending audio, picked **the morning of posting** from the Reels Trending
  tab, ducked to ~15–20% under the VO. Sounds decay in days — never reuse
  last week's.
- Persona continuity: same creator identity every clip (our Maya anchor) —
  familiarity compounds retention.
- Pattern-interrupt every 3–5s: caption flash, b-roll cutaway, push-in.
- Design the cover frame deliberately; the grid is a storefront.

## 7. Compliance rails (non-negotiable, this repo)

- "Educational — not financial advice · DYOR" on every deliverable (spoken
  + on-screen for Reels, footer for slides).
- Fact vs reported vs expected: certainty is **labeled** (our news-slide
  tags FACT / REPORTED / EXPECTED). Never state a rumor as fact; never name
  outlets — "reportedly".
- Congressional trades: public record, transparency framing only — never an
  accusation, never "copy this trade".
- No fabricated numbers: every figure traces to a dated retrieval; decayed
  figures carry their date ("as of July 11").

## 8. Cadence & measurement

- Consistency beats volume: a sustainable 3–5 posts/week outperforms
  bursts. Post when the audience is on (test 12–14h and 19–21h local).
- Judge a post by **saves, shares, and carousel completion** — not likes.
- First hour matters: reply to early comments; a comment answered is a
  second impression.
- Iterate from the grid: if a cover frame underperforms, redesign the
  cover, not the whole carousel.

---

*Owner of this doc: whoever ships content next. Update it when the platform
moves; date your edits.*
