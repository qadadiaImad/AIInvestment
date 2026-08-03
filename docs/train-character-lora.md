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
import glob, zipfile, os, shutil
zip_path = glob.glob('/kaggle/input/**/fable_lora_dataset.zip', recursive=True)[0]
print('dataset:', zip_path)
zipfile.ZipFile(zip_path).extractall('/kaggle/working/raw')
for name, trig in [('grasshopper','fablegh'), ('ant','fableant')]:
    dst=f'/kaggle/working/data_{trig}/10_{trig}'; os.makedirs(dst, exist_ok=True)
    for f in os.listdir(f'/kaggle/working/raw/{name}'):
        if f.endswith(('.png','.txt')): shutil.copy(f'/kaggle/working/raw/{name}/{f}', dst)
open('/kaggle/working/s_gh.txt','w').write("fablegh, a cute cartoon green grasshopper playing a fiddle in a meadow --w 768 --h 768 --d 42 --s 24")
open('/kaggle/working/s_ant.txt','w').write("fableant, a cute cartoon red ant carrying a grain in a forest --w 768 --h 768 --d 42 --s 24")
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
