"""Local ComfyUI image generator — free/unlimited/private image gen on the
local GPU (RTX 4050 6GB), an alternative to the Grok subscription pipeline for
heroes/backgrounds/icon art. Talks to a running ComfyUI server over its HTTP
API (same integration pattern as our Playwright-driven carousel builders).

Prereqs (one-time, see setup):
  ComfyUI portable at C:\\Users\\Amsegt\\comfy\\ComfyUI_windows_portable, launched with
    python_embeded\\python.exe -s ComfyUI\\main.py --lowvram --port 8188
  models/checkpoints/sd_xl_base_1.0.safetensors  (SDXL base 1.0)
  models/loras/3d_icon_xl.safetensors            (3D-icon LoRA, trigger word "TOK")

Usage:
  python scripts/comfy_gen.py --prompt "a glowing emerald bull market chart, tech-noir, dark" \\
      --out higgs/test.png --width 1024 --height 1024 --steps 28
  # with the 3D-icon LoRA (prepend the trigger word "TOK" to the prompt):
  python scripts/comfy_gen.py --prompt "TOK icon, a golden dollar coin, dark background" \\
      --lora 3d_icon_xl.safetensors --lora-weight 0.9 --out higgs/coin.png

Educational/research tooling. Not financial advice.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import time
import urllib.parse
import urllib.request

HOST = "http://127.0.0.1:8188"

NEG_DEFAULT = "text, watermark, logo, blurry, low quality, jpeg artifacts, deformed, extra limbs"


def build_workflow(prompt, negative, width, height, steps, cfg, seed, ckpt, lora, lora_weight):
    """SDXL txt2img graph in ComfyUI API format. Optional LoRA is inserted
    between the checkpoint and the sampler/CLIP."""
    g = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
    }
    model_src, clip_src = ["4", 0], ["4", 1]
    if lora:
        g["10"] = {
            "class_type": "LoraLoader",
            "inputs": {"lora_name": lora, "strength_model": lora_weight, "strength_clip": lora_weight,
                       "model": ["4", 0], "clip": ["4", 1]},
        }
        model_src, clip_src = ["10", 0], ["10", 1]
    g["6"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip_src}}
    g["7"] = {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip_src}}
    g["3"] = {"class_type": "KSampler", "inputs": {
        "seed": seed, "steps": steps, "cfg": cfg, "sampler_name": "dpmpp_2m", "scheduler": "karras",
        "denoise": 1.0, "model": model_src, "positive": ["6", 0], "negative": ["7", 0], "latent_image": ["5", 0]}}
    g["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}}
    g["9"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "aiinvest", "images": ["8", 0]}}
    return g


def _post(path, payload):
    req = urllib.request.Request(HOST + path, data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def _get(path):
    return json.loads(urllib.request.urlopen(HOST + path, timeout=30).read())


def generate(prompt, out, negative=NEG_DEFAULT, width=1024, height=1024, steps=28, cfg=7.0,
             seed=0, ckpt="sd_xl_base_1.0.safetensors", lora=None, lora_weight=0.9, timeout_s=600):
    wf = build_workflow(prompt, negative, width, height, steps, cfg, seed, ckpt, lora, lora_weight)
    t0 = time.time()
    pid = _post("/prompt", {"prompt": wf})["prompt_id"]
    img = None
    while time.time() - t0 < timeout_s:
        hist = _get(f"/history/{pid}")
        if pid in hist:
            outs = hist[pid].get("outputs", {})
            imgs = (outs.get("9") or {}).get("images") or []
            if imgs:
                img = imgs[0]
                break
        time.sleep(1.5)
    if not img:
        raise SystemExit(f"timed out after {timeout_s}s (prompt_id={pid})")
    q = urllib.parse.urlencode({"filename": img["filename"], "subfolder": img.get("subfolder", ""), "type": img.get("type", "output")})
    data = urllib.request.urlopen(f"{HOST}/view?{q}", timeout=60).read()
    outp = pathlib.Path(out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_bytes(data)
    print(f"OK {outp}  ({len(data)//1024} KB)  {time.time()-t0:.1f}s  [{width}x{height} {steps}steps{' +LoRA' if lora else ''}]")
    return str(outp)


if __name__ == "__main__":
    import urllib.parse
    ap = argparse.ArgumentParser(description="Local ComfyUI SDXL image generator")
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--negative", default=NEG_DEFAULT)
    ap.add_argument("--width", type=int, default=1024)
    ap.add_argument("--height", type=int, default=1024)
    ap.add_argument("--steps", type=int, default=28)
    ap.add_argument("--cfg", type=float, default=7.0)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--ckpt", default="sd_xl_base_1.0.safetensors")
    ap.add_argument("--lora", default=None)
    ap.add_argument("--lora-weight", type=float, default=0.9)
    a = ap.parse_args()
    generate(a.prompt, a.out, a.negative, a.width, a.height, a.steps, a.cfg, a.seed, a.ckpt, a.lora, a.lora_weight)
