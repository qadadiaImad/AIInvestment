# Course Persona — "Karim" (working name)

> The stable synthetic presenter for the halal AI-investing course. **Identity is locked** to the
> reference grid in `reference/` and the registered Higgsfield custom avatar. Never regenerate the
> face from text — always anchor on these references. Created 2026-07-21.

## Persona bible

| Field | Value |
|---|---|
| Name | **Karim** (working name — rename before publishing) |
| Role | Branded narrator / presenter of the course. **Disclosed as an AI persona** — never presented as a real human expert or credential holder. |
| Age / look | Early 30s, light-brown skin, short neatly trimmed beard, kind confident eyes, gentle closed-mouth smile |
| Wardrobe A | Navy blazer over plain white crew-neck (default / course lessons) |
| Wardrobe B | Charcoal crew-neck sweater (casual posts / shorts) |
| Wardrobe C | Plain white thobe (Ramadan / religious-calendar content) |
| Set | Ordinary modern Western interiors (home office, desk + monitor, café) — neutral, lived-in. **No Islamic patterns/tiles or cultural set dressing** (owner rule 2026-07-21 — see RULES.md; original master/grid backgrounds predate this rule) |
| Tone | Calm, warm, sober "financial educator, not guru." No hype, no luxury flash, no signals. Cite-never-rule ("passes the AAOIFI screen at X%", never "this is halal"). |
| Voice | TBD — lock ONE preset at pilot review and never change it (precedent: "Harrison" for the reels) |
| Aesthetic rails | No lambos, no green-candle porn, no "1000%" thumbnails, no logos, no watches. Thin NFA footer on published content. |

## Prompt block

**Superseded — use the canonical prompt block and full rule set in [`RULES.md`](RULES.md)** (owner-validated 2026-07-21: neutral Western backgrounds, no Islamic-pattern set dressing; face and wardrobes unchanged).

## How to generate new content (identity-stable)

- **New stills:** `higgsfield generate create nano_banana_pro --prompt "<prompt block> + <variation>" --image course/persona/reference/00_master.png --aspect_ratio 3:4 --wait`
- **Talking-head video:** `marketing_studio_video` with the custom avatar (see IDs below), `--mode ugc`, 9:16, `--generate-audio true`
- **Cinematic B-roll:** `seedance_2_0 --start-image course/persona/reference/00_master.png` (or any grid image as the start frame)
- QA every new asset against the reference grid before publishing (face, wardrobe, set drift).

## Files (v2 — desk set, owner-validated 2026-07-21)

```
reference/00_master.png          canonical FACE anchor (unchanged)
reference/07_desk_master.png     canonical SET anchor — the desk/workspace every asset lives in
reference/01_desk_front.png      front waist-up at desk, wardrobe B
reference/02_desk_three_quarter.png  45° at desk, wardrobe B
reference/03_desk_profile.png    profile working at monitor, wardrobe B
reference/04_desk_presenting.png presenting gesture at desk, wardrobe B
reference/05_desk_blazer.png     front at desk, wardrobe A
reference/06_desk_wide.png       16:9 wide of the full home office
reference/_v1/                   archived v1 grid (emerald-panel backgrounds, pre-RULES)
video/intro_desk.mp4             15s course intro at the desk (Karim v2 avatar)
video/_v1/                       archived pilots (pilot_ugc, pilot_broll)
higgsfield-ids.json              all platform IDs (avatars, uploads, URLs)
```

## Higgsfield IDs (also in higgsfield-ids.json)

- **Custom avatar v2 (USE THIS):** `65141281-16a9-411a-817c-b75f31a65319` — "Karim v2 - desk set" (built from 07 + 01 + 04)
- Custom avatar v1 (deprecated): `1d3ddacc-e0fd-4b07-bfaa-bf4d67403d75` — "Karim - Halal AI Investing narrator"
- Workspace: `6594d62c-39d3-4804-b29e-60d57f0beceb` (starter plan)
- CLI: `~/.higgsfield/bin/higgsfield.exe` (v1.1.19, on user PATH as `higgsfield`)

## Compliance notes

Persona is presentation, not authority: scholarly/methodology trust lives in the content
(timestamped math, published AAOIFI methodology, scholar citations). Disclose AI persona in
channel bios and course about-pages. FR content additionally falls under AMF/2023 influencer-law
rules — review before publishing French videos. *Not financial or religious advice.*
