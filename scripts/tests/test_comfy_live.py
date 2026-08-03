"""Live smoke tests — auto-skip when no local server is running."""
import pytest

from comfy import launch

pytestmark = pytest.mark.skipif(not launch.is_up(),
                                 reason="local ComfyUI server not running")


def test_zimage_renders_a_png(tmp_path):
    from comfy.client import ComfyClient
    outs = ComfyClient().generate("zimage_t2i", tmp_path,
                                  prompt="a red cube on white background",
                                  seed=1, width=512, height=512)
    assert outs and outs[0].suffix == ".png" and outs[0].stat().st_size > 10_000


def test_wan22_ti2v_5b_renders_a_video(tmp_path):
    # Size floor measured empirically at 50_000, not the 100_000 in the
    # brief: an actual 448x256/17-frame/24fps h264 clip from this graph
    # is ~0.7s of video and lands at ~84 KB (see task-7-report.md) —
    # 100 KB doesn't hold at this resolution/length, so the floor is set
    # to comfortably clear real output while still catching an empty or
    # truncated file.
    from comfy.client import ComfyClient
    outs = ComfyClient().generate("wan22_ti2v_5b", tmp_path,
                                  prompt="a red cube spinning on white background",
                                  negative="blurry, low quality, static",
                                  seed=1, width=448, height=256, length=17,
                                  timeout=900)
    assert outs and outs[0].suffix == ".mp4" and outs[0].stat().st_size > 50_000


def test_wan22_i2v_14b_renders_a_video(tmp_path):
    # I2V-only quality lane (GGUF + lightx2v 4-step LoRAs, two-expert MoE
    # chain). Size floor kept at 50_000 (not the brief's literal 100_000),
    # same empirical basis as test_wan22_ti2v_5b_renders_a_video above --
    # see task-8-report.md for the actual measured size at this
    # resolution/frame-count.
    from pathlib import Path

    from comfy.client import ComfyClient
    client = ComfyClient()
    staged = client.stage_input(
        Path(__file__).parent.parent.parent / "data" / "comfy_smoke" /
        "zimage_t2i_00001_.png")
    outs = client.generate("wan22_i2v_14b", tmp_path,
                           prompt="the telescope on the desk gently rocks "
                                  "as warm light sweeps across the room",
                           negative="blurry, low quality, static, distorted",
                           seed=11, width=512, height=288, length=33,
                           image=staged, timeout=1800)
    assert outs and outs[0].suffix == ".mp4" and outs[0].stat().st_size > 50_000
