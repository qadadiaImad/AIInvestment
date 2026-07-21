"""Data-bundle manifest — the single declaration of what the site requires.

The problem this solves: every refresh driver reports *per-step exit codes*,
never whether the artifacts a step was supposed to produce actually landed.
A step that is guarded (skips when an input is absent) exits 0 and produces
nothing, so a run can print ``failures: none`` while the site 500s. Observed
2026-07-20: refresh_daily.py reported 15/15 OK with ta_desk.json,
congress.json and backtests.json all absent.

The manifest inverts that: it declares the *artifacts* the web app needs —
not the steps someone remembered to list — and a verifier checks them on
disk. Requirements come from the web loaders (web/lib/*.ts); the drift guard
in tests/test_bundles_drift.py keeps the two in sync.

Policy (agreed with the owner):
  * missing / truncated / corrupt required bundle -> FAILURE (exit non-zero)
  * present but past its cadence                  -> WARNING (loud, exit 0)
  * every problem states *why* and *how to rerun*

Educational/research only — not investment advice.
"""
from __future__ import annotations

import dataclasses
import datetime
import json
import pathlib

from . import merge

__all__ = [
    "PUBLIC", "WEBDATA", "Bundle", "BUNDLES", "Result",
    "OK", "MISSING", "STALE", "TOO_SMALL", "UNPARSEABLE",
    "check_bundle", "check_all", "failures", "warnings",
    "for_driver", "render_verification",
    "DRV_DAILY", "DRV_TA", "DRV_CONGRESS",
]

# ---------------------------------------------------------------------------
# Roots. Two of them, deliberately.
# ---------------------------------------------------------------------------

#: Statically served by Next.js — anything here is public.
PUBLIC = "web/public/data"

#: Server-only. portfolio.json lives here so positions are never served as a
#: static asset (which would bypass the /terminal route gate entirely).
WEBDATA = "web/data"

# ---------------------------------------------------------------------------
# Statuses
# ---------------------------------------------------------------------------

OK = "ok"
MISSING = "missing"
STALE = "stale"
TOO_SMALL = "too_small"
UNPARSEABLE = "unparseable"


@dataclasses.dataclass(frozen=True)
class Bundle:
    """One artifact the site loads.

    ``required=False`` means *may legitimately be absent* (an optional merge,
    or data only the owner has). It never means "may be corrupt": a present
    but unreadable bundle is a failure regardless.

    ``max_age_h`` encodes the artifact's own cadence, not one blanket rule —
    congress PTR filings move monthly, backtests weekly, quotes daily.
    """

    name: str
    root: str
    produced_by: str
    required: bool = True
    max_age_h: int = 30
    min_bytes: int = 1_000
    #: Owning refresh driver; each verifies only its own outputs, so a
    #: not-yet-run monthly job never false-alarms a daily one. None = manual.
    driver: str | None = None
    note: str = ""


# Cadence constants, so the intent is legible at each call site.
_DAILY = 30       # 24h + slack for a late run
_WEEKLY = 192     # 8d
_MONTHLY = 744    # 31d
_RARELY = 2_160   # 90d — curated datasets that change by hand

# Owning drivers.
DRV_DAILY = "refresh_daily.py"
DRV_TA = "refresh_ta.py"
DRV_CONGRESS = "refresh_congress.py"


