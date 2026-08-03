# Local ComfyUI Comic Pipeline — setup & usage

A local-GPU image/comic generation pipeline: **ComfyUI** (headless HTTP API) driven by a
small stdlib Python wrapper. Generates hero art, backgrounds, and full comics with
**consistent characters** (IPAdapter) and **story-telling panels** (a panel-schema +
two-pass "scene → face-lock"). Runs free/unlimited on a local NVIDIA GPU (tested on a
6 GB RTX 4050 — SDXL images ~26 s, +IPAdapter ~45 s, two-pass ~55 s).

Two tracked files are all you need on the code side:
- `scripts/comfy_gen.py` — the generator (talks to the ComfyUI API; base / +LoRA / +IPAdapter / two-pass)
- `scripts/comic_pipeline.py` — the reusable `Panel` schema (composes story-telling prompts)

Everything below (ComfyUI + models) lives **outside** the repo and is set up once per machine.

---

## 1. Install ComfyUI (Windows portable — bundles Python + CUDA torch)

Download the NVIDIA portable from the ComfyUI releases (Comfy-Org/ComfyUI), extract with 7-Zip:
```
https://github.com/Comfy-Org/ComfyUI/releases  →  ComfyUI_windows_portable_nvidia.7z (~2 GB)
```
Extract to e.g. `C:\Users\<you>\comfy\ComfyUI_windows_portable`. (macOS/Linux: install ComfyUI
normally; the wrapper only needs the API on `127.0.0.1:8188`.)

Verify the bundled torch sees the GPU:
```
./python_embeded/python.exe -c "import torch;print(torch.cuda.get_device_name(0))"
```

## 2. Models (place under `ComfyUI/models/…`)

| File | → dir | Source |
|---|---|---|
| `sd_xl_base_1.0.safetensors` (6.9 GB) | `checkpoints/` | HuggingFace `stabilityai/stable-diffusion-xl-base-1.0` |
| `comic_eldritch.safetensors` (102 MB) | `loras/` | Civitai model version **305491** (Eldritch Comics, trigger `comic book`) |
| *(optional)* `pixar_xl.safetensors` | `loras/` | Civitai version **211735** (Pixar style, trigger `pixar style`) |
| *(optional)* `3d_icon_xl.safetensors` | `loras/` | Civitai version **342431** (3D icon, trigger `TOK`) |

Civitai direct download (no token needed for these): `https://civitai.com/api/download/models/<versionId>`

## 3. IPAdapter (for consistent characters)

Custom node + two models:
```
git clone https://github.com/cubiq/ComfyUI_IPAdapter_plus  ComfyUI/custom_nodes/ComfyUI_IPAdapter_plus
```
| File | → dir | Source |
|---|---|---|
| `CLIP-ViT-H-14-laion2B-s32B-b79K.safetensors` (2.5 GB) | `clip_vision/` | HF `h94/IP-Adapter` → `models/image_encoder/model.safetensors` (rename) |
| `ip-adapter-plus_sdxl_vit-h.safetensors` (848 MB) | `ipadapter/` | HF `h94/IP-Adapter` → `sdxl_models/ip-adapter-plus_sdxl_vit-h.safetensors` |

## 4. Launch the server (leave it running)

```
cd .../ComfyUI_windows_portable
./python_embeded/python.exe -s ComfyUI/main.py --lowvram --port 8188
```
`--lowvram` is needed for 6–8 GB GPUs. API + GUI at `http://127.0.0.1:8188`.

---

## 5. Usage

Run the wrapper with **system Python** (it's stdlib-only HTTP — no torch needed):

```bash
# base SDXL
python scripts/comfy_gen.py --prompt "a glowing emerald market chart, tech-noir" --out out/x.png

# + comic LoRA (add the trigger word to the prompt)
python scripts/comfy_gen.py --lora comic_eldritch.safetensors --prompt "comic book, a red robot hero" --out out/r.png

# consistent character (IPAdapter): lock a reference face/costume
python scripts/comfy_gen.py --lora comic_eldritch.safetensors --ref refs/hero.png --ip-weight 0.6 \
    --prompt "comic book, the red hero leaping" --out out/hero_leap.png

# two-pass "scene → face-lock": dynamic action + rich background, THEN lock identity
python scripts/comfy_gen.py --lora comic_eldritch.safetensors --ref refs/hero.png --twopass --pass2-denoise 0.5 \
    --prompt "comic book, wide shot, the red hero hauling a huge crate up a hill, busy marketplace" --out out/haul.png
```

Every run also saves `<name>.workflow.json` next to the image — load it in the ComfyUI GUI
(**Workflow → Open**, or drag the PNG onto the canvas) to see/edit the node graph.

### Panel schema (comic_pipeline.py) — story-telling comics
```python
import sys; sys.path.insert(0, "scripts")
from comic_pipeline import Panel, render_panels

render_panels({
  "p1": Panel(char="refs/ant.png", shot="FULL",
              action="a cartoon ant straining to push a giant grain up a trail",
              setting="a sunlit summer meadow",
              props=["a line of worker ants", "an anthill", "wildflowers"],
              mood="hard-working, golden light", seed=11, lora_weight=0.6,
              neg_extra="muscular, superhero, human body"),
  # ... more panels ...
}, "out/comic")
```
Fields: `char` (IPAdapter ref, or `None` for scenes / 2-character panels — describe both in `action`),
`shot` (WIDE/FULL/MEDIUM/CLOSEUP), `action`, `setting`, `props`, `mood`, `ip_weight`,
`pass2_denoise`, `lora_weight`, `neg_extra`, `style`. `compose()` front-loads shot + action +
background so the image narrates the story.

## Tuning notes
- IPAdapter weight ~**0.6** is the sweet spot for pose-varied consistency (0.8 over-locks the ref pose).
- **Two-pass** frees the action/scene while keeping identity — best for dynamic panels.
- Exotic props (a specific "giant grain seed") remain SDXL-weak; lean on shot + scene + speech bubbles.
- Multi-character panels: IPAdapter locks one identity — describe both figures in `action`.

*Educational tooling. The finance builders in `higgs/` are project-specific; this pipeline is generic.*
