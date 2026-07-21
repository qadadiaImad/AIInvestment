# Persona Image-Generation Rule Set — "Karim"

> Canonical rules for EVERY persona image/video generation. Validated by owner 2026-07-21.
> If a generation violates any rule below, discard and regenerate — do not publish.

## 1. Identity — LOCKED (never change)

- Always image-to-image anchored on `reference/00_master.png` (or another grid image as start frame for video). **Never generate the face from text.**
- Face: identical to reference — short neatly trimmed beard, light-brown skin, same hairstyle, same features. No face edits, no aging, no stylization.
- Wardrobe (fixed, pick per context): **A** navy blazer + white crew-neck (lessons/default) · **B** charcoal crew-neck sweater (casual/shorts) · **C** plain white thobe (religious-calendar content only, e.g. Ramadan/Eid).

## 2. Background & setting — keep it NORMAL (owner rule)

- **No Islamic geometric patterns, no ornamental tiles, no emerald/green "Islamic aesthetic" panels, no Arabic calligraphy, no mosque imagery, no cultural set dressing.** (The original master/grid backgrounds predate this rule — override the background in every new generation.)
- Settings are ordinary modern Western interiors: home office with plain shelves/plants, clean desk with a monitor, kitchen counter with coffee, city café, neutral wall. Lived-in and relatable, not staged.
- Don't try hard on the background — it's a backdrop, not a statement. Soft natural light, gentle depth of field, muted neutral tones.

## 3. Vibe — a normal person living a Western halal lifestyle

- He reads as a relatable Western professional who happens to be Muslim — **never styled to "appear Muslim or Arab."** Faith shows through what he says and does (the content: screening, purification, zakat math), not through costume or decor.
- No staged religious props (prayer beads on desk, ornamental Qur'an stands, etc.). Natural, incidental, modern.
- Demeanor: calm, warm, confident, understated. Educator, neighbor, colleague — not preacher, not guru.

## 4. Aesthetic rails (unchanged)

- No luxury items, no watches, no logos, no lambos, no green-candle porn, no "1000%" thumbnails.
- Sober financial-educator look; thin NFA footer on published content; persona disclosed as AI in bios/about pages.

## 5. The prompt block (paste verbatim, then add the shot description)

```
Same person as the reference image: identical face, short neatly trimmed beard, light-brown
skin, same hairstyle. Photorealistic, soft natural light. Setting: an ordinary modern Western
interior (home office / desk / cafe), plain neutral background, lived-in and relatable.
No Islamic geometric patterns, no ornamental tiles, no Arabic calligraphy, no cultural set
dressing. Sober professional financial-educator aesthetic, no logos, no luxury items.
```

- Model: `nano_banana_pro` with `--image course/persona/reference/00_master.png`
- Stills 3:4 (portrait) or 16:9 (wide/thumbnail); video 9:16.

## 6. Generation workflow (owner rule 2026-07-21)

- **Always present TWO generation suggestions (concept + prompt sketch + estimated credits) and get the owner's pick BEFORE consuming credits on any image or video.**
- The desk/workspace is a **persistent set feature** (like the avatar): once the desk-master image is validated, every video/still at the desk anchors on it (image-to-image / `--start-image` / `--image` reference) — same desk, same layout, same camera framings, so the space feels real and recurring, never freshly AI-generated.

## 7. QA checklist before publishing any asset

1. Face matches the reference grid (side-by-side check).
2. Wardrobe is exactly A, B, or C.
3. Background: zero Islamic-pattern/cultural set dressing; reads as a normal Western interior.
4. No luxury/logo/trading-flash items anywhere in frame.
5. Voice (video): the single locked voice preset, unchanged.
