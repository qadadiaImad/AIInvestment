# Standalone "shock-stat" Instagram carousels

One-off, standalone 9-slide Instagram carousels (4:5) that market the AI-Stack
Terminal itself — distinct from the daily halal-post / reels-kit pipeline
(`_build_v4.py`, `make_reel.py`). Each is a self-contained builder script; there is
no shared framework beyond the copied brand system.

*Educational/research only — not financial advice. Congress data is public-record
STOCK Act disclosure, not an accusation of wrongdoing.*

## The builders

| Script | Post | Hook | Data source | CTA |
|---|---|---|---|---|
| `_build_platform_carousel.py` | Platform feature tour | "We mapped the entire AI stack" | live site screenshots | LINK/AI STACK |
| `_build_systemic_risk_carousel.py` | Correlation / systemic risk | "You don't own 20 AI stocks. You own 3." | `web/public/data/risk.json` + resiliency | RISK |
| `_build_congress_carousel.py` | Congress trading | "Congress traded up to $1B. Guess what they bought." | `web/public/data/congress.json` | CONGRESS |
| `_build_value_carousel.py` | Price vs fundamental value | "This stock costs $548. A model says it's worth $86." | `web/public/data/site.json` screener | VALUE |
| `_build_energy_carousel.py` | AI power crunch | "AI doesn't run on chips. It runs on electricity." | `site.json` (energy layer) + `capital_web` GW deals | POWER |
| `_capture_platform_src.py` | (helper) captures legible, zoomed screenshots of the live site into `_platform_src/` | — | live site via Playwright | — |

## Run

```bash
# from repo root; each writes higgs/<name>_showcase_<date>/ (PNGs + caption.txt + manifest.json)
python higgs/_build_congress_carousel.py
python higgs/_build_value_carousel.py
python higgs/_build_energy_carousel.py
python higgs/_build_systemic_risk_carousel.py
python higgs/_build_platform_carousel.py

# (re)capture the live-site screenshots the feature/tool slides embed:
python higgs/_capture_platform_src.py     # → higgs/_platform_src/*.jpg
```

Rendering uses Playwright/Chromium at `device_scale_factor=2`, so the 1080×1350
layout comes out **2160×2700** (crisp for Instagram). Screenshots are captured live
from `highreturnethicalscreen.vercel.app`, cropped/zoomed for legibility, and shown
uncropped (`object-fit: contain`).

## Shared conventions (owner-tuned)

- **Brand system** copied from `_build_v4.py`: Fraunces / Inter / JetBrains Mono,
  dark `#0A0D12`, giant-stat-first slide layout, browser-chrome mockup frames.
- **Palette:** gold `#E0A23B` for shock/scale numbers, green `#34D399` / `#7FE9C2`
  for the "good/opportunity" side. **No red as text emphasis** (owner preference).
- **Typography:** big headlines that fill the frame; body/explanation text sized
  ~0.7–0.8× the headline so it reads on a phone; sparse slides vertically centered.
- **Rails on every slide:** educational/NFA footer; "a read, not a call" for
  model-based value claims; "public record · not an accusation of wrongdoing" for
  the congress post; certainty labels (reported/filed) on sourced figures; the data
  vendor is never named (always "a fundamental-value model"). Numbers trace to the
  live bundles and are stamped by date.
- **Distribution:** comment-a-keyword → DM-the-link funnel (per-post keyword above).

## Output & git

Each run writes `higgs/<name>_showcase_<date>/` containing `0_*.png … 8_*.png`,
`caption.txt`, `manifest.json`. **These PNGs and any hero photos are gitignored**
(regenerable media) — only these builder scripts are tracked. The congress post also
reads a Capitol hero photo (`higgs/hero_congress_*.png`, gitignored) as a per-slide
varied background; regenerate/replace that asset locally if missing.
