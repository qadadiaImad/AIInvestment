"""Extract render frames at pose-cycle boundaries and strip them up.

The comp cycles 2-3 LoRA drawings per beat while a line is spoken
(CYCLE=[0,1,0,2] on a 14-frame swap). Each variant is an INDEPENDENT
generation, so a swap can change hair silhouette or head direction
mid-sentence. This probe samples the frame right after every swap so the
drift (if any) is visible side by side instead of asserted.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from vector.visemes_ep1 import EP, _font

FF = (Path(__file__).resolve().parents[2] / "remotion" / "node_modules" /
      "@remotion" / "compositor-win32-x64-msvc" / "ffmpeg.exe")
CYCLE = [0, 1, 0, 2]
SWAP = 14

# (beat_at, label, [pose variants]) for every beat where Sol or Rex speaks
# with more than one drawing in the cycle -- read off FairMarketEp1.tsx.
BEATS = [
    (0,   "b0 sol_smug_v1/v2",        ["sol_smug_v1", "sol_smug_v2"]),
    (110, "b110 rex_eager/_v1",       ["rex_eager", "rex_eager_v1"]),
    (195, "b195 sol_laugh/_v1",       ["sol_laugh", "sol_laugh_v1"]),
    (345, "b345 rex_shock/_v1",       ["rex_shock", "rex_shock_v1"]),
    (400, "b400 sol_point/_v1/finger", ["sol_point", "sol_point_v1",
                                        "sol_finger"]),
    (640, "b640 rex_shock_v1/shock",  ["rex_shock_v1", "rex_shock"]),
    (895, "b895 sol_wink/_v1",        ["sol_wink", "sol_wink_v1"]),
]


def swap_frames(at: int, n_poses: int, n: int = 4) -> list[tuple[int, str]]:
    """Frame 4 into each of the first n cycle slots, + which pose shows."""
    out = []
    for k in range(n):
        f = at + k * SWAP + 4
        out.append((f, str(CYCLE[k % len(CYCLE)] % n_poses)))
    return out


def extract(video: Path, frames: list[int], out_dir: Path) -> dict[int, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    # Remotion's bundled ffmpeg is a minimal build with no `select` filter,
    # so pull one frame per call. -ss AFTER -i is output seeking: decodes
    # from the start, frame-accurate (input seeking lands on a keyframe and
    # would silently sample the wrong side of a 14-frame swap).
    got = {}
    for f in frames:
        p = out_dir / f"probe_{f:04d}.png"
        subprocess.run([str(FF), "-v", "error", "-i", str(video),
                        "-ss", f"{(f + 0.5) / 30:.4f}", "-frames:v", "1",
                        str(p), "-y"], check=True)
        got[f] = p
    return got


def main(video: Path, out_dir: Path, tag: str) -> None:
    plan = [(at, label, poses, swap_frames(at, len(poses)))
            for at, label, poses in BEATS]
    frames = sorted({f for _, _, _, sf in plan for f, _ in sf})
    got = extract(video, frames, out_dir)
    for at, label, poses, sf in plan:
        tiles = []
        for f, idx in sf:
            im = Image.open(got[f]).convert("RGB")
            # Heads land anywhere from ~35% (full-body poses, where the
            # actor y is a FOOT anchor) to ~75% (busts) down the frame --
            # this band covers every beat's layout.
            im = im.crop((0, int(im.height * 0.30),
                          im.width, int(im.height * 0.90)))
            s = 620 / im.height
            im = im.resize((int(im.width * s), 620))
            tile = Image.new("RGB", (im.width, 620 + 30), "white")
            tile.paste(im, (0, 30))
            ImageDraw.Draw(tile).text(
                (5, 4), f"f{f}  pose[{idx}]={poses[int(idx)]}",
                fill="black", font=_font(19))
            tiles.append(tile)
        w = sum(t.width for t in tiles)
        strip = Image.new("RGB", (w, tiles[0].height), "white")
        x = 0
        for t in tiles:
            strip.paste(t, (x, 0))
            x += t.width
        p = out_dir / f"strip_{tag}_{label.split()[0]}.png"
        strip.save(p)
        print(f"{label}: {p}")


if __name__ == "__main__":
    vid = Path(sys.argv[1])
    main(vid, EP / f"continuity_{sys.argv[2]}", sys.argv[2])
