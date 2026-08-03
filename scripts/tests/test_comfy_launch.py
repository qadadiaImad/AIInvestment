import pytest

from comfy import launch


def test_attaches_when_already_up():
    got = launch.ensure_server(
        spawn=lambda argv: pytest.fail("must not spawn"), probe=lambda: True)
    assert got == "already-running"


def test_spawns_then_waits_until_probe_true():
    probes = iter([False, False, True])
    spawned = []
    got = launch.ensure_server(spawn=spawned.append,
                               probe=lambda: next(probes),
                               wait_s=10, _sleep=lambda s: None)
    assert got == "started"
    assert spawned == [launch.SERVER_ARGV]


def test_raises_when_server_never_comes_up():
    with pytest.raises(TimeoutError):
        launch.ensure_server(spawn=lambda argv: None, probe=lambda: False,
                             wait_s=0.01, _sleep=lambda s: None)
