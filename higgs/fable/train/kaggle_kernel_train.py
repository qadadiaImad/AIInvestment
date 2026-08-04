"""Kaggle SCRIPT kernel — trains the v2 character LoRAs on a free Kaggle GPU.

Pushed + run headless via the Kaggle API (see kaggle_run.py). Heavy artifacts
(sd-scripts, the 6.9 GB SDXL base, the dataset copy) go in /kaggle/tmp so they
are NOT captured as kernel output — only the two .safetensors land in
/kaggle/working, keeping the output pull small.

v2 fix params (from the consistency post-mortem): dim32 / alpha16 / 14 epochs.
Dataset attached at /kaggle/input/**/{grasshopper,ant}/ (png + txt captions).
"""
import glob
import os
import shutil
import subprocess

TMP = "/kaggle/tmp"
OUT = "/kaggle/working"
os.makedirs(TMP, exist_ok=True)


def sh(cmd: str):
    print("+", cmd, flush=True)
    r = subprocess.run(cmd, shell=True)
    if r.returncode != 0:
        raise SystemExit(f"FAILED ({r.returncode}): {cmd}")


# 1) kohya sd-scripts + deps
sh(f"git clone -q https://github.com/kohya-ss/sd-scripts {TMP}/sd-scripts")
os.chdir(f"{TMP}/sd-scripts")
sh("pip -q install -r requirements.txt")
sh("pip -q install bitsandbytes accelerate")

# 2) SDXL base checkpoint
sh(f"wget -q -O {TMP}/sdxl.safetensors "
   "https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors")

# 3) locate the attached dataset + lay out kohya's 10_<trigger> folders
gh = glob.glob("/kaggle/input/**/grasshopper", recursive=True)
assert gh, "grasshopper folder not found under /kaggle/input — attach the dataset"
base = os.path.dirname(gh[0])
for name, trig in [("grasshopper", "fablegh"), ("ant", "fableant")]:
    dst = f"{TMP}/data_{trig}/10_{trig}"
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(f"{base}/{name}"):
        if f.endswith((".png", ".txt")):
            shutil.copy(f"{base}/{name}/{f}", dst)
    print(name, "->", len([x for x in os.listdir(dst) if x.endswith(".png")]), "images", flush=True)


# 4) train each character (v2: dim32 / alpha16 / 14 epochs)
def train(trig: str):
    cmd = (
        "accelerate launch --num_cpu_threads_per_process 2 sdxl_train_network.py "
        f"--pretrained_model_name_or_path={TMP}/sdxl.safetensors "
        f"--train_data_dir={TMP}/data_{trig} --output_dir={OUT} --output_name={trig} "
        "--resolution=768,768 --enable_bucket "
        "--network_module=networks.lora --network_dim=32 --network_alpha=16 "
        "--train_batch_size=1 --max_train_epochs=14 --learning_rate=1e-4 "
        "--optimizer_type=AdamW8bit --mixed_precision=fp16 --save_precision=fp16 "
        "--gradient_checkpointing --lowram --cache_latents --cache_latents_to_disk "
        "--max_data_loader_n_workers=1 --save_every_n_epochs=14 --sdpa"
    )
    sh(cmd)


train("fablegh")
train("fableant")

print("DONE — outputs:", glob.glob(f"{OUT}/*.safetensors"), flush=True)
