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
