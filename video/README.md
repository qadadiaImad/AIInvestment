# video/ — character reels

A Remotion project that turns the AI-STACK mascot family into short vertical
(1080×1920) reels. It does not own or redefine the characters: `remotion/src/characters/`
is the single source of truth, and this project reads it directly.

## Where things come from

| What | Lives in | Consumed here via |
|---|---|---|
| Character roster + metadata (name/role/tagline/color) | `../remotion/src/characters/family.tsx` | `src/characters/registry.ts` |
| Rigs (Chip/Watt/Qubit/Cap/Nova/Cloudy) | `../remotion/src/characters/*Rig.tsx` | `src/characters/registry.ts` |
| `Grain` / `Vignette` polish layers | `../remotion/src/motion/Polish.tsx` | `src/compositions/CharacterSmokeTest.tsx` |
| Brand palette (mirrored, not imported) | `../remotion/src/slides/theme.ts` (`C`) | `src/theme.ts` |

`registry.ts` imports the rig `.tsx` files by relative path across the project
boundary — this repo does not use npm workspaces, so it's a plain filesystem
import. It works because both projects pin identical `react`/`remotion` versions
(19.2.3 / 4.0.496); don't let them drift apart.

Maya is excluded from this project (out of scope per owner request). Karim has no
SVG rig to import — he's a voice/portrait persona defined under `../course/persona/`
and participates here via audio + a static portrait, not `registry.ts`.

## What's added on top (Phase 3 approvals)

Source: `haidrrrry/claude-remotion-skill` (audited, not vendored — see CLAUDE.md §9).

- `src/components/Entrance.tsx` — spring-first entrance (opacity + translateY +
  scale). Phase 3 decision: default to spring() over interpolate()/bezier; if a
  render looks worse than the existing `remotion/src/motion/craft.ts` approach,
  roll back per-composition, don't force it project-wide.
- `src/components/BgMesh.tsx`, `Grade.tsx` — the two layers of the skill's 5-layer
  stack that didn't already exist (`Grain`/`Vignette` are reused, not duplicated).
- `src/components/SafeZoneGuide.tsx` — dev-only 9:16 safe-zone overlay (`enabled`
  prop, off by default; never ship it burned into a delivered render).
- `src/components/Captions.tsx` — word-synced captions via the official
  `@remotion/captions` API, styled per the skill's design rules (2–4 words/page,
  active word in the speaking character's own brand color, ~65% height). Not yet
  wired into a composition — no character has a recorded voice track yet.

## Font loading

`theme.ts` declares font *names* only; the actual `@font-face` rules come along for
free through the cross-project import chain (`registry.ts` → a `*Rig.tsx` → import →
`remotion/src/slides/theme.ts` → `@fontsource/*` CSS imports). This project's own
`package.json` intentionally does not list `@fontsource` or `@remotion/google-fonts`
as a dependency — do not add `@remotion/google-fonts` here; `fonts.gstatic.com` is
unreachable in this repo's sandboxed render environments, which is exactly why the
main project moved to `@fontsource` in the first place.

## Commands

```bash
npm --prefix video install         # first time
npm run video:studio               # from repo root — opens Remotion Studio
npm run video:render               # from repo root — see remotion render --help
# or, from inside video/:
npx remotion render src/index.ts SmokeTest-Chip out/chip.mp4 \
  --browser-executable=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

The `--browser-executable` flag is only needed in sandboxes where Remotion's
Chrome auto-download/launch fails ("Old Headless mode has been removed").

## Compositions

`SmokeTest-{Chip,Watt,Qubit,Cap,Nova,Cloudy}` — the Phase 5 smoke test: one 8s
(240 frame @30fps) vertical card per character using only the enhancements above,
nothing else. Render times (this sandbox, `headless_shell`, `--crf 17`): Chip ~75s,
Watt/Qubit/Cap/Nova/Cloudy ~68–70s each. All six passed visual QA (frames extracted
at 0.5s/2s/4s/7.5s and inspected): fonts load, brand-color glow/mesh render, text
stays inside the safe zone, no clipping, entrances stagger correctly (character
settles before title, title before tagline).

`ChokepointStory-TSMC` — a 26s (780 frame) vertical explainer: Chip plays in
front of `src/components/OrbitBackground.tsx`, a live animated ring of real
company logos orbiting a TSM center mark, while staged captions tell the
TSMC chokepoint's story (`content/carousel_2026-07-23/CHOKEPOINT_TSMC/brief.md`).
Logo source: `src/data/orbitLogos.ts`, generated from the `simple-icons` npm
package (CC0-licensed real brand marks) — see that file's header comment for
the exact regeneration command and the coverage note (only 7 of the
chokepoint's ~20 related tickers have a real mark in `simple-icons`; the
orbit is scoped to named-in-the-script companies plus the other available
real logos, rather than mixing real logos with placeholder dots). An earlier
version of this composition used a matplotlib-rendered dot graph as a static
background image — replaced after review feedback that it looked bad;
`OrbitBackground` is a live Remotion/SVG layer instead (animated ring drift +
per-tile idle breathing), which also reads better than a flat image.

## Licensing

Remotion is free for individuals, non-profits, and for-profit orgs with ≤3
employees; a Company License is required at 4+ (aggregated across agency/client/
contractor collaborations on the same project). Confirm headcount before any
commercial use of output from this project.
