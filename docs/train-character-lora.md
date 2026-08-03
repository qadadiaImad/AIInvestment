# Train a character LoRA (Kaggle GPU) — visual, ~1 GPU-hour total (free)

The local 6 GB GPU can't train SDXL LoRAs. The **dataset is done + portable** —
`higgs/fable/train/fable_lora_dataset.zip` (14 captioned images of the grasshopper + 14 of the
ant). Train on a **free Kaggle T4** (~30 min/character), download the `.safetensors`, and we drop
them into `ComfyUI/models/loras/`. Each character then becomes **baked-in** — identical in ANY
pose/scene/interaction. Triggers: **`fablegh`** (grasshopper), **`fableant`** (ant).

## Kaggle setup
1. kaggle.com → verify phone (unlocks GPU + Internet) → **Create → Notebook**.
2. Right panel: **Accelerator = GPU T4 ×2**, **Internet = On**.
3. **Add Input → Upload** → `fable_lora_dataset.zip` → name it `fable_training` → Create.

## Cell 1 — install + SDXL + unzip
(The `glob` finds the zip wherever Kaggle mounts `fable_training`, hyphen or underscore.)
```python
!git clone https://github.com/kohya-ss/sd-scripts /kaggle/working/sd-scripts
%cd /kaggle/working/sd-scripts
!pip -q install -r requirements.txt && pip -q install bitsandbytes accelerate tensorboard
!wget -q -O /kaggle/working/sdxl.safetensors https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0/resolve/main/sd_xl_base_1.0.safetensors
import glob, os, shutil, zipfile
# Kaggle auto-extracts uploaded zips, so detect the extracted folders OR a zip:
gh = glob.glob('/kaggle/input/**/grasshopper', recursive=True)
if gh:
    base = os.path.dirname(gh[0]); print('dataset (already extracted) at:', base)
else:
    z = glob.glob('/kaggle/input/**/*.zip', recursive=True)
    assert z, "No dataset under /kaggle/input — Add Input > attach fable_training, then rerun."
    print('extracting', z[0]); zipfile.ZipFile(z[0]).extractall('/kaggle/working/raw'); base='/kaggle/working/raw'
for name, trig in [('grasshopper','fablegh'), ('ant','fableant')]:
    dst=f'/kaggle/working/data_{trig}/10_{trig}'; os.makedirs(dst, exist_ok=True)
    for f in os.listdir(f'{base}/{name}'):
        if f.endswith(('.png','.txt')): shutil.copy(f'{base}/{name}/{f}', dst)
    print(name, '->', len([x for x in os.listdir(dst) if x.endswith('.png')]), 'images')
open('/kaggle/working/s_gh.txt','w').write("fablegh, a cute cartoon green grasshopper playing a fiddle in a meadow --w 768 --h 768 --d 42 --s 24")
open('/kaggle/working/s_ant.txt','w').write("fableant, a cute cartoon red ant carrying a grain in a forest --w 768 --h 768 --d 42 --s 24")
print('SETUP DONE')
```

## Cell 2 — live loss graph (optional)
```python
%load_ext tensorboard
%tensorboard --logdir /kaggle/working/logs
```

## Cell 3 — train the grasshopper (~20 min)
```python
%cd /kaggle/working/sd-scripts
!accelerate launch sdxl_train_network.py --pretrained_model_name_or_path=/kaggle/working/sdxl.safetensors \
 --train_data_dir=/kaggle/working/data_fablegh --output_dir=/kaggle/working/out --output_name=fablegh \
 --resolution=768,768 --enable_bucket --network_module=networks.lora --network_dim=16 --network_alpha=8 \
 --train_batch_size=1 --max_train_epochs=8 --learning_rate=1e-4 --optimizer_type=AdamW8bit \
 --mixed_precision=fp16 --save_precision=fp16 --gradient_checkpointing --lowram --cache_latents --cache_latents_to_disk --max_data_loader_n_workers=1 --save_every_n_epochs=8 \
 --sample_every_n_epochs=2 --sample_prompts=/kaggle/working/s_gh.txt --sample_sampler=euler_a \
 --logging_dir=/kaggle/working/logs --log_with=tensorboard
```

