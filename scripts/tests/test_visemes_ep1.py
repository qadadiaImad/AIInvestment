"""Tests for the FairMarketEp1 viseme production pipeline (pure parts).

GPU/网络-free: mask geometry, pad8 round-trip, composite exactness,
plan enumeration, and face->mouth calibration math.
"""
import numpy as np
import pytest

from vector.visemes_ep1 import (
    MASK_RX, MASK_RY, SOL_POSES, REX_POSES,
    ellipse_mask, pad8, unpad8, composite_rgb, plan_jobs,
    mouth_ratios_from_face, apply_ratios,
)


def test_ellipse_mask_geometry():
    m = ellipse_mask(400, 300, cx=200, cy=150, rx=80, ry=50)
    assert m.shape == (300, 400) and m.dtype == np.uint8
    assert m[150, 200] == 255            # center white
    assert m[0, 0] == 0 and m[299, 399] == 0
    ys, xs = np.nonzero(m > 128)
    assert abs((xs.max() - xs.min() + 1) - 160) <= 2
    assert abs((ys.max() - ys.min() + 1) - 100) <= 2
    # ellipse fill ratio ~ pi/4 (the proven proof mask measured 0.785)
    fill = (m > 128).sum() / (160 * 100)
    assert 0.74 <= fill <= 0.82


def test_proof_mask_ratios_are_frozen():
    # measured from the committed _inpaint_mask.png: 4.42w x 3.53w ellipse
    assert MASK_RX == pytest.approx(2.21)
    assert MASK_RY == pytest.approx(1.77)


def test_pad8_roundtrip_identity():
    rgb = np.random.randint(0, 255, (1101, 846, 3), dtype=np.uint8)
    padded, box = pad8(rgb)
    assert padded.shape[0] % 8 == 0 and padded.shape[1] % 8 == 0
    assert padded.shape[:2] == (1104, 848)
    back = unpad8(padded, box)
    assert np.array_equal(back, rgb)
    # already-multiple-of-8 input is untouched
    rgb8 = np.zeros((1096, 840, 3), dtype=np.uint8)
    p8, b8 = pad8(rgb8)
    assert p8.shape == rgb8.shape and np.array_equal(unpad8(p8, b8), rgb8)


def test_composite_exact_outside_mask():
    base = np.full((100, 80, 3), 40, dtype=np.uint8)
    gen = np.full((100, 80, 3), 200, dtype=np.uint8)
    mask = ellipse_mask(80, 100, cx=40, cy=50, rx=20, ry=15)
    out = composite_rgb(base, gen, mask)
    inside = mask > 128
    assert (out[inside] == 200).all()
    assert (out[~inside] == 40).all()      # pixel-exact identity outside


def test_plan_jobs_shape():
    jobs = plan_jobs()
    poses = {j["pose"] for j in jobs}
    assert poses == set(SOL_POSES) | set(REX_POSES)
    # Sol: no 'closed' (mustache IS closed); Rex: closed is a real viseme
    sol = [j for j in jobs if j["pose"] in SOL_POSES]
    rex = [j for j in jobs if j["pose"] in REX_POSES]
    assert not any(j["viseme"] == "closed" for j in sol)
    assert any(j["viseme"] == "closed" for j in rex)
    # every job unique output name, deterministic seed, explicit phrasing
    names = [j["out"] for j in jobs]
    assert len(names) == len(set(names))
    assert all(isinstance(j["seed"], int) for j in jobs)
    assert all(j["phrase"] for j in jobs)
    # blink jobs mask the eyes, mouth visemes mask the mouth
    assert all(j["mask"] == ("eyes" if j["viseme"] == "blink" else "mouth")
               for j in jobs)
    # production scale: ~100+ candidates, >=2 per target
    assert 100 <= len(jobs) <= 200
    from collections import Counter
    per_target = Counter((j["pose"], j["viseme"]) for j in jobs)
    assert min(per_target.values()) >= 2


def test_mouth_calibration_roundtrip():
    # synthetic: face box, known mouth -> ratios -> re-projection lands back
    face = (100, 50, 300, 250)          # x0,y0,x1,y1 -> w=200,h=200
    mouth = {"cx": 205.0, "cy": 210.0, "w": 80.0}
    r = mouth_ratios_from_face(face, mouth)
    assert r["dx"] == pytest.approx(0.025)   # (205-200)/200
    assert r["my"] == pytest.approx(0.8)     # (210-50)/200
    assert r["mw"] == pytest.approx(0.4)
    back = apply_ratios(face, r)
    assert back["cx"] == pytest.approx(mouth["cx"])
    assert back["cy"] == pytest.approx(mouth["cy"])
    assert back["w"] == pytest.approx(mouth["w"])
