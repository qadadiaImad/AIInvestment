"""Drive Kaggle to train the v2 fable LoRAs end-to-end via the public API.

No MCP needed — this IS what a Kaggle MCP would wrap. Requires the Kaggle API
token at ~/.kaggle/kaggle.json (the user downloads it from Kaggle > Settings >
API > Create New Token; we never see/paste the key). Reads the username from that
file, so nothing else is needed.

Steps (sub-commands):
  push     upload/version the dataset, then push the training kernel (starts the run)
  status   poll the kernel status once
  wait     poll until the kernel finishes (complete/error)
  pull     download /kaggle/working outputs and install the .safetensors into ComfyUI
  all      push -> wait -> pull

    python higgs/fable/train/kaggle_run.py all
"""
import json
import os
import pathlib
import shutil
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
V2_DIR = HERE / "v2"                      # dataset payload: grasshopper/, ant/
KERNEL_DIR = HERE / "_kernel"            # kernel push dir (metadata + code)
COMFY_LORAS = pathlib.Path(r"C:\Users\Amsegt\comfy\ComfyUI_windows_portable\ComfyUI\models\loras")
OUT_DIR = HERE / "kaggle_out"

DATASET_SLUG = "fable-training-v2"
KERNEL_SLUG = "vv-fable-lora-train"


def api():
    from kaggle.api.kaggle_api_extended import KaggleApi
    a = KaggleApi()
    a.authenticate()
    return a


def username() -> str:
    p = pathlib.Path.home() / ".kaggle" / "kaggle.json"
    if p.exists():
        return json.loads(p.read_text())["username"]
    if os.environ.get("KAGGLE_USERNAME"):
        return os.environ["KAGGLE_USERNAME"]
    sys.exit("No Kaggle credentials. Put your token at ~/.kaggle/kaggle.json first.")


def ensure_dataset_payload():
    """The dataset folder must exist with grasshopper/ + ant/ (from _prep_train_v2.py)."""
    if not (V2_DIR / "grasshopper").exists() or not (V2_DIR / "ant").exists():
        sys.exit(f"Missing dataset payload at {V2_DIR}. Run: python higgs/_prep_train_v2.py")


def cmd_push():
    a = api()
    user = username()
    ensure_dataset_payload()

    # 1) dataset: create on first run, version thereafter
    (V2_DIR / "dataset-metadata.json").write_text(json.dumps({
        "title": DATASET_SLUG,
        "id": f"{user}/{DATASET_SLUG}",
        "licenses": [{"name": "CC0-1.0"}],
    }, indent=2))
    try:
        print("Creating dataset (first run)…", flush=True)
        a.dataset_create_new(str(V2_DIR), dir_mode="zip", public=False)
    except Exception as e:
        print(f"  create failed ({e}); versioning existing dataset…", flush=True)
        a.dataset_create_version(str(V2_DIR), version_notes="v2 bg-augmented", dir_mode="zip")

    # 2) kernel: metadata + code, then push
    KERNEL_DIR.mkdir(exist_ok=True)
    shutil.copy(HERE / "kaggle_kernel_train.py", KERNEL_DIR / "kaggle_kernel_train.py")
    (KERNEL_DIR / "kernel-metadata.json").write_text(json.dumps({
        "id": f"{user}/{KERNEL_SLUG}",
        "title": KERNEL_SLUG,
        "code_file": "kaggle_kernel_train.py",
        "language": "python",
        "kernel_type": "script",
        "is_private": True,
        "enable_gpu": True,
        "enable_internet": True,
        "dataset_sources": [f"{user}/{DATASET_SLUG}"],
        "competition_sources": [],
        "kernel_sources": [],
    }, indent=2))
    print("Pushing kernel (starts the GPU run)…", flush=True)
    a.kernels_push(str(KERNEL_DIR))
    print(f"Pushed. Watch: https://www.kaggle.com/{user}/{KERNEL_SLUG}", flush=True)


def _status(a, user):
    r = a.kernels_status(f"{user}/{KERNEL_SLUG}")
    return getattr(r, "status", r)


def cmd_status():
    a = api(); user = username()
    print("status:", _status(a, user))


def cmd_wait():
    a = api(); user = username()
    while True:
        s = str(_status(a, user))
        print(time.strftime("%H:%M:%S"), "status:", s, flush=True)
        if any(k in s.lower() for k in ("complete", "error", "cancel")):
            return s
        time.sleep(30)


def cmd_pull():
    a = api(); user = username()
    OUT_DIR.mkdir(exist_ok=True)
    print("Downloading kernel output…", flush=True)
    a.kernels_output(f"{user}/{KERNEL_SLUG}", str(OUT_DIR))
    got = list(OUT_DIR.glob("*.safetensors"))
    print("pulled:", [p.name for p in got])
    if COMFY_LORAS.exists():
        for p in got:
            shutil.copy(p, COMFY_LORAS / p.name)
            print("installed ->", COMFY_LORAS / p.name)
    else:
        print(f"(ComfyUI loras dir not found at {COMFY_LORAS}; copy manually)")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    if cmd == "push":
        cmd_push()
    elif cmd == "status":
        cmd_status()
    elif cmd == "wait":
        cmd_wait()
    elif cmd == "pull":
        cmd_pull()
    elif cmd == "all":
        cmd_push()
        s = cmd_wait()
        if "complete" in s.lower():
            cmd_pull()
        else:
            sys.exit(f"kernel ended: {s}")
    else:
        sys.exit(f"unknown command: {cmd}")
