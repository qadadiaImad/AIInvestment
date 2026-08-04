"""Load and parameterize API-format ComfyUI workflow templates.

Templates are the JSON shape POST /prompt expects:
{node_id: {"class_type": …, "inputs": {…}}, …}. PARAM_MAPS names the
logical knobs a template exposes and where each lands (node_id, input);
entries are added as templates are authored against the live server.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path

TEMPLATES_DIR = Path(__file__).parent / "templates"

PARAM_MAPS: dict[str, dict[str, tuple[str, str]]] = {}

# Z-Image-Turbo text-to-image. Graph reconstructed from the native
# `image_z_image_turbo.json` template shipped in
# comfyui_workflow_templates_media_other (steps=4, cfg=1, res_multistep,
# simple, ModelSamplingAuraFlow shift=3) with one deviation: node "5" is a
# real CLIPTextEncode for the negative prompt instead of the template's
# ConditioningZeroOut(positive), so a "negative" param has somewhere to
# land. At cfg=1 (no CFG) both are equivalent — the sampler output is the
# positive conditioning alone either way.
PARAM_MAPS["zimage_t2i"] = {
    "prompt":   ("4", "text"),
    "negative": ("5", "text"),
    "seed":     ("8", "seed"),
    "width":    ("6", "width"),
    "height":   ("6", "height"),
}

# Wan 2.2 TI2V-5B fast video (Apache 2.0). Graph reconstructed from the
# native `video_wan2_2_5B_ti2v.json` template shipped in
# comfyui_workflow_templates_media_video: UNETLoader(wan2.2_ti2v_5B_fp16)
# -> ModelSamplingSD3(shift=8) -> KSampler(steps=20, cfg=5, uni_pc,
# simple, denoise=1) fed by Wan22ImageToVideoLatent (vae=wan2.2_vae.
# safetensors, umt5_xxl CLIP type="wan") -> VAEDecode -> CreateVideo
# (fps=24) -> SaveVideo. The native template is ONE graph with a LoadImage
# node the user bypasses (UI "mode 4") for T2V and enables for I2V —
# API-format prompts can't ship a bypassed/dangling node, so this is
# shipped as two template files sharing everything except the
# Wan22ImageToVideoLatent.start_image link and its upstream LoadImage:
# "wan22_ti2v_5b" (T2V, no start_image input at all — the input is
# optional per /object_info) and "wan22_ti2v_5b_i2v" (adds node "12"
# LoadImage wired to node "6"'s start_image).
# Illustrious-XL (SDXL) + LoRA text-to-image. Standard SDXL graph:
# CheckpointLoaderSimple -> LoraLoader -> dual CLIPTextEncode -> KSampler
# (dpmpp_2m/karras, steps 26, cfg 6) -> VAEDecode -> SaveImage. Written for
# the ana_cast_v1 cast LoRA (2026-08-04); lora/strength are exposed so any
# future character or style LoRA reuses the same graph.
PARAM_MAPS["sdxl_lora_t2i"] = {
    "prompt":     ("3", "text"),
    "negative":   ("4", "text"),
    "seed":       ("6", "seed"),
    "width":      ("5", "width"),
    "height":     ("5", "height"),
    "lora":       ("2", "lora_name"),
    "lora_sm":    ("2", "strength_model"),
    "lora_sc":    ("2", "strength_clip"),
}

# Two-character regional variant of sdxl_lora_t2i: core-node area
# conditioning (ConditioningSetArea left/right halves + Combine with a
# scene-glue base prompt) to fight cross-character trait bleed at
# inference. Areas are fixed halves of a 1216x832 canvas.
# Mouth-viseme inpainting: regenerate ONLY a masked mouth region of a
# base drawing (SetLatentNoiseMask, denoise 0.8) so every viseme shares
# pixel-identical art outside the mask. base/mask are staged into the
# ComfyUI input dir via ComfyClient.stage_input.
PARAM_MAPS["sdxl_lora_inpaint"] = {
    "prompt":   ("3", "text"),
    "negative": ("4", "text"),
    "image":    ("5", "image"),
    "mask":     ("6", "image"),
    "seed":     ("10", "seed"),
    "denoise":  ("10", "denoise"),
}

PARAM_MAPS["sdxl_lora_regional2"] = {
    "prompt_base": ("3", "text"),
    "prompt_left": ("4", "text"),
    "prompt_right": ("6", "text"),
    "negative":   ("10", "text"),
    "seed":       ("12", "seed"),
}

PARAM_MAPS["wan22_ti2v_5b"] = {
    "prompt":   ("4", "text"),
    "negative": ("5", "text"),
    "seed":     ("8", "seed"),
    "width":    ("6", "width"),
    "height":   ("6", "height"),
    "length":   ("6", "length"),
}
PARAM_MAPS["wan22_ti2v_5b_i2v"] = {
    **PARAM_MAPS["wan22_ti2v_5b"],
    "image": ("12", "image"),
}

# Wan 2.2 I2V-A14B, quality lane (Apache 2.0). Graph reconstructed from the
# native `video_wan2_2_14B_i2v.json` template's "fp8_scaled + 4steps LoRA"
# group (the group left enabled/mode:0 by default; the plain "fp8_scaled"
# group is mode:4/bypassed in the native file and is NOT reproduced here).
# One structural swap from the native graph: each expert's UNETLoader
# (fp8_scaled .safetensors) is replaced with UnetLoaderGGUF pointing at the
# repo's Q4_K_M .gguf files (per Task 1's manifest / Task 7's finding that
# the native 14B template ships fp8_scaled weights, not the GGUF files this
# repo's video-14b manifest group actually downloads) -- class name
# confirmed live via GET /object_info (search key containing "gguf"):
# UnetLoaderGGUF, required=["unet_name"], and its dropdown lists exactly
# our two on-disk files. Everything else (CLIPLoader umt5_xxl, VAELoader
# wan_2.1_vae.safetensors per Task 7 Step 2, LoraLoaderModelOnly x2 at
# strength_model=1.0, ModelSamplingSD3 shift=5, WanImageToVideo, the
# two-expert KSamplerAdvanced chain, VAEDecode -> CreateVideo(fps=16) ->
# SaveVideo) is carried over unchanged from the native group's own wiring
# and widget values.
#
# Sampler settings: the native group's own KSamplerAdvanced pair is
# steps=4 total (NOT 8) split 2/2 -- node "13" (add_noise=enable,
# start_at_step=0, end_at_step=2, return_with_leftover_noise=enable) then
# node "14" (add_noise=disable, start_at_step=2, end_at_step=4,
# return_with_leftover_noise=disable) -- cfg=1, sampler=euler,
# scheduler=simple, both experts' ModelSamplingSD3 shift=5. This is the
# native template's actual shipped default, kept here rather than the
# task brief's assigned starting point of "8 steps split 4/4" (untested
# alternative: steps=8, end_at_step=4/8 -- see task-8-report.md).
#
# This template is I2V-only: LoadImage (node "11") is always wired to
# WanImageToVideo.start_image, so "image" is a REQUIRED param in practice
# (a bare filename from ComfyClient.stage_input) even though apply_params
# itself doesn't enforce presence -- same non-enforced-but-required shape
# as "wan22_ti2v_5b_i2v"'s own "image" param.
PARAM_MAPS["wan22_i2v_14b"] = {
    "prompt":   ("9", "text"),
    "negative": ("10", "text"),
    "seed":     ("13", "noise_seed"),
    "width":    ("12", "width"),
    "height":   ("12", "height"),
    "length":   ("12", "length"),
    "image":    ("11", "image"),
}


def apply_params(workflow: dict, param_map: dict, params: dict) -> dict:
    unknown = set(params) - set(param_map)
    if unknown:
        raise KeyError(f"unknown params {sorted(unknown)}; "
                       f"template exposes {sorted(param_map)}")
    wf = copy.deepcopy(workflow)
    for name, value in params.items():
        node_id, input_name = param_map[name]
        wf[node_id]["inputs"][input_name] = value
    return wf


def load_template(name: str, **params) -> dict:
    wf = json.loads((TEMPLATES_DIR / f"{name}.json").read_text("utf-8"))
    return apply_params(wf, PARAM_MAPS[name], params)