## Cell 4 — train the ant (~20 min) — same, 3 values swapped
```python
%cd /kaggle/working/sd-scripts
!accelerate launch sdxl_train_network.py --pretrained_model_name_or_path=/kaggle/working/sdxl.safetensors \
 --train_data_dir=/kaggle/working/data_fableant --output_dir=/kaggle/working/out --output_name=fableant \
 --resolution=768,768 --enable_bucket --network_module=networks.lora --network_dim=16 --network_alpha=8 \
 --train_batch_size=1 --max_train_epochs=8 --learning_rate=1e-4 --optimizer_type=AdamW8bit \
 --mixed_precision=fp16 --save_precision=fp16 --gradient_checkpointing --lowram --cache_latents --cache_latents_to_disk --max_data_loader_n_workers=1 --save_every_n_epochs=8 \
 --sample_every_n_epochs=2 --sample_prompts=/kaggle/working/s_ant.txt --sample_sampler=euler_a \
 --logging_dir=/kaggle/working/logs --log_with=tensorboard
```

## Watch + download
- Previews land in `/kaggle/working/out/sample/` each epoch — watch the character sharpen.
- TensorBoard (Cell 2): a smooth downward-then-flat loss = healthy.
- When both finish: right panel **Output** tab → download `/kaggle/working/out/fablegh.safetensors`
  and `fableant.safetensors`. Hand them to the pipeline owner.

## Bring them back into the local pipeline
Drop both into `ComfyUI/models/loras/`, then generate consistent characters:
```bash
python scripts/comfy_gen.py --lora comic_eldritch.safetensors --lora-weight 0.6 \
  --prompt "comic book, fablegh a green grasshopper begging fableant a red ant at a snowy cottage door" \
  --out out/beg.png
```
Trigger the characters by their words: **`fablegh`**, **`fableant`**. (Stacking two character LoRAs +
the style LoRA needs multi-LoRA support in `comfy_gen` — a small add on request.)

## Tuning
- Identity too weak → 12 epochs or `--network_dim=32`. Overfit (same pose) → fewer epochs.
- ~1 GPU-hour total; free tier is ~30 h/week, so it costs nothing.

## v2 — lessons from the consistency post-mortem (2026-08-03)
The v1 LoRAs (dim16, alpha8, 8 epochs, 14 images all on the SAME mint background in
the SAME front-facing pose) came out **under-baked**: identity is soft, entangled with
that one background/pose, and easily overridden by a style LoRA or scene cues. Symptoms:
the character renders as a *different* green creature each panel (dino-snout / frog-face /
person-in-a-hoodie). Root cause = a weak, context-bound LoRA — NOT a prompt bug.

**Two independent fixes (do both):**

1. **Generation-side (already applied, no retrain):** trained char LoRA @ **0.9** + comic
   style LoRA @ **0.2** (a higher style weight hijacks the face), reuse ONE canonical
   descriptor + a fixed seed per panel, keep the character **upright/bipedal** (the trained
   pose), and **ban clothing** in the negative (winter "coat" cues → humanoid). Baked into
   `higgs/_gen_fable_panels.py`.

2. **Training-side (the durable fix) — retrain v2 with:**
   - **`--network_dim=32 --network_alpha=16`** (more capacity to lock the face).
   - **`--max_train_epochs=14`** (v1's 8 under-fit).
   - **Background + pose variety in the dataset.** v1's images were all identical mint-bg
     front poses, so identity entangled with context. For v2: cut/segment each character
     onto **varied or transparent backgrounds**, and include a few **pose variations**
     (3/4 view, sitting, reaching). ~20 images/character. This is the single biggest lever.
   - Keep `--lowram --cache_latents_to_disk --max_data_loader_n_workers=1 --train_batch_size=1`
     (Kaggle CPU-RAM fix). Sanity-check the epoch samples in `out/sample/` actually match
     the training face before downloading.

The v2 dataset is prepped at `higgs/fable/train/fable_lora_dataset_v2.zip` (see the
`_prep_train_v2` driver). Upload it to Kaggle as `fable_training` (replacing v1) and rerun
Cells 3/4 with the dim/alpha/epoch values above.
