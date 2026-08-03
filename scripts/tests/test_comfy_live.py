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
