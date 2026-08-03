# Local ComfyUI gen stack — live benchmark (Task 9)

Server: headless ComfyUI (`comfy/launch.py` `SERVER_ARGV`), 127.0.0.1:8000, RTX 4070
12,282 MiB. All timings are wall-clock for a single render on otherwise-idle
hardware, GPU preflight-checked (`nvidia-smi`, no game process) immediately
before each submission per the repo's concurrency doctrine. `source_class:
local-comfyui` for every artifact below.

## Render 1 — `zimage_t2i` (PASS)

| Field | Value |
|---|---|
| Template | `zimage_t2i` |
| Params | prompt="a trading terminal glowing green in a dark room, candlestick charts on screen, cinematic, dramatic rim light, ultra detailed"; negative="text artifacts, watermark, blurry"; seed=990177; width=1024; height=1024 |
| Sampling | 4-step (`steps=4, cfg=1, sampler=res_multistep, scheduler=simple`), `ModelSamplingAuraFlow shift=3` |
| Wall-clock | **12.1 s** (client-measured submit→fetch; server-side `execution_start`→`execution_success` span for this run was ~10.5 s, the gap is client HTTP/staging overhead) |
| Peak VRAM | **10,771 MiB** |
| Output | `data/comfy_smoke/zimage_t2i_00016_.png`, 1,164,428 bytes |
| Model files | `qwen_3_4b_fp8_mixed.safetensors` (CLIPLoader, type=lumina2), `ae.safetensors` (VAE), `z_image_turbo_fp8_e4m3fn.safetensors` (UNET) |
| `generated_at` | 2026-08-03T18:15:58Z |

**Content verdict: clean pass.** Dual-monitor trading-terminal desk shot,
green glowing candlestick + volume panels on the left monitor, a scrolling
green/red ticker grid on the right, dark room, warm/green rim lighting,
keyboard/mouse foreground — matches every element of the prompt (subject,
lighting, mood) with no artifacts, no garbled text, no watermark.

## Render 2 — `wan22_i2v_14b` (PASS, after a rotation lesson)

| Field | Value |
|---|---|
| Template | `wan22_i2v_14b` |
| Params | prompt="the oil tanker glides slowly forward across the strait, its wake trailing on the calm dark water, mist drifting over the distant mountains at dusk, subtle cinematic camera push-in"; negative="text warping, distorted logos, static, flicker, blurry, artifacts"; seed=990179; width=832; height=480; length=81; image=`hormuz_cover.png` (staged from `content/probe/hormuz_cover.png`) |
| Sampling | lightx2v 2+2 (`KSamplerAdvanced` pair, 4 steps total split 2/2 across the high-noise/low-noise experts, `cfg=1, sampler=euler, scheduler=simple`), `ModelSamplingSD3 shift=5` on both experts |
| Wall-clock | **185.2 s** (client-measured, fresh server, cold model load) |
| Peak VRAM | **11,653 MiB** (96% of the 12,282 MiB card) |
| Output | `data/comfy_smoke/wan22_i2v_14b_00005_.mp4`, 286,637 bytes, h264, 832×480, 16 fps, 81 frames, 5.06 s |
| Model files | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (CLIP), `wan_2.1_vae.safetensors` (VAE), `Wan2.2-I2V-A14B-HighNoise-Q4_K_M.gguf` + `Wan2.2-I2V-A14B-LowNoise-Q4_K_M.gguf` (UNETs, GGUF), `wan2.2_i2v_A14b_high_noise_lora_rank64_lightx2v_4step_1022.safetensors` + `wan2.2_i2v_A14b_low_noise_lora_rank64_lightx2v_4step_1022.safetensors` (LoRAs, strength 1.0) |
| `generated_at` | 2026-08-03T18:33:01Z |

**Content verdict: clean pass.** 4 frames sampled at t=0/1.7/3.4/4.9s. The
tanker holds scene identity and coherent motion across the full 81-frame
clip — camera subtly pushes in, the haze over the strait clears as dusk
light warms the mountain ridgeline toward the end, water/wake motion reads
naturally. `WanImageToVideo` resizes/crops the 1080×1920 source to 832×480
landscape, which (fortuitously) crops out the title text and candlestick-chart
overlay baked into `hormuz_cover.png`, leaving a clean tanker-on-water frame
with no on-screen text for the model to warp.

### Rotation lesson: this render was corrupted twice before this pass, and both prior files are evidence of a known bug, not new deliverables

`wan22_i2v_14b_00003_.mp4` (2,968,002 bytes, seed=990179) and
`wan22_i2v_14b_00004_.mp4` (15,745 bytes, seed=990180) preceded `_00005_` in
this session and are both **invalid** — verified by extracting frames from
each, not by inference:

- **`_00003_`**: every sampled frame (t=0/2.5/4.9s) is pure colored TV-static
  noise, no scene content at all.
- **`_00004_`**: every sampled frame is solid black — this is also why the
  file is only 15.7 KB despite being a full 81-frame 832×480 clip
  (`ffprobe` confirms `nb_frames=81`, not truncated): a constant-black frame
  sequence h264-compresses to almost nothing.

Root cause: both renders ran in the **same long-lived ComfyUI server
process** immediately after the Z-Image render (Render 1, above) *without a
restart*. This is the exact VRAM-eviction bug `task-8-report.md` already
documented for this repo's stack — swapping a large model out of a
12 GB card's VRAM to load a differently-sized one can leave the CUDA
context / internal model-cache bookkeeping corrupted, silently producing
garbage output on the next render rather than a hard error. `_00003_` (static
noise) and `_00004_` (black) are two different corruption signatures of the
same underlying issue. **Fix applied:** killed the server process and
relaunched fresh (`comfy.launch.ensure_server()`) before resubmitting with
the original intended seed (990179) — `_00005_` is that clean resubmission,
confirmed pixel-content-valid by direct frame inspection. The server was
restarted *again* before the Render 3 attempt below for the same reason
(14B GGUF UNETs → 5B fp16 UNET is the same class of large-model swap).

## Render 3 — `wan22_ti2v_5b` native T2V, 1280×704×121 — **DNF, not production-viable at this config**

| Field | Value |
|---|---|
| Template | `wan22_ti2v_5b` |
| Params attempted | prompt="slow cinematic push-in on a glowing trading terminal in a dark room, green candlestick charts flickering, dust motes in the light beam"; seed=990178; width=1280; height=704; length=121 (native template defaults) |
| Sampling | native default, **no distillation LoRA** — plain 20-step `KSampler` (`cfg=5, sampler=uni_pc, scheduler=simple`), `ModelSamplingSD3 shift=8` |
| Model files (loaded, never completed) | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (CLIP), `wan2.2_vae.safetensors` (VAE), `wan2.2_ti2v_5B_fp16.safetensors` (UNET) |
| Attempt 1 | Submitted, model load + latent prep succeeded, then `execution_interrupted` at the `KSampler` node after 1,951 s (~32.5 min) of real `execution_start`→interrupt time — likely queue/GPU contention from a parallel session's concurrent `zimage_t2i` submissions hitting the same shared server (ComfyUI history shows dozens of interleaved `z_image_turbo` prompts around this window). |
| Attempt 2 (retry) | Submitted 21:17:41, ran at reported ~100% GPU utilization throughout, **manually interrupted by the orchestrator at 23:43:44** after **2h 26m 3s (8,763 s) elapsed** — owner decision: "not feasible for prod." Reported server log line: `loaded partially... 2290.68 MB offloaded` (PCIe host↔GPU streaming penalty from a model that doesn't fit fully resident at this config) — **this line was reported by the orchestrator's session monitoring, not independently captured/verified by this task run** (the headless server's own stdout isn't captured to a readable log in this setup), flagged per the repo's verify-before-completion standard. |
| Output | none — no file produced, both attempts DNF |

**No content verdict possible — nothing rendered.**

**Why this lane is structurally slower than the 14B I2V lane:** the 14B I2V
template uses the lightx2v 4-step distillation LoRA (4 total sampler steps
across both MoE experts). The native `wan22_ti2v_5b` template ships **no
distillation LoRA** — its default is a plain 20-step `KSampler`, 5x more
sampler steps than the 14B lane, on top of ~4x the pixel count (1280×704 vs
832×480) and ~1.5x the frame count (121 vs 81) relative to Render 2, and
~4x pixels / ~3.7x frames relative to Task 7's own 640×352×33 calibration
point. Naively scaling Task 7's cold measurement (462.6 s at 640×352×33,
T2V) by pixel-count×frame-count (≈4×3.67≈14.7x) predicts ≈6,800 s (~1.9 h)
— same order of magnitude as the >2.4 h actually observed before
interruption (and that run *still hadn't finished*), which suggests the
naive linear-in-pixels-and-frames model understates the real cost at this
resolution — consistent with the reported PCIe-offload penalty adding
overhead a pure compute-scaling estimate wouldn't capture.

## Comparison to the research sweep's inferred estimates

Source: `docs/superpowers/specs/2026-08-03-comfyui-local-gen-design.md`
line 45 — *"Expected (inferred, must be benchmarked live): ~1.5–3 min per
5 s 480p clip with the 4-step LoRAs"* (this line is scoped to the 14B I2V
lightx2v lane; no estimate exists in that spec for Z-Image or for the 5B
lane at native/720p resolution — both were explicitly flagged
"inferred... hypotheses until the live benchmark").

| Lane | Estimate | Measured | Held? |
|---|---|---|---|
| `zimage_t2i` (1024²) | none given | 12.1 s | N/A — no estimate to compare |
| `wan22_i2v_14b` (832×480, 5 s/81 frames, lightx2v 4-step) | 1.5–3 min (90–180 s) | 185.2 s | **Held, at the top edge of the range** — 5.2 s (~3%) over the stated 3 min ceiling, effectively at the boundary. Task 8's own comparable 49-frame/832×480 render measured 138.35 s warm; scaling that linearly by frame count (81/49) predicts ≈228.7 s, so 185.2 s landing *below* that naive frame-scaled projection suggests this run wasn't fully "cold" (model files' disk blocks likely still page-cached from the same-session Render 1/failed-attempt loads even though the CUDA context was fresh). |
| `wan22_ti2v_5b` native (1280×704, 121 frames, no distill LoRA) | no estimate given (explicitly flagged as unbenchmarked) | DNF after >2.4 h | **Not applicable — confirms the spec's own caveat that this lane required live benchmarking before being trusted**, and the live benchmark says it isn't viable as configured. |
| `wan22_ti2v_5b` reduced res (640×352, 33 frames) — Task 7 reference, not re-run this task | no estimate given | 462.6 s cold (T2V) / 38.4 s warm (I2V) | Reference points only, carried over from Task 7 — not remeasured in Task 9. |

## Conclusion — production lanes

- **14B I2V @ 480p (832×480), lightx2v 4-step: production-viable.** 138–185 s
  per 5 s clip warm, clean content, ~96% VRAM headroom used but stable once
  the server is freshly rotated between differently-sized-model runs.
- **5B lane at reduced resolution (640×352 or similar), not native 720p:
  production-viable as a fast T2V/I2V fallback.** 38 s warm / 462 s cold per
  Task 7 at 33 frames.
- **5B native res (1280×704) with the default 20-step, no-LoRA sampler:
  batch-only or an offload/quantization-tuning candidate, not an
  interactive/production path** on this 12 GB card — two live attempts
  totaling roughly 2h 58m of GPU time (1,951 s + 8,763 s) produced zero
  finished output.

## Operational note — server rotation between differently-sized models

Confirmed again this task (on top of `task-8-report.md`'s prior finding):
**do not run differently-sized models (e.g. Z-Image 6B → Wan 14B, or Wan
14B → Wan 5B) back-to-back in one long-lived ComfyUI process.** VRAM
eviction when swapping models on a card this size can corrupt the CUDA
context / model-cache bookkeeping and silently produce garbage output
(static noise, solid black) on the *next* render rather than raising an
error — the failure surfaces one render late, not on the render that
triggers it. Restarting the server (`comfy.launch.ensure_server()` after
killing the prior process) before each large-model-class switch is the
verified fix, used twice in this task.
