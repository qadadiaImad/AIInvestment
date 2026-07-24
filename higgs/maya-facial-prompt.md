# Maya — first facial/character reference prompt

First Higgsfield generation for **Maya** (`@StackedWithMaya`), the AI STACK
channel's on-camera persona. Built from the existing bible in
`.claude/agents/higgsfield-ugc.md` (24, sharp young markets analyst, calm/
dry-witted, "not a hype creator") — this doesn't redefine her, it's the
first actual face reference to lock the look that text description implies.

**Scope note:** this prompt is deliberately face/expression/styling/lighting
only — no body or figure descriptors. That's a intentional choice, not an
oversight: Maya's brand is "sharp analyst," not a body-forward creator, and a
generation prompt that foregrounds physical descriptors beyond the face
reads as sexualizing a content-creator avatar, which isn't the direction
here. If a later pass wants a full-body wardrobe reference (for a walking/
gesture shot, say), that's a separate, clothing/pose-only prompt — not a
figure-emphasis one.

## Physical traits (defaults, from the existing bible — flag anything to change)

| Trait | Value | Source |
|---|---|---|
| Age | 24 | bible |
| Ethnicity | Mixed-race | bible |
| Skin tone | Warm light-to-medium olive/tan, natural undertone | new — pick a specific tone since "mixed-race" alone under-specifies it for consistent regeneration |
| Hair | Shoulder-length, dark, soft natural waves | bible |
| Eyes | Warm brown | new — kept in the same warm palette as hair/skin rather than a contrasting color, for a cohesive natural look |
| Face shape | Soft-oval with defined cheekbones — approachable, not severe | new |
| Makeup | Light, natural — dewy finish, subtle brow, no heavy contour | bible ("light natural makeup") |
| Accessories | Small gold hoop earrings | bible |
| Wardrobe | Cream ribbed knit top, oversized soft blazer | bible |
| Setting | Cozy modern home-office corner — bookshelf, small plant, warm desk lamp, soft monitor bokeh | bible |
| Expression | Calm, quietly confident, dry-witted — camera-aware, not performative | bible (voice description translated to face) |

## Generation prompt

```
Photoreal portrait, chest-up composition, 9:16 vertical framing.

A 24-year-old mixed-race woman with warm light-to-medium olive skin, natural
undertone, healthy natural skin texture (not airbrushed or plastic).
Shoulder-length dark hair in soft natural waves. Warm brown eyes, soft-oval
face shape with defined but gentle cheekbones, straight nose, natural full
lips, easy half-smile — calm, quietly confident expression, like a sharp
financial analyst about to explain something clearly, not a performative
influencer smile.

Light, natural makeup: dewy skin finish, subtle brow definition, no heavy
contour or dramatic eye makeup. Small gold hoop earrings. Wearing a cream
ribbed knit top under an oversized soft blazer.

Setting: cozy modern home-office corner, softly out-of-focus bookshelf and
small potted plant in the background, warm desk lamp glow, gentle monitor
bokeh. Soft warm key light from front-left, subtle rim light, natural color
grade.

Camera: shot as if on a mirrorless camera with an 85mm-equivalent lens,
shallow depth of field, natural color science, 4K-level facial detail.
Photographic realism, not illustrated or airbrushed.
```

## Negative / avoid

```
sexualized styling, low-cut or revealing wardrobe, exaggerated or
figure-emphasizing framing, plastic/over-smoothed "AI doll" skin,
heavy glam makeup, dramatic studio lighting, emoji-influencer aesthetic,
exaggerated proportions, uncanny-valley artifacts, extra fingers/limbs.
```

## Next step

This is the prompt only — not yet run. When you're ready to generate:
`higgsfield-soul-id` (if you want a reusable Soul Character/identity lock
for consistent reuse across future renders) or a one-off `higgsfield-generate`
call with this prompt (faster, no identity training). Once a reference image
exists, update `higgs/_maya_avatar.json` with the resulting reference ID the
same way it's already keyed for the current placeholder entry.
