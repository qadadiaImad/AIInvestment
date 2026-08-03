# Local ComfyUI generation backend

Third gen backend beside Higgsfield and grok: free, unlimited, runs on this
machine's RTX 4070 SUPER (12,282 MiB VRAM). Drives the existing **ComfyUI
Desktop** install (`Documents\ComfyUI`) headless through its own local HTTP
API (`127.0.0.1:8000`, no auth) — same models, same output folder as the
GUI. Built 2026-08-03; spec is
`docs/superpowers/specs/2026-08-03-comfyui-local-gen-design.md`, ledger is
`.superpowers/sdd/2026-08-03-comfyui-local-gen/progress.md`.

## Model inventory

All Apache 2.0. Installed under `Documents\ComfyUI\models\<dir>\`; sizes
are exact bytes from live HF resolution (`comfy.manifest.resolve()`, Task
1, 2026-08-03), not estimates.

| Group | File | Repo | Size | Dir |
|---|---|---|---|---|
| video-5b (Wan 2.2 TI2V-5B, T2V+I2V fallback) | `wan2.2_ti2v_5B_fp16.safetensors` | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 10.00 GB | `diffusion_models/` |
| | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 6.74 GB | `text_encoders/` |
| | `wan2.2_vae.safetensors` | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 1.41 GB | `vae/` |
| | `wan_2.1_vae.safetensors` | Comfy-Org/Wan_2.2_ComfyUI_Repackaged | 0.25 GB | `vae/` |
| video-14b (Wan 2.2 I2V-A14B GGUF, quality, lightx2v 4-step) | `Wan2.2-I2V-A14B-HighNoise-Q4_K_M.gguf` | QuantStack/Wan2.2-I2V-A14B-GGUF | 9.65 GB | `unet/` |
| | `Wan2.2-I2V-A14B-LowNoise-Q4_K_M.gguf` | QuantStack/Wan2.2-I2V-A14B-GGUF | 9.65 GB | `unet/` |
| | `..._high_noise_lora_rank64_lightx2v_4step_1022.safetensors` | lightx2v/Wan2.2-Distill-Loras | 0.63 GB | `loras/` |
| | `..._low_noise_lora_rank64_lightx2v_4step_1022.safetensors` | lightx2v/Wan2.2-Distill-Loras | 0.74 GB | `loras/` |
| image (Z-Image-Turbo, 4-step still) | `z_image_turbo_fp8_e4m3fn.safetensors` | drbaph/Z-Image-Turbo-FP8 | 6.15 GB | `diffusion_models/` |
| | `qwen_3_4b_fp8_mixed.safetensors` | Comfy-Org/z_image_turbo | 5.63 GB | `text_encoders/` |
| | `ae.safetensors` | Comfy-Org/z_image_turbo | 0.34 GB | `vae/` |

`drbaph/Z-Image-Turbo-FP8` is a community repackage — the official
`Comfy-Org/z_image_turbo` ships bf16/int8/nvfp4 but no fp8 variant. Only
file existence/size were verified live, not the repo's provenance.
`wan_2.1_vae.safetensors` downloads under the `video-5b` group but is the
VAE the **14B I2V** template actually references, not the 5B one (confirmed
by reading `video_wan2_2_14B_i2v.json` directly, Task 7) — don't assume it's
5B-only.

## How to generate

`scripts/comfy/client.py`'s `ComfyClient.generate(template, out_dir,
timeout=3600, **params)` submits, polls `/history`, and fetches every
output. Needs a headless server up (`comfy.launch.ensure_server()` first
if not).

**`zimage_t2i`** — text-to-image, 4-step. Params: `prompt, negative, seed,
width, height`. Measured **12–14 s** at 1024×1024 (12.1 s Task 9, 14.08 s
Task 6), peak VRAM 10,771 MiB.

```python
from comfy.client import ComfyClient

