"""Model manifest for the local ComfyUI open-source gen backend.

Spec: docs/superpowers/specs/2026-08-03-comfyui-local-gen-design.md
approx_gb comes from the 2026-08-03 research sweep and is for reporting
only; real sizes are always fetched live from the HuggingFace API.
"""
from __future__ import annotations

import json
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path

COMFY_MODELS = Path.home() / "Documents" / "ComfyUI" / "models"
HF_TREE_URL = "https://huggingface.co/api/models/{repo}/tree/main?recursive=true"
UA = {"User-Agent": "AIInvestment-comfy-setup/1.0"}


@dataclass(frozen=True)
class ModelFile:
    repo: str        # HF repo id
    pattern: str     # regex against the full path inside the repo
    dest_dir: str    # subfolder of COMFY_MODELS
    approx_gb: float
    group: str       # "video-5b" | "video-14b" | "image"


@dataclass(frozen=True)
class ResolvedFile:
    repo: str
    rfile: str
    size: int        # exact bytes per HF API
    dest_dir: str
    group: str

    @property
    def url(self) -> str:
        return f"https://huggingface.co/{self.repo}/resolve/main/{self.rfile}"

    @property
    def dest(self) -> Path:
        import comfy.manifest as m  # late lookup so tests can monkeypatch
        return m.COMFY_MODELS / self.dest_dir / Path(self.rfile).name


MANIFEST: list[ModelFile] = [
    # --- video-5b: Wan 2.2 TI2V-5B + shared encoder/VAEs (Apache 2.0)
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/diffusion_models/wan2\.2_ti2v_5B_fp16\.safetensors$",
              "diffusion_models", 10.0, "video-5b"),
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled\.safetensors$",
              "text_encoders", 6.74, "video-5b"),
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/vae/wan2\.2_vae\.safetensors$",
              "vae", 1.41, "video-5b"),
    ModelFile("Comfy-Org/Wan_2.2_ComfyUI_Repackaged",
              r"split_files/vae/wan_2\.1_vae\.safetensors$",
              "vae", 0.25, "video-5b"),
    # --- video-14b: Wan 2.2 I2V-A14B GGUF Q4_K_M + lightx2v 4-step LoRAs
    ModelFile("QuantStack/Wan2.2-I2V-A14B-GGUF",
              r"(?i)high[-_]?noise.*Q4_K_M\.gguf$",
              "unet", 9.65, "video-14b"),
    ModelFile("QuantStack/Wan2.2-I2V-A14B-GGUF",
              r"(?i)low[-_]?noise.*Q4_K_M\.gguf$",
              "unet", 9.65, "video-14b"),
    ModelFile("lightx2v/Wan2.2-Distill-Loras",
              r"wan2\.2_i2v_A14b_high_noise_lora_rank64_lightx2v_4step.*\.safetensors$",
              "loras", 0.64, "video-14b"),
    ModelFile("lightx2v/Wan2.2-Distill-Loras",
              r"wan2\.2_i2v_A14b_low_noise_lora_rank64_lightx2v_4step.*\.safetensors$",
              "loras", 0.74, "video-14b"),
    # --- image: Z-Image-Turbo (Apache 2.0)
    # Comfy-Org/z_image_turbo ships bf16/int8/nvfp4 diffusion weights but no
    # fp8; fp8 lives in this community repackage (fallback per task brief).
    ModelFile("drbaph/Z-Image-Turbo-FP8",
              r"(?i)z_image_turbo_fp8_e4m3fn\.safetensors$",
              "diffusion_models", 6.15, "image"),
    ModelFile("Comfy-Org/z_image_turbo",
              r"(?i)split_files/text_encoders/qwen_3_4b.*fp8.*\.safetensors$",
              "text_encoders", 5.63, "image"),
    ModelFile("Comfy-Org/z_image_turbo",
              r"split_files/vae/ae\.safetensors$",
              "vae", 0.34, "image"),
]


class ResolveError(RuntimeError):
    pass


def hf_tree(repo: str) -> list[dict]:
    """Full file listing of a HF repo: [{'path':…, 'size':…}, …]."""
    req = urllib.request.Request(HF_TREE_URL.format(repo=repo), headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def resolve(entries=None, tree_fn=hf_tree) -> list[ResolvedFile]:
    """Match every manifest pattern against the live repo listing.

    Raises ResolveError (listing candidates) on 0 or >1 matches — fix
    the pattern from the candidate list; never guess a filename.
    """
    entries = MANIFEST if entries is None else entries
    trees: dict[str, list[dict]] = {}
    out: list[ResolvedFile] = []
    for e in entries:
        if e.repo not in trees:
            trees[e.repo] = [f for f in tree_fn(e.repo) if f.get("size")]
        hits = [f for f in trees[e.repo] if re.search(e.pattern, f["path"])]
        if len(hits) != 1:
            names = sorted(f["path"] for f in trees[e.repo])
            raise ResolveError(
                f"{e.repo}: pattern {e.pattern!r} matched "
                f"{[h['path'] for h in hits]}; repo files: {names}")
        out.append(ResolvedFile(e.repo, hits[0]["path"], hits[0]["size"],
                                e.dest_dir, e.group))
    return out
