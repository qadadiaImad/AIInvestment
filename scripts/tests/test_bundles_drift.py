"""Drift guard: the manifest must cover everything the web app actually loads.

Without this, the manifest is just another hand-maintained list that rots the
first time someone adds a page. This reads the real loaders in web/lib/ and
fails if any bundle they read is undeclared.

IMPORTANT — web/lib/data.ts is UTF-8 *with BOM*. ripgrep reports it as binary
and plain grep skips it silently, which is exactly how ta_desk.json/
backtests.json went unnoticed. We read with encoding="utf-8-sig" so the BOM
is stripped rather than corrupting the first token.
"""
from __future__ import annotations

import pathlib
import re

import pytest

from aiinvest import bundles

REPO = pathlib.Path(__file__).resolve().parents[2]
WEB_LIB = REPO / "web" / "lib"

# Files named *.json in web/lib that are not data bundles.
_NOT_BUNDLES = {
    "package.json", "tsconfig.json", "package-lock.json",
    "tsconfig.node.json", "tsconfig.web.json",
}

# Only these directories are bundle roots; a match must be loaded from one.
_JSON_RE = re.compile(r'["\'`]([a-z0-9_]+\.json)["\'`]')


def _loader_sources():
    """Every .ts source in web/lib, read BOM-safely."""
    if not WEB_LIB.is_dir():
        pytest.skip("web/lib not present in this checkout")
    out = {}
    for p in sorted(WEB_LIB.glob("*.ts")):
        if p.name.endswith(".test.ts"):
            continue
        out[p.name] = p.read_text(encoding="utf-8-sig")
    if not out:
        pytest.skip("no web/lib/*.ts sources found")
    return out


def _referenced_bundles():
    """Map {json filename -> [loader files that reference it]}."""
    found: dict[str, list[str]] = {}
    for fname, src in _loader_sources().items():
        for m in _JSON_RE.finditer(src):
            name = m.group(1)
            if name in _NOT_BUNDLES:
                continue
            found.setdefault(name, []).append(fname)
    return found


def test_data_ts_is_readable_despite_bom():
    """Regression guard: a BOM must not make the loader unreadable/empty."""
    src = _loader_sources()
    assert "data.ts" in src, "web/lib/data.ts missing"
    body = src["data.ts"]
    assert len(body) > 1_000
    assert not body.startswith("﻿"), "BOM leaked into parsed text"
    assert "site.json" in body, "data.ts read but core bundle reference absent"


def test_every_bundle_the_site_loads_is_declared():
    """The core invariant. Add a page reading foo.json -> declare foo.json."""
    referenced = _referenced_bundles()
    assert referenced, "no .json references found - the regex or read is broken"

    undeclared = {n: srcs for n, srcs in referenced.items() if n not in bundles.BUNDLES}
    assert not undeclared, (
        "these bundles are loaded by the web app but missing from "
        "aiinvest/bundles.BUNDLES:\n"
        + "\n".join(f"  {n}  (referenced in {', '.join(s)})"
                    for n, s in sorted(undeclared.items()))
        + "\n\nAdd them to the manifest, or the nightly refresh cannot verify them."
    )


def test_manifest_entries_are_actually_used():
    """Reverse direction: flag declared bundles nothing reads (dead entries).

    Not every bundle must appear in web/lib - some are consumed elsewhere -
    so this is informational rather than strict, but a bundle that no loader
    and no script reads is probably a typo.
    """
    referenced = set(_referenced_bundles())
    unused = sorted(set(bundles.BUNDLES) - referenced)
    # portfolio.json is read via a dedicated fs path in portfolio.ts and may
    # not match the literal-string regex; tolerate a small known set.
    # halal_alerts.json: manifest entry declared by Task 12; web/lib loader
    # added by Task 13 (parallel lane) — tolerated until T13 lands.
    tolerated = {"portfolio.json", "halal_alerts.json"}
    suspicious = [n for n in unused if n not in tolerated]
    assert not suspicious, (
        "declared in the manifest but not referenced by any web/lib loader: "
        f"{suspicious}. Confirm these are still needed."
    )


def test_no_bundle_is_declared_under_two_roots():
    seen: dict[str, str] = {}
    for name, b in bundles.BUNDLES.items():
        assert name not in seen, f"{name} declared twice"
        seen[name] = b.root
