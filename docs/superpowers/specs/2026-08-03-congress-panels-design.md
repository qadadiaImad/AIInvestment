# Congress Panels — series design

**Date:** 2026-08-03 · **Status:** pilot sanctioned by owner brief (this session); full build
awaits owner spec review · **Working title:** Congress Panels

## What it is

A JoJo-adjacent high-drama manga/comic series. Each episode storytells ONE real, freshly
detected congressional stock filing from this repo's data engine as a news-story arc:
**hook → tension (committee/policy leverage over the traded sector) → reveal (the trades,
as filed ranges) → honest "does this matter" verdict**, with party/ideology subtext where
the data supports it. Educational parody, never an accusation. Non-commercial.

## Editorial rails (binding, from owner brief + social-copy/narrative memories)

- No first person. Attribute to "filings" / "the public record" / "reports".
- Frame as "oversees X, traded X" — transparency, never wrongdoing.
- Amounts are STOCK Act range buckets, verbatim from the parsed PTR. Label filed vs
  reported vs rumored. Numbers are NEVER model-authored (house rule 10.1): every ticker,
  date, and amount on screen is injected by code from the parsed filing JSON, which is
  force-added to git as evidence.
- Real members appear as stylized editorial caricatures (public figures, parody).
  Every panel carries an on-image footer: parody · based on public House filings
  (DocID) · educational, not advice · not an accusation.
- Disclaimers stay THIN — one small footer line, never stacked into the story copy.
- Never put JJBA/Araki proper nouns (characters, Stands, "style of Hirohiko Araki") in
  prompts. The JoJo flavor comes from generic dramatic-manga tokens and (later) a style
  LoRA; the parody's grounding is the real-public-figure subject matter, not the source
  artist.

## Architecture (verified by the 2026-08-03 research sweep, wf_d1daa32c-333)

Four-agent web sweep, all claims source-cited in the workflow journal. Decisions:

1. **Series base model: Illustrious-XL** (SDXL-anime lineage; FAIPL-1.0, no commercial
   restriction — moot, content is NC). Why: largest anime LoRA ecosystem; JoJo/Araki-style
   LoRAs already published on Civitai (e.g. civitai.com/models/607276); SDXL fits 12GB at
   1024px unquantized; kohya sd-scripts trains SDXL LoRA in fp16 — exactly what Kaggle's
   bf16-less Turing T4s need, with live community notebooks proving it; and the installed
   `comfyui_ipadapter_plus` supports SDXL (NOT Z-Image/FLUX), so reference conditioning
   works only on this lineage.
2. **Local draft engine: Z-Image-Turbo** (installed, Apache 2.0, ~14s/1024px). Used for
   fast iteration and the pilot. NOT the series LoRA base: turbo-distill LoRA training is
   documented experimental (musubi-tuner docs), no proven-safe fp16/bf16 choice on T4.
3. **Character consistency (hybrid):** one series-style LoRA + per-character LoRAs
   (15–30 curated images each, the researched sweet spot) for the recurring cast only,
   stacked at reduced weights, + IPAdapter single-reference conditioning per character
   (research: one strong full-body reference beats a turnaround sheet). Max ~1–2 character
   LoRAs active per panel (SDXL stacking limit); multi-character panels use regional
   prompting (Impact-Pack RegionalPrompt) or per-character render + composite.
   Qwen-Image-Edit-2511 GGUF identity pass = future experiment (tight Q4 fit on 12GB,
   unbenchmarked on caricature faces).
4. **Kaggle training lane** (MCP verified live 2026-08-03; 30h GPU/week = 108000s):
   curate character sheets locally → private Kaggle Dataset per character (kohya folder
   format `N_name/img.png+img.txt`) → fork `zombiksss/sdxl-lora-trainer-for-kaggle`
   (kohya lineage, fp16 default, single T4; pointed at the Illustrious checkpoint) →
   Save&RunAll background session → pull `.safetensors` (50–230MB) via
   `download_notebook_output_zip`, promote to a private versioned Kaggle Model per
   character → drop into `Documents\ComfyUI\models\loras`. First run doubles as the
   wall-clock + unattended-run verification (both unmeasured; see caveats).
5. **Division of labor:** local 4070 = interactive panel renders (owner games on it —
   nvidia-smi preflight before every batch); Kaggle = all LoRA training + overflow batch
   renders when local is busy. One prompt-spec (subject/action/style/negative + seed +
   size) renders on either backend.
6. **Page production:** panels are generated INDIVIDUALLY; page layout, gutters, speech
   bubbles, captions, SFX lettering, and the compliance footer are composited in code
   (PIL/HTML) — no in-model dialogue text ever (Z-Image's own docs admit multi-line
   degradation; SDXL is worse; post lettering is editable and audit-able). Comic
   lettering font; numbers injected from the parsed filing JSON only.

## Episode pipeline (per episode)

```
detect  : targeted fresh-PTR pull (index sorted by FilingDate desc) → parse → sector join
select  : story score = committee/jurisdiction relevance × recency × size × pattern
script  : hook/tension/reveal/verdict beats + copy under rails (this file's §rails)
board   : 6-10 panels, one beat each; prompt-spec per panel; cast sheet refs
render  : local ComfyUI (Illustrious + style LoRA + character LoRA/IPAdapter)
letter  : PIL/HTML pass — bubbles, captions, SFX, footer, numbers-from-JSON
assemble: 4:5 carousel slides (one panel per slide) + optional 9:16 reel cut
verify  : frame extraction + copy scrub (no first person, no outlet names, rails)
```

## Pilot (this session, owner-sanctioned)

Episode 1: Rep. Dan Newhouse (R-WA04) PTR filed 2026-07-17 (DocID 20034998) — member of
the House Select Committee on Strategic Competition with the CCP; 31 same-day (07/10)
transactions, every row $1,001–$15,000: partial sells NVDA/AMD/AMAT/GOOGL/…, buys
MU/ANET/APH/DUK/FE/…. Honest verdict: pattern reads as advisor-style rebalance, not a
conviction bet — the drama is the appearance, the verdict is the honesty.
Pilot renders 4 test panels on Z-Image-Turbo (draft engine) + PIL lettering, shown in
chat. Purpose: validate prompt-spec, B&W-manga look without a LoRA, lettering pipeline,
and the compliance footer — before any training spend.

## Not in scope yet (needs owner review of this spec)

- Downloading Illustrious-XL (~6.9GB — verify exact size/hash on HF before download).
- Designing + training the recurring cast (which members recur, caricature canon).
- Kaggle training runs (burns GPU quota; first run is also the verification run).
- Distribution format lock (4:5 carousel vs 9:16 reel vs both).

## Risks / caveats

- Kaggle session-length (12h) and unattended Save&RunAll behavior: search-sourced, not
  read from an authoritative page — verify with the first real run before scheduling.
- LoRA training wall-clock on T4 unmeasured (community estimate 30–45min/character-LoRA
  is unverified).
- Z-Image pilot panels are a style approximation; the series look locks only after the
  Illustrious + style-LoRA test.
- Caricature-identity fidelity of every consistency technique is unbenchmarked on
  exaggerated faces — the cast pilot must test 1–2 characters before batch training.
- Editorial/defamation posture rests on: parody labeling, public-figure subjects,
  public-record facts, range-bucket amounts, no-accusation framing. Any episode that
  can't meet all five doesn't ship.
