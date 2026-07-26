"""The Daily Screen v2 — layer -> hero-image resolver.

Maps a halal-verdict `layer` value (e.g. "Q4-security") to a staticFile-
relative image path the Remotion reel loads via `staticFile(...)`. Brand
assets live on disk at `remotion/public/heroes/<layer>.jpg`; unknown/missing
layers fall back to `heroes/_default.jpg` so the reel never crashes on a
layer this module doesn't recognize yet.

Pure — no file I/O, no network. `hero_abs_path` only joins path segments; it
does not check the file exists (callers that need on-disk data, e.g. a copy
step, do that themselves).

Educational/research only — not financial or religious advice.
"""
from __future__ import annotations

import pathlib

# The 8 live layer values, sourced from web/public/data/halal.json verdicts'
# "layer" field (see .superpowers/sdd/task-1-brief.md). Each maps to its own
# staticFile-relative hero image -- no leading slash (Remotion's
# `staticFile()` resolves relative to remotion/public/).
LAYER_HEROES: dict[str, str] = {
    "L0-energy": "heroes/L0-energy.jpg",
    "L1-chips": "heroes/L1-chips.jpg",
    "L2-infra": "heroes/L2-infra.jpg",
    "L4-application": "heroes/L4-application.jpg",
    "Q1-hardware": "heroes/Q1-hardware.jpg",
    "Q3-software": "heroes/Q3-software.jpg",
    "Q5-applications": "heroes/Q5-applications.jpg",
    "Q4-security": "heroes/Q4-security.jpg",
}

DEFAULT_HERO = "heroes/_default.jpg"


def hero_for_layer(layer: str | None) -> str:
    """staticFile-relative hero path for `layer`; `_default` for None/unknown.

    Never raises -- any layer value that isn't a key in LAYER_HEROES
    (including None, "", or a typo'd/future layer) resolves to DEFAULT_HERO
    so the reel always has an image to render.
    """
    return LAYER_HEROES.get(layer, DEFAULT_HERO)


def hero_abs_path(layer: str | None, remotion_public_dir) -> pathlib.Path:
    """On-disk path to `layer`'s hero file under `remotion_public_dir`.

    `remotion_public_dir` is the Remotion `public/` directory (any
    path-like); the returned path is `remotion_public_dir / hero_for_layer(layer)`,
    with the "heroes/<file>.jpg" split into real path segments.
    """
    rel = hero_for_layer(layer)
    return pathlib.Path(remotion_public_dir).joinpath(*rel.split("/"))
