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

# Richer defaults so the CLIP-encode nodes in the saved workflow carry detailed
# descriptions (owner request 2026-08-03). QUALITY is appended to the positive
# prompt unless --plain; NEG_DEFAULT is a thorough negative.
QUALITY = ("masterpiece, best quality, ultra-detailed, intricate details, sharp focus, "
           "dramatic cinematic lighting, rich vivid colors, professional illustration, 8k")
NEG_DEFAULT = ("text, caption, words, letters, signature, watermark, logo, username, "
               "blurry, low quality, low resolution, jpeg artifacts, noisy, grainy, "
               "deformed, disfigured, bad anatomy, extra limbs, extra fingers, mutated hands, "
               "cropped, out of frame, cluttered, oversaturated, ugly, plain flat lighting")


def build_workflow(prompt, negative, width, height, steps, cfg, seed, ckpt, lora, lora_weight,
                   ref_filename=None, ip_weight=0.75, twopass=False, pass2_denoise=0.5, loras=None):
    """SDXL graph in ComfyUI API format.

    - base: txt2img.
    - +ref (single-pass): IPAdapter conditions the whole generation on a
      reference character — strong identity but tends to copy the ref's pose.
    - +ref +twopass: PASS 1 renders the full action/scene from the prompt with
      NO IPAdapter (dynamic pose + rich background), then PASS 2 img2img-refines
      it (denoise=pass2_denoise) WITH IPAdapter to lock the character's identity
      onto that scene — dynamic storytelling AND a consistent character.
    """
    g = {
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": ckpt}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"width": width, "height": height, "batch_size": 1}},
    }
    # LoRA stack: `loras` = list of (name, weight); falls back to the single
    # lora/lora_weight for backward compat. Chained so e.g. a character LoRA +
    # a comic-style LoRA compose (trained character IN the comic look).
    stack = loras if loras is not None else ([(lora, lora_weight)] if lora else [])
    model_src, clip_src = ["4", 0], ["4", 1]
    for i, (ln, lw) in enumerate(stack):
        nid = str(10 + i)
        g[nid] = {"class_type": "LoraLoader",
                  "inputs": {"lora_name": ln, "strength_model": lw, "strength_clip": lw,
                             "model": model_src, "clip": clip_src}}
        model_src, clip_src = [nid, 0], [nid, 1]
    base_model = model_src  # model before any IPAdapter patch
    g["6"] = {"class_type": "CLIPTextEncode", "inputs": {"text": prompt, "clip": clip_src}}
    g["7"] = {"class_type": "CLIPTextEncode", "inputs": {"text": negative, "clip": clip_src}}

    def ksampler(nid, model, latent, denoise, s):
        g[nid] = {"class_type": "KSampler", "inputs": {
            "seed": s, "steps": steps, "cfg": cfg, "sampler_name": "dpmpp_2m", "scheduler": "karras",
            "denoise": denoise, "model": model, "positive": ["6", 0], "negative": ["7", 0], "latent_image": latent}}

    def ipadapter(model_in):
        g["50"] = {"class_type": "IPAdapterUnifiedLoader",
                   "inputs": {"model": model_in, "preset": "PLUS (high strength)"}}
        g["51"] = {"class_type": "LoadImage", "inputs": {"image": ref_filename}}
        g["52"] = {"class_type": "IPAdapterAdvanced", "inputs": {
            "model": ["50", 0], "ipadapter": ["50", 1], "image": ["51", 0],
            "weight": ip_weight, "weight_type": "linear", "combine_embeds": "concat",
            "start_at": 0.0, "end_at": 1.0, "embeds_scaling": "V only"}}
        return ["52", 0]

    if ref_filename and twopass:
        ksampler("30", base_model, ["5", 0], 1.0, seed)            # pass 1: scene
        ksampler("3", ipadapter(base_model), ["30", 0], pass2_denoise, seed)  # pass 2: face-lock refine
    elif ref_filename:
        ksampler("3", ipadapter(base_model), ["5", 0], 1.0, seed)
    else:
        ksampler("3", base_model, ["5", 0], 1.0, seed)

    g["8"] = {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}}
    g["9"] = {"class_type": "SaveImage", "inputs": {"filename_prefix": "aiinvest", "images": ["8", 0]}}
    return g


