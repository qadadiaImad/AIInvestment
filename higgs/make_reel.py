"""Assemble one narrated 9:16 reel end-to-end (deterministic; safe ffmpeg recipe).

Usage:  python higgs/make_reel.py <TICKER> <HERO_MP4_URL> <VOICE_MP3_URL>
Steps:  render 9:16 frames -> download animated hero + AI voice -> detect sentence-pause
        cut points -> build segments (hook over animated hero; ken-burns data + takeaway)
        -> concat -> mux voice -> verify. Writes higgs/reel_<tk>_<date>.mp4.

Ken-burns idiom is the CORRECTED one: `-loop 1` with NO `-t` on input + `-frames:v N` cap
(prevents the zoompan frame-multiplication blowup) and `-crf` rate control.
"""
import subprocess, sys, os, re, json, urllib.request, pathlib, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent          # repo root
HG = ROOT / "higgs"
FPS = 30

def _round_date():
    """Content-round date for output filenames: the manifest's `date` (the kit round being
    assembled), falling back to today (UTC) — never a hardcoded constant."""
    try:
        d = json.loads((HG / "reels_manifest.json").read_text(encoding="utf-8")).get("date")
        if d and re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(d)):
            return str(d)
    except Exception:
        pass
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

DATE = _round_date()

def sh(cmd):
    r = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True, text=True)
    return r.returncode, r.stdout, r.stderr

def ff(args):  # run ffmpeg, raise on failure
    rc, out, err = sh("ffmpeg -y -loglevel error " + args)
    if rc != 0:
        raise SystemExit(f"ffmpeg failed:\n{err[-1500:]}")

def probe_dur(path):
    rc, out, err = sh(f'ffprobe -v error -show_entries format=duration -of csv=p=0 "{path}"')
    return float(out.strip())

def silence_ends(path):
    rc, out, err = sh(f'ffmpeg -hide_banner -i "{path}" -af silencedetect=noise=-32dB:d=0.28 -f null - 2>&1')
    txt = out + err
    return [float(m) for m in re.findall(r"silence_end:\s*([\d.]+)", txt)]

def nearest(cands, target, default):
    if not cands: return default
    return min(cands, key=lambda x: abs(x - target))

def main():
    tk = sys.argv[1].upper(); hero_url = sys.argv[2]; voice_url = sys.argv[3]
    tkl = tk.lower()
    os.chdir(str(ROOT))

    # 1. frames (local, free)
    rc, out, err = sh(f'python "{HG/"_build_reel_stock.py"}" {tk}')
    if rc != 0: raise SystemExit(f"frame build failed:\n{err[-1200:]}")
    hook_png = HG/f"reel_{tkl}_hook.png"; data_png = HG/f"reel_{tkl}_data.png"; take_png = HG/f"reel_{tkl}_takeaway.png"
    for p in (hook_png, data_png, take_png):
        if not p.exists(): raise SystemExit(f"missing frame {p}")

    # 2. download hero + voice
    hero = HG/f"hero_{tkl}_anim.mp4"; voice = HG/f"voice_{tkl}_{DATE}.mp3"
    urllib.request.urlretrieve(hero_url, str(hero))
    urllib.request.urlretrieve(voice_url, str(voice))

    # 3. timing: 3 acts, cut on sentence pauses near targets
    dur = probe_dur(voice)
    ends = silence_ends(voice)
    t1 = round(nearest([e for e in ends if 6 < e < dur*0.45], dur*0.32, dur*0.32), 2)
    t2 = round(nearest([e for e in ends if t1+3 < e < dur*0.92], dur*0.74, dur*0.74), 2)
    n_data = max(1, round((t2 - t1) * FPS))
    n_take = max(1, round((dur - t2 + 0.4) * FPS))
    take_fade = max(0.1, n_take/FPS - 0.6)

    seg_hook = HG/f"_seg_{tkl}_hook.mp4"; seg_data = HG/f"_seg_{tkl}_data.mp4"; seg_take = HG/f"_seg_{tkl}_take.mp4"
    silent = HG/f"_silent_{tkl}.mp4"; concat = HG/f"_concat_{tkl}.txt"
    out_mp4 = HG/f"reel_{tkl}_{DATE}.mp4"

    # 4a. hook: animated hero looped to t1, cropped 9:16, hook overlay, fade-in
    ff(f'-stream_loop -1 -t {t1} -i "{hero}" -i "{hook_png}" -filter_complex '
       f'"[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps={FPS},format=rgba[bg];'
       f'[bg][1:v]overlay=0:0,fade=t=in:st=0:d=0.5[v]" -map "[v]" -an '
       f'-c:v libx264 -pix_fmt yuv420p -r {FPS} "{seg_hook}"')

    # 4b. data: ken-burns (CORRECTED idiom)
    ff(f'-loop 1 -i "{data_png}" -vf '
       f'"scale=1242:2208,zoompan=z=\'min(zoom+0.00020,1.12)\':d={n_data}:'
       f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS},setsar=1\" "
       f'-frames:v {n_data} -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r {FPS} "{seg_data}"')

    # 4c. takeaway: ken-burns + fade-out tail
    ff(f'-loop 1 -i "{take_png}" -vf '
       f'"scale=1242:2208,zoompan=z=\'min(zoom+0.00026,1.12)\':d={n_take}:'
       f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=1080x1920:fps={FPS},setsar=1,"
       f'fade=t=out:st={take_fade:.2f}:d=0.6" '
       f'-frames:v {n_take} -c:v libx264 -preset veryfast -crf 20 -pix_fmt yuv420p -r {FPS} "{seg_take}"')

    # 5. concat
    concat.write_text(f"file '{seg_hook.name}'\nfile '{seg_data.name}'\nfile '{seg_take.name}'\n", encoding="utf-8")
    ff(f'-f concat -safe 0 -i "{concat}" -c copy "{silent}"')

    # 6. mux voice (fade-out tail + pad to video length)
    afade = max(0.1, dur - 0.5)
    ff(f'-i "{silent}" -i "{voice}" -filter_complex '
       f'"[1:a]afade=t=out:st={afade:.2f}:d=0.5,apad[a]" '
       f'-map 0:v -map "[a]" -c:v copy -c:a aac -b:a 192k -shortest "{out_mp4}"')

    # 7. cleanup + verify
    for p in (seg_hook, seg_data, seg_take, silent, concat): p.unlink(missing_ok=True)
    size_mb = out_mp4.stat().st_size/1e6
    vdur = probe_dur(out_mp4)
    rc, acodec, err = sh(f'ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of csv=p=0 "{out_mp4}"')
    if size_mb > 40: raise SystemExit(f"output too large ({size_mb:.0f}MB) — encode bug")
    print(f"OK {out_mp4.name}  dur={vdur:.1f}s  size={size_mb:.1f}MB  audio={acodec.strip()}  "
          f"cuts(t1={t1},t2={t2})  voice={dur:.1f}s")

if __name__ == "__main__":
    main()
