# Train a character LoRA (cloud GPU) — visual, ~30 min each

The local 6 GB GPU can't train SDXL LoRAs (needs ~10 GB+, and no compatible Python here).
The **dataset is the hard part and it's done** — `higgs/fable/train/fable_lora_dataset.zip`
(14 curated, captioned images of the grasshopper + 14 of the ant). Train on a **free cloud GPU**
(Kaggle gives a 16 GB T4/P100, 30 h/week; Colab free also works), then bring the `.safetensors`
back and we drop them into `models/loras/`.

Result: each character becomes **baked-in** — identical in ANY pose, scene, or two-character
panel, at full SDXL quality. Trigger words: **`fablegh`** (grasshopper), **`fableant`** (ant).

---

## 1. Notebook setup (Kaggle recommended)

New Kaggle notebook → Settings → **Accelerator: GPU T4** → Internet **On**. Upload
`fable_lora_dataset.zip` as a dataset (or drag into `/kaggle/working`).

```python
# --- install kohya sd-scripts (the standard SDXL LoRA trainer) ---
!git clone https://github.com/kohya-ss/sd-scripts /kaggle/working/sd-scripts
%cd /kaggle/working/sd-scripts
!pip -q install -r requirements.txt
!pip -q install bitsandbytes accelerate tensorboard

# --- SDXL base checkpoint ---
!wget -q -O /kaggle/working/sdxl.safetensors \
  https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors

# --- unzip the dataset into kohya's expected layout: <dir>/<repeats>_<name>/ ---
import zipfile, os, shutil
zipfile.ZipFile('/kaggle/input/<your-dataset>/fable_lora_dataset.zip').extractall('/kaggle/working/raw')
for name, trig in [('grasshopper','fablegh'), ('ant','fableant')]:
    dst = f'/kaggle/working/data_{trig}/10_{trig}'   # 10 = repeats per image
    os.makedirs(dst, exist_ok=True)
    for f in os.listdir(f'/kaggle/working/raw/{name}'):
        if f.endswith(('.png','.txt')): shutil.copy(f'/kaggle/working/raw/{name}/{f}', dst)
```

## 2. Train one character (repeat for the other)

```python
%cd /kaggle/working/sd-scripts
!accelerate launch --num_cpu_threads_per_process 2 sdxl_train_network.py \
  --pretrained_model_name_or_path=/kaggle/working/sdxl.safetensors \
  --train_data_dir=/kaggle/working/data_fablegh \
  --output_dir=/kaggle/working/out --output_name=fablegh \
  --resolution=1024,1024 --enable_bucket \
  --network_module=networks.lora --network_dim=16 --network_alpha=8 \
  --train_batch_size=2 --max_train_epochs=10 --learning_rate=1e-4 \
  --optimizer_type=AdamW8bit --mixed_precision=fp16 --save_precision=fp16 \
  --gradient_checkpointing --cache_latents \
  --save_every_n_epochs=2 \
  --sample_every_n_epochs=1 --sample_prompts=/kaggle/working/sample.txt --sample_sampler=euler_a \
  --logging_dir=/kaggle/working/logs --log_with=tensorboard
```
Create the sample prompt file first so it renders a preview each epoch:
```python
open('/kaggle/working/sample.txt','w').write(
  "fablegh, a cute cartoon green grasshopper playing a fiddle in a meadow --w 1024 --h 1024 --d 42 --s 24")
```
Then rerun the command with `--train_data_dir=/kaggle/working/data_fableant --output_name=fableant`
and an `fableant …` sample prompt.

## 3. Visualize it training
- **Sample images:** `/kaggle/working/out/sample/` fills with a preview each epoch — watch the
  character sharpen from blob → your exact grasshopper.
- **Loss curve (TensorBoard):**
  ```python
  %load_ext tensorboard
  %tensorboard --logdir /kaggle/working/logs
  ```
  A smooth downward-then-flat loss = healthy. Spikes/flatline = lower the LR or check the data.

## 4. Bring the LoRAs back
Download `/kaggle/working/out/fablegh.safetensors` and `fableant.safetensors`, drop them in
`ComfyUI/models/loras/`. Then generate consistent characters locally:
```bash
python scripts/comfy_gen.py --lora comic_eldritch.safetensors --lora-weight 0.7 \
  --prompt "comic book, fablegh a cute green grasshopper begging fableant a red ant at a snowy cottage door, both characters" \
  --out out/beg.png
```
(Two character LoRAs can be stacked in one prompt — the schema/pipeline supports it; ping me and I'll
wire multi-LoRA into `comfy_gen`.) Trigger the characters by their words: **`fablegh`**, **`fableant`**.

## Tuning
- Too weak an identity → more epochs (12–15) or `--network_dim=32`.
- Overfit (same pose always) → fewer epochs / more varied dataset.
- Keep the comic **style** via the Eldritch LoRA at ~0.5–0.7 alongside the character LoRA.