BUNDLES: dict[str, Bundle] = {
    b.name: b
    for b in [
        # --- core, rebuilt every day -------------------------------------
        Bundle("site.json", PUBLIC, "export_site.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=400_000),
        Bundle("quantum.json", PUBLIC, "export_quantum.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=30_000),
        Bundle("news.json", PUBLIC, "pull_news.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=150_000),
        Bundle("macro.json", PUBLIC, "pull_macro.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=10_000),
        Bundle("risk.json", PUBLIC, "build_risk.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=20_000),
        Bundle("archetypes.json", PUBLIC, "build_archetypes.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=300_000),
        Bundle("graph_analysis.json", PUBLIC, "run_graph_analysis.py",
               driver=DRV_DAILY, max_age_h=_DAILY, min_bytes=20_000),
        Bundle("halal.json", PUBLIC, "export_halal.py", driver=DRV_DAILY,
               max_age_h=_DAILY, min_bytes=100_000,
               note="Sharia screening verdicts (AAOIFI/FTSE/MSCI worked math)"),
        Bundle("halal_alerts.json", PUBLIC, "export_halal.py", driver=DRV_DAILY,
               required=False, max_age_h=_DAILY, min_bytes=50,
               note="halal compliance-change feed; empty is legitimate"),

        # --- own schedule: refresh_ta.py, deliberately not in refresh_daily
        Bundle("ta_desk.json", PUBLIC, "refresh_ta.py", driver=DRV_TA,
               max_age_h=_DAILY, min_bytes=20_000,
               note="separate driver by design (how_to_update.md)"),

        # --- slower cadences ---------------------------------------------
        Bundle("backtests.json", PUBLIC, "run_backtest.py", driver=DRV_DAILY,
               max_age_h=_WEEKLY, min_bytes=200_000),
        Bundle("congress.json", PUBLIC, "export_congress.py", driver=DRV_CONGRESS,
               max_age_h=_MONTHLY, min_bytes=1_000_000,
               note="PTR filings move monthly"),
        Bundle("chokepoints.json", PUBLIC, "build_chokepoints.py", driver=DRV_DAILY,
               max_age_h=_RARELY, min_bytes=10_000,
               note="hand-curated source dataset"),

        # --- optional merges: absent is legitimate ------------------------
        Bundle("congress_stocks.json", PUBLIC, "export_congress_stocks.py",
               driver=DRV_CONGRESS, required=False, max_age_h=_MONTHLY,
               min_bytes=1_000, note="optional merge in data.ts"),
        Bundle("extra_stocks.json", PUBLIC, "pull_kalray.py",
               driver=None, required=False, max_age_h=_MONTHLY, min_bytes=200,
               note="optional merge in data.ts; no driver builds it"),

        # --- server-only, owner-supplied ---------------------------------
        Bundle("portfolio.json", WEBDATA, "build_portfolio.py", driver=DRV_DAILY,
               required=False, max_age_h=_DAILY, min_bytes=500,
               note="needs data/portfolio/positions.json; NEVER public"),
    ]
}


@dataclasses.dataclass
class Result:
    """Outcome of checking one bundle, with the reason and the remedy."""

    bundle: Bundle
    status: str
    detail: str = ""
    age_h: float | None = None
    age_source: str | None = None   # "generated_at" | "mtime" | None
    size: int | None = None
    path: str = ""

    @property
    def is_failure(self) -> bool:
        if self.status in (TOO_SMALL, UNPARSEABLE):
            return True
        return self.status == MISSING and self.bundle.required

    @property
    def is_warning(self) -> bool:
        if self.status == STALE:
            return True
        return self.status == MISSING and not self.bundle.required

    @property
    def fix_command(self) -> str:
        """The exact command that regenerates this bundle."""
        return f"python {self.bundle.produced_by}"


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------

def _iso(dt: datetime.datetime) -> str:
    return dt.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _age_hours(stamp: str, now: str) -> float:
    delta = merge._parse(now) - merge._parse(stamp)
    return delta.total_seconds() / 3600.0


def check_bundle(bundle: Bundle, repo_root, now: str) -> Result:
    """Check one bundle on disk. Never raises — every fault becomes a Result."""
    root = pathlib.Path(repo_root)
    path = root / bundle.root / bundle.name
    rel = f"{bundle.root}/{bundle.name}"

    if not path.is_file():
        return Result(
            bundle, MISSING, path=rel,
            detail=(f"not found at {rel}"
                    + ("" if bundle.required else " (optional - absence is allowed)")),
        )

    size = path.stat().st_size
    if size < bundle.min_bytes:
        return Result(
            bundle, TOO_SMALL, path=rel, size=size,
            detail=(f"{size:,} bytes is below the {bundle.min_bytes:,}-byte floor "
                    "- the producer likely wrote a truncated or empty bundle"),
        )

    try:
        with path.open(encoding="utf-8") as fh:
            payload = json.load(fh)
    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as exc:
        return Result(
            bundle, UNPARSEABLE, path=rel, size=size,
            detail=f"does not parse as JSON ({type(exc).__name__}: {exc})",
        )

    # Prefer the bundle's own stamp; fall back to file mtime so we never
    # report a confident "fresh" on an unknown age.
    stamp, source = None, None
    if isinstance(payload, dict) and isinstance(payload.get("generated_at"), str):
        stamp, source = payload["generated_at"], "generated_at"
    else:
        stamp = _iso(datetime.datetime.fromtimestamp(
            path.stat().st_mtime, datetime.timezone.utc))
        source = "mtime"

    try:
        age = _age_hours(stamp, now)
    except (ValueError, TypeError):
        return Result(
            bundle, OK, path=rel, size=size, age_source=source,
            detail=f"unreadable timestamp {stamp!r}; age not verified",
        )

    if merge.is_stale(stamp, now, max_age_hours=bundle.max_age_h):
        return Result(
            bundle, STALE, path=rel, size=size, age_h=age, age_source=source,
            detail=(f"{age:.1f}h old (limit {bundle.max_age_h}h, by {source}) "
                    "- data is past its cadence"),
        )

    return Result(bundle, OK, path=rel, size=size, age_h=age, age_source=source,
                  detail=f"{age:.1f}h old (limit {bundle.max_age_h}h)")


def check_all(repo_root, now: str | None = None, names=None) -> list[Result]:
    """Check every manifest entry (or the subset named in ``names``)."""
    if now is None:
        now = _iso(datetime.datetime.now(datetime.timezone.utc))
    selected = BUNDLES.values() if names is None else [BUNDLES[n] for n in names]
    return [check_bundle(b, repo_root, now) for b in selected]


def failures(results) -> list[Result]:
    return [r for r in results if r.is_failure]


def warnings(results) -> list[Result]:
    return [r for r in results if r.is_warning]


def for_driver(driver: str) -> list[Bundle]:
    """The bundles a given refresh driver is responsible for producing."""
    return [b for b in BUNDLES.values() if b.driver == driver]


def render_verification(repo_root, driver: str | None = None,
                        now: str | None = None) -> tuple[list[str], int]:
    """Verify bundles and render driver-summary lines.

    Returns ``(lines, n_failed)``. Drivers print the lines and fold
    ``n_failed`` into their exit code, so a run that produced no artifacts
    can no longer report success.

    ASCII only: these land in a cp1252 Windows console.
    """
    names = None if driver is None else [b.name for b in for_driver(driver)]
    if names is not None and not names:
        return ([], 0)

    results = check_all(repo_root, now, names)
    fails, warns = failures(results), warnings(results)
    scope = "all" if driver is None else driver

    lines = [f"  bundles: {len(results) - len(fails)}/{len(results)} verified "
             f"({len(fails)} failed, {len(warns)} warned) [scope: {scope}]"]

    for r in fails:
        lines.append(f"    FAIL {r.bundle.name}: {r.detail}")
        lines.append(f"         fix: cd scripts && python {r.bundle.produced_by}")
    for r in warns:
        lines.append(f"    WARN {r.bundle.name}: {r.detail}")

    return (lines, len(fails))