outs = ComfyClient().generate(
    "zimage_t2i", "data/out",
    prompt="a trading terminal glowing green in a dark room, cinematic",
    negative="text artifacts, watermark, blurry",
    seed=990177, width=1024, height=1024,
)
```

**`wan22_ti2v_5b` / `wan22_ti2v_5b_i2v`** — fast fallback video, no
distillation LoRA (native 20-step KSampler). T2V and I2V are two template
files sharing every param but `image` (`prompt, negative, seed, width,
height, length[, image]`) — API-format JSON can't express the native
template's UI-only bypassed `LoadImage` node. I2V needs
`client.stage_input(path)` first, then pass its return value as `image`.
Measured at 640×352×33f: **38.4 s warm / 462.6 s cold**. Native default
res (1280×704×121f, no LoRA): **DNF — 2h26m, not a production lane**
(see below).

```python
client = ComfyClient()
staged = client.stage_input("content/probe/hormuz_cover.png")
outs = client.generate(
    "wan22_ti2v_5b_i2v", "data/out",
    prompt="the telescope on the desk gently rocks as warm light sweeps",
    negative="blurry, low quality, static, distorted",
    seed=5, width=640, height=352, length=33, image=staged, timeout=900,
)
```

**`wan22_i2v_14b`** — quality video, I2V only (`image` required), two-expert
GGUF MoE chain + lightx2v 4-step LoRA (4 total sampler steps, not 20).
Params: `prompt, negative, seed, width, height, length, image`. Measured
**185.2 s** at 832×480×81f (Task 9 deliverable), **138.35 s** at
832×480×49f — page-cache warm on a freshly restarted server, not GPU-
resident warmth (`task-8-report.md`). Peak VRAM **11,653 MiB** at 81f
(Task 9) and **≥11,757 MiB** at 49f (Task 8 — a floor, not a confirmed
peak; the VRAM poller stopped sampling ~58s before that render finished).
This is the production video lane.

```python
client = ComfyClient()
staged = client.stage_input("content/probe/hormuz_cover.png")
outs = client.generate(
    "wan22_i2v_14b", "data/out",
    prompt="the oil tanker glides slowly forward across the strait, "
           "its wake trailing on the calm dark water",
    negative="text warping, distorted logos, static, flicker, blurry",
    seed=990179, width=832, height=480, length=81, image=staged,
    timeout=1800,
)
```

**The DNF:** two `wan22_ti2v_5b` attempts at native 1280×704×121f — one
lost to queue contention after 1,951 s, a clean retry manually stopped at
owner instruction after **2h 26m 3s** ("not feasible for prod"). Neither
produced output. Scaling the 640×352×33f cold measurement by pixel×frame
count predicts ~6,800 s — same order of magnitude as observed, so this is
this lane's real cost at native res, not a fluke to retry. **5B production
use stays at reduced resolution (640×352 or similar), never native 720p.**

## Server lifecycle

`comfy.launch.ensure_server()` probes `GET /system_stats`; if down, it launches
`Documents\ComfyUI\.venv\Scripts\python.exe` against the Desktop app's own
`resources\ComfyUI\main.py`, with the exact argv captured live from
`/system_stats` (`SERVER_ARGV` in `launch.py`) — same ports/dirs/database as
the GUI, spawned detached.

**Port 8000 is shared with the ComfyUI Desktop Electron GUI — never run
both.** Same port, same sqlite DB. Task 8 found the Electron app itself
racing the headless launcher for the port, running a system Python that
lacked the `gguf` package the GGUF template needs — check `Get-Process
ComfyUI` before assuming the headless server owns the port.

**The queue interleaves submissions from multiple sessions — that is not
the same as running safely under contention.** Observed live 2026-08-03: a
parallel session's `zimage_t2i` submissions interleaved in `/history` with
the 5B DNF's Attempt 1 (see below), which ran 1,951 s and then hit
`execution_interrupted` at the `KSampler` node — likely caused by that
same contention (`benchmark.md`'s own hedge: "likely queue/GPU
contention"), and a **failed render**, not merely a slow one. Budget for
outright failure/retry under concurrency, not just added latency.

**GPU etiquette.** `nvidia-smi` preflight before every submission — the
owner games on this GPU, and a concurrent game is not a Python-catchable
failure: Task 6's first render crashed the whole ComfyUI backend process
outright (no traceback, port stopped listening) with Elden Ring running.
Never submit into game contention.

**Restart, don't `/free`, when switching model classes.** Swapping a
large model out of a 12 GB card's VRAM to load a differently-sized one
(Z-Image ↔ Wan 14B ↔ Wan 5B) can corrupt the CUDA context / ComfyUI's
model-cache bookkeeping — `task-8-report.md` first hit this as a hard CUDA
`invalid argument` error; Task 9's benchmark hit the worse variant with
**no error at all**, just silent garbage on the next render (TV-static
noise, then solid black — two signatures of the same bug). The verified
fix both times was killing the process and calling `ensure_server()`
fresh; a bare `POST /free` call is unverified for this failure mode, not a
substitute for a restart.

## Platform state

**torch 2.13.0+cu130** since 2026-08-03 (Task 10), up from 2.7.1+cu128.
Unlocks `comfy_kitchen`'s CUDA backend (Ada FP8/INT8 kernels): server log
went `cuda: {disabled: True}` → `{disabled: False}`. No rollback needed —
the zimage canary rendered visually identical before/after. Rollback pin
at `data/comfy_venv_freeze_pre_cu130.txt` (`torch==2.7.1+cu128` etc.) if
ever needed. **Not yet re-verified:** the Wan 5B/14B video paths under
cu130 — only the zimage canary was re-tested post-upgrade.

**ComfyUI core 0.13.0**, unchanged. Desktop v0.9.4 (bundling core 0.22.3)
is available as an owner one-click update — recommended for GGUF/template
fixes, not applied yet, non-blocking (Task 11). **Krea 2 needs core
≥0.26** — out of reach even after that update.

## Excluded or deferred, and why

- **HunyuanVideo 1.5 — excluded.** Tencent's Community License territorially
  excludes the EU (verified from the LICENSE text); the owner is assumed EU
  (.fr).
- **LTX-2/2.3 — deferred**, not excluded (spec's own word). 19–22B UNet plus
  a mandatory Gemma-12B text encoder (≥9.45 GB at smallest quant) doesn't fit
  this 12 GB card sensibly; its NVFP4 memory gains are Blackwell-only, no
  help on an Ada card. Revisit if a smaller-footprint variant ships.
- **"Wan 2.5/2.6/2.7 open weights"** — 2.5/2.6 are API-only, no open weights
  exist; "Wan 2.7 open weights" sites are SEO fakes (checked against the
  official Wan GitHub/HF orgs directly).

## Provenance

Every generated asset gets `generated_at` (UTC) and `source_class:
local-comfyui`, the same discipline as any other retrieval in this repo
(CLAUDE.md §0 Rule #3). Content produced here is non-commercial (owner
declaration, 2026-08-02) — moot for licensing since every Phase-1 model is
already Apache 2.0, but still the operative use restriction on output.

## Follow-ups parked

- Re-run the Wan 5B/14B video live tests under torch 2.13.0+cu130 — only
  the zimage canary has been verified on the new stack.
- A lightx2v-style distillation LoRA for the 5B lane, to see if it closes
  the gap to the 14B lane's step count — unverified, not attempted.
- Q5_K_M step-up for the 14B GGUF lane: Q4_K_M already peaks ~96% VRAM at
  832×480×81f, so headroom needs checking before a heavier quant.
- A Kaggle GPU-offload lane for work this 12 GB card can't do at native
  res (the 5B 720p case above) — see
  `references/kaggle-manga-session-prompt.md`.

---

*Educational/research use only. Local generation, not investment advice.*
