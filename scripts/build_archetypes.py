"""Assemble the investor-archetype scorecard bundle: web/public/data/archetypes.json
(schema "archetypes-v1").

NETWORK-FREE. The only input is web/public/data/site.json (from export_site.py) --
every number here is a deterministic, rule-based transform of already-retrieved
fundamentals. Zero LLM calls anywhere. source_class="computed" at the top level is
deliberate: this stage performs zero new retrieval, it adds a methodology_version, not a
new fact. See docs/superpowers/specs/2026-07-14-archetypes-design.md for the binding
contract.

Usage:
    python build_archetypes.py
    python build_archetypes.py --site /tmp/site.json --out /tmp/archetypes.json
"""
from __future__ import annotations

import argparse
import datetime
import json
import pathlib

from aiinvest import archetypes as arche


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _iso(dt):
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")


def _load_json(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def _default_data_dir():
    repo = pathlib.Path(__file__).resolve().parent.parent
    return str(repo / "web" / "public" / "data")


def _default_site_path():
    return str(pathlib.Path(_default_data_dir()) / "site.json")


def _default_out_path():
    return str(pathlib.Path(_default_data_dir()) / "archetypes.json")


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Assemble archetypes.json from already-retrieved site.json (no network).")
    ap.add_argument("--site", default=_default_site_path(),
                    help="Path to site.json (default: web/public/data/site.json).")
    ap.add_argument("--out", default=_default_out_path(),
                    help="Output path (default: web/public/data/archetypes.json).")
    args = ap.parse_args(argv)

    site = _load_json(args.site)
    if site is None:
        print(f"error: site.json not found or unparseable at {args.site}")
        return 1

    generated_at = _iso(_utc_now())
    bundle = arche.build_archetypes(site, generated_at)

    out_path = pathlib.Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")

    n = len(bundle["per_stock"])
    print(f"archetypes: {n} symbols scored -> {out_path}")
    print(f"  warnings: {len(bundle.get('warnings', []))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
