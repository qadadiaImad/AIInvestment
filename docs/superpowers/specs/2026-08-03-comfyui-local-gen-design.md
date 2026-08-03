# Local open-source image/video generation via ComfyUI — design

**Date:** 2026-08-03 · **Status:** approved by owner (video-first, Claude-driven, phased) ·
**Machine:** Windows 11, RTX 4070 SUPER 12 GB VRAM, 32 GB RAM, driver 591.86, C: 53 GB free (after removing the redundant 22 GB flux1-dev full checkpoint).

## Goal

Make the existing **ComfyUI Desktop** install (core 0.13.0, user data `C:\Users\imadq\Documents\ComfyUI`)
a third generation backend alongside Higgsfield and grok: **open-weight video** (priority) and
faster open-weight images, drivable both from the GUI and **headless by Claude** through the local
ComfyUI API (`127.0.0.1:8000`, verified open, no auth).

## Verified context (2026-08-03 web sweep, 4-agent workflow, all claims source-backed)

- Wan 2.2 (Apache 2.0) is the newest open-weight Wan; "Wan 2.5/2.6" are API-only; "Wan 2.7 open
  weights" sites are SEO fakes (checked official GitHub/HF orgs).
- HunyuanVideo 1.5 **excluded**: Tencent Community License territorially excludes the EU (verified
  LICENSE text). Owner assumed EU (.fr).
- LTX-2/2.3 (weights open since 2026-01) **deferred**: 19–22B + mandatory Gemma-12B encoder
  (≥9.45 GB at smallest quant) — not a sensible daily driver at 12 GB; NVFP4 gains are Blackwell-only.
- ComfyUI 0.13.0 already has native Wan 2.2 and Z-Image support; core 0.30.0 is current. Krea 2
  needs core ≥0.26 → deferred behind the core update.
- The `cu130` log warning gates ComfyUI's whole comfy_kitchen CUDA backend (incl. Ada-compatible
  FP8/INT8 kernels) on `torch.version.cuda >= 13`; torch 2.9+cu130 has a live Windows crash issue
  (Comfy-Org/ComfyUI #10389) → upgrade is attempt-with-rollback, done last.

## Phase 1 — Wan 2.2 video stack (~29 GB, Apache 2.0)

Downloads into `Documents\ComfyUI\models\` (**verify byte size on the HF file page immediately
before each download** — several sizes below are search-snippet-sourced):

| File | Repo | Size | Dir |
|---|---|---|---|
| Wan2.2-I2V-A14B **high**-noise GGUF Q4_K_M | QuantStack/Wan2.2-I2V-A14B-GGUF | ~9.65 GB | `unet/` (GGUF loader) |
| Wan2.2-I2V-A14B **low**-noise GGUF Q4_K_M | QuantStack/Wan2.2-I2V-A14B-GGUF | ~9.65 GB | `unet/` |
| lightx2v 4-step LoRA, I2V high+low (`*_rank64_lightx2v_4step_1022`) | lightx2v/Wan2.2-Distill-Loras | ~0.64+0.74 GB | `loras/` |
| `wan2.2_ti2v_5B_fp16.safetensors` (fast fallback; covers T2V) | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 10 GB | `diffusion_models/` |
| `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | ~6.74 GB | `text_encoders/` |
| VAE(s) — `wan2.2_vae.safetensors` (TI2V-5B) **and whichever VAE the official 14B I2V template references (likely wan_2.1_vae — confirm from the template, do not assume)** | Comfy-Org repackaged repos | ~1.4–1.7 GB | `vae/` |

Workflows: start from ComfyUI's **native** template for each (14B I2V with the two-expert
MoE chain + per-expert lightx2v LoRA at ~4 steps/expert, no CFG; TI2V-5B single-model), saved as
GUI workflow files **and** exported API-format JSON. Native nodes only; no WanVideoWrapper
(its own README says don't use it unless a feature is missing from core). VAE tiling on for >512px.
Expected (inferred, must be benchmarked live): ~1.5–3 min per 5 s 480p clip with the 4-step LoRAs.

**Optional image add-on (approved):** Z-Image-Turbo (6B, Apache 2.0, 8-step 1024²):
`z_image_turbo_fp8_e4m3fn.safetensors` (~6.15 GB) + `qwen_3_4b.safetensors` fp8 encoder
(~5.63 GB) + `ae.safetensors` VAE (~0.34 GB) from Comfy-Org/z_image_turbo (+ drbaph or Kijai fp8
for the diffusion file). Disk after everything: ~12 GB headroom remains.

## Phase 2 — Claude-driven wiring (`scripts/comfy/`, TDD)

- `client.py` — minimal stdlib/requests client for the canonical local API: `POST /prompt`
  (returns prompt_id), poll `GET /history/{id}` (polling, not websocket — simpler, adequate),
  fetch outputs via `GET /view`. Parameterized template loading: fill prompt text, input image,
  seed, resolution, frame count into the exported API-format JSONs in `scripts/comfy/templates/`.
- `launch.py` — headless server start when the Desktop app is closed: run
  `Documents\ComfyUI\.venv\Scripts\python.exe` against the app's bundled
  `resources\ComfyUI\main.py` with the exact argv captured live from `/system_stats`
  (same ports/dirs → same models, same outputs). Detect an already-running server first.
- `tests/` — pytest: template parameter-injection unit tests; client tests against mocked HTTP;
  one opt-in live smoke test (skipped unless server reachable).
- Outputs land in `Documents\ComfyUI\output\`; the client copies results to a caller-given path.
  Every generated asset gets provenance stamps (model files + hashes where published, workflow
  JSON, `retrieved_at`-style `generated_at` UTC) per repo Rule #3, and NC-use noted per the
  content-non-commercial policy (all Phase-1 models are Apache 2.0 anyway).

## Phase 3 — platform upgrades (each reversible, done after 1–2 work)

1. **torch → cu130** in the Desktop venv: `pip freeze` snapshot → `python.exe -m pip install
   torch torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu130` →
   relaunch, run the Phase-1 smoke renders; on any failure pin back to `2.7.1+cu128`.
   Success criterion: the cu130 warning gone, renders still correct.
2. **ComfyUI core update** via the Desktop updater toward 0.30.x (unlocks Krea 2, LTX-2.3
   templates, GGUF VRAM-manager fixes; check the open GGUF utilization regression #11081
   behavior before/after). May require one GUI click by the owner — not blocking anything.

## Verification (before "done")

Real renders shown to the owner (house rule: show, don't describe): one Z-Image still, one
TI2V-5B clip, one 14B I2V clip animating an existing reel still; report measured wall-clock,
peak VRAM, and file sizes. Uploads for phone viewing via the Higgsfield media flow.

## Risks

- **Disk**: ~41 GB new files vs 53 free → ~12 GB headroom; downloads sized-checked before start.
- **cu130 instability** (#10389) → rollback pin, done last, after everything already works.
- **GGUF VRAM under-utilization regression** (#11081) → if throughput looks low, test
  fp8_scaled 14B variants or adjust; TI2V-5B is the guaranteed-fit fallback.
- **Timing estimates are inferred** from 4090/3090/3080 data — treated as hypotheses until the
  live benchmark.
- **VAE mismatch** for 14B (2.1 vs 2.2 VAE) → resolved by reading the official template, not memory.