def _post(path, payload):
    req = urllib.request.Request(HOST + path, data=json.dumps(payload).encode(),
                                headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=30).read())


def _get(path):
    return json.loads(urllib.request.urlopen(HOST + path, timeout=30).read())


def upload_ref(path):
    """Upload a reference image to ComfyUI's input/ dir (for IPAdapter LoadImage).
    Returns the server-side filename."""
    p = pathlib.Path(path)
    data = p.read_bytes()
    boundary = "----aiinvest" + str(len(data))
    body = (f"--{boundary}\r\n".encode()
            + f'Content-Disposition: form-data; name="image"; filename="{p.name}"\r\n'.encode()
            + b"Content-Type: image/png\r\n\r\n" + data + b"\r\n"
            + f"--{boundary}--\r\n".encode())
    req = urllib.request.Request(HOST + "/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    r = json.loads(urllib.request.urlopen(req, timeout=60).read())
    sub = r.get("subfolder", "")
    return f"{sub}/{r['name']}" if sub else r["name"]


def generate(prompt, out, negative=NEG_DEFAULT, width=1024, height=1024, steps=28, cfg=7.0,
             seed=0, ckpt="sd_xl_base_1.0.safetensors", lora=None, lora_weight=0.9, timeout_s=600,
             quality=True, ref=None, ip_weight=0.75, twopass=False, pass2_denoise=0.5, loras=None):
    full_prompt = f"{prompt}, {QUALITY}" if quality else prompt
    ref_filename = upload_ref(ref) if ref else None
    wf = build_workflow(full_prompt, negative, width, height, steps, cfg, seed, ckpt, lora, lora_weight,
                        ref_filename=ref_filename, ip_weight=ip_weight, twopass=twopass,
                        pass2_denoise=pass2_denoise, loras=loras)
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
    # Always drop the exact workflow next to the image so it can be reviewed /
    # imported into the ComfyUI GUI (owner request 2026-08-03). Load via
    # ComfyUI "Workflow > Open (API)", or just drag the PNG onto the canvas.
    wf_path = outp.with_name(outp.stem + ".workflow.json")
    wf_path.write_text(json.dumps(wf, indent=2), encoding="utf-8")
    print(f"OK {outp}  ({len(data)//1024} KB)  {time.time()-t0:.1f}s  "
          f"[{width}x{height} {steps}steps{' +LoRA' if lora else ''}]  workflow -> {wf_path.name}")
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
    ap.add_argument("--lora", action="append", default=None,
                    help="LoRA to apply; repeatable. Use 'name' or 'name:weight' (e.g. fablegh.safetensors:0.9)")
    ap.add_argument("--lora-weight", type=float, default=0.9, help="default weight for --lora entries without :weight")
    ap.add_argument("--plain", action="store_true", help="do not append the QUALITY suffix to the prompt")
    ap.add_argument("--ref", default=None, help="reference character image (IPAdapter) for consistent face/costume")
    ap.add_argument("--ip-weight", type=float, default=0.75, help="IPAdapter strength (0.5-1.0)")
    ap.add_argument("--twopass", action="store_true", help="scene-then-face-lock: dynamic action/scene, then IPAdapter refines identity")
    ap.add_argument("--pass2-denoise", type=float, default=0.5, help="two-pass refine denoise (0.4-0.6); lower keeps more of the scene")
    a = ap.parse_args()
    loras = None
    if a.lora:
        loras = []
        for item in a.lora:
            if ":" in item:
                name, w = item.rsplit(":", 1)
                loras.append((name, float(w)))
            else:
                loras.append((item, a.lora_weight))
    generate(a.prompt, a.out, a.negative, a.width, a.height, a.steps, a.cfg, a.seed, a.ckpt, None, a.lora_weight,
             quality=not a.plain, ref=a.ref, ip_weight=a.ip_weight, twopass=a.twopass, pass2_denoise=a.pass2_denoise,
             loras=loras)
