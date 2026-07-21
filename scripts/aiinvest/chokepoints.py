"""Pure-function core for the supply-chain chokepoint layer.

Zero HTTP, zero disk I/O — every function here is a pure transform over plain dicts/
lists/strings, unit-tested in isolation (see tests/test_build_chokepoints.py).
`build_chokepoints.py` is the thin argparse/IO shell that reads
`chokepoints_source.json` (curated, committed at repo root), `capital_web.json` (curated
graph, committed at repo root), and optionally `web/public/data/graph_analysis.json`
(generated, gitignored), and calls these functions to validate/enrich/assemble the
`web/public/data/chokepoints.json` bundle. See
docs/superpowers/specs/2026-07-15-chokepoints-design.md for the binding contract this
module implements (schema in §1, validation rules in §1.5, pytest list in §2).

Two categories of check, on purpose (per CLAUDE.md rule #5 and the design spec):
  - HARD FAIL (validate_dataset / validate_entry_schema / validate_claim_schema): bad
    enum values, missing claim fields, dirty sentinel strings, duplicate ids, a
    last_reviewed date in the future. These abort the build — the curated file is wrong
    and must be fixed, not silently degraded.
  - WARN ONLY (crossref_node_ids): a node_id that doesn't (yet) resolve against
    capital_web.json. A curated entry can legitimately reference a node that predates the
    next capital_web.json refresh — don't brick the whole bundle over one stale id.

`needs_verification` (rollup_needs_verification) and `graph_crossref`
(join_graph_crossref) are fields ADDED by the build script — never hand-set in the
source file. `graph_crossref` is a DIFFERENT lens than the curated `severity_score`
(structural/graph-theoretic vs. curated analyst judgment) — the two are never conflated
here or in the UI that consumes this bundle.
"""
from __future__ import annotations

import datetime
import re

CATEGORY_ENUM = {
    "fab_concentration", "equipment_monopoly", "memory", "packaging",
    "export_controls", "power_grid", "materials", "other",
}
LAYER_ORDER = ["L0-energy", "L1-chips", "L2-infra", "L3-models", "L4-application"]
CLAIM_CLASS_ENUM = {"fact", "reported", "rumored"}
SOURCE_CLASS_ENUM = {"api", "html", "xhr-json", "filing"}

# Local copy of build_risk.py's dirty/sentinel-string convention — not imported, this
# module isn't a shared-library target (per CLAUDE.md / build_risk.py precedent).
_DIRTY_STRINGS = {"", ".", "-", "--", "n/a", "na", "none", "null"}

REQUIRED_ENTRY_FIELDS = [
    "id", "name", "category", "layers", "severity_score", "severity_rationale",
    "summary", "card_tagline", "description", "node_ids", "external_entities",
    "tickers", "claims", "mitigation_watch", "last_reviewed",
]
REQUIRED_CLAIM_FIELDS = [
    "text", "class", "source_name", "source_url", "source_class", "retrieved_at",
    "needs_verification",
]

_KEBAB_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def _utc_now():
    return datetime.datetime.now(datetime.timezone.utc)


def _parses_as_utc_iso8601(value):
    if not isinstance(value, str) or not value:
        return False
    try:
        if value.endswith("Z"):
            datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        else:
            datetime.datetime.fromisoformat(value)
        return True
    except (ValueError, TypeError):
        return False


# --------------------------------------------------------------------------- dirty-string walk


def _walk_dirty_strings(obj, path):
    problems = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            problems += _walk_dirty_strings(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            problems += _walk_dirty_strings(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        if obj.strip().lower() in _DIRTY_STRINGS:
            problems.append(f"{path}: dirty sentinel string {obj!r}")
    return problems


# --------------------------------------------------------------------------- schema validation (hard fail)


def validate_claim_schema(claim, entry_index, claim_index, entry_id):
    """Return a list of hard-fail issue strings for one claim object. Empty = valid."""
    label = f"chokepoints[{entry_index}] ({entry_id}) claims[{claim_index}]"
    if not isinstance(claim, dict):
        return [f"{label}: claim must be an object"]

    issues = []
    for field in REQUIRED_CLAIM_FIELDS:
        if field not in claim:
            issues.append(f"{label}: missing required field '{field}'")

    if "text" in claim:
        text = claim.get("text")
        if not isinstance(text, str) or not text.strip():
            issues.append(f"{label}: text must be a non-empty string")

    if "class" in claim:
        cls = claim.get("class")
        if cls not in CLAIM_CLASS_ENUM:
            issues.append(f"{label}: unknown claim class {cls!r} "
                           f"(must be one of {sorted(CLAIM_CLASS_ENUM)})")

    if "source_url" in claim:
        url = claim.get("source_url")
        if not isinstance(url, str) or not url.startswith("http"):
            issues.append(f"{label}: source_url {url!r} must start with 'http'")

    if "source_class" in claim:
        sc = claim.get("source_class")
        if sc not in SOURCE_CLASS_ENUM:
            issues.append(f"{label}: unknown source_class {sc!r} "
                           f"(must be one of {sorted(SOURCE_CLASS_ENUM)})")

    if "retrieved_at" in claim:
        ra = claim.get("retrieved_at")
        if not _parses_as_utc_iso8601(ra):
            issues.append(f"{label}: retrieved_at {ra!r} does not parse as UTC ISO-8601")

    if "needs_verification" in claim:
        nv = claim.get("needs_verification")
        if not isinstance(nv, bool):
            issues.append(f"{label}: needs_verification must be a boolean")

    return issues


def validate_entry_schema(entry, index):
    """Return a list of hard-fail issue strings for one ChokepointEntry. Empty = valid.

    Does NOT check node_ids cross-reference (warn-only, see crossref_node_ids) or
    last_reviewed-vs-now (dataset-level, needs `now`; see validate_dataset).
    """
    if not isinstance(entry, dict):
        return [f"chokepoints[{index}]: entry must be an object"]

    eid = entry.get("id")
    label = f"chokepoints[{index}] ({eid!r})"
    issues = []

    for field in REQUIRED_ENTRY_FIELDS:
        if field not in entry:
            issues.append(f"{label}: missing required field '{field}'")

    if "id" in entry:
        if not isinstance(eid, str) or not _KEBAB_RE.match(eid):
            issues.append(f"{label}: id {eid!r} is not a kebab-case slug")

    if "category" in entry:
        category = entry.get("category")
        if category not in CATEGORY_ENUM:
            issues.append(f"{label}: unknown category {category!r} "
                           f"(must be one of {sorted(CATEGORY_ENUM)})")

    if "layers" in entry:
        layers = entry.get("layers")
        if not isinstance(layers, list) or not layers:
            issues.append(f"{label}: layers must be a non-empty list")
        else:
            for layer in layers:
                if layer not in LAYER_ORDER:
                    issues.append(f"{label}: unknown layer code {layer!r} "
                                   f"(must be one of {LAYER_ORDER})")

    if "severity_score" in entry:
        score = entry.get("severity_score")
        if (not isinstance(score, (int, float)) or isinstance(score, bool)
                or not (0 <= score <= 100)):
            issues.append(f"{label}: severity_score {score!r} out of range [0, 100]")

    if "claims" in entry:
        claims = entry.get("claims")
        if not isinstance(claims, list) or not claims:
            issues.append(f"{label}: claims must be a non-empty list")
        else:
            for ci, claim in enumerate(claims):
                issues += validate_claim_schema(claim, index, ci, eid)

    if "last_reviewed" in entry:
        lr = entry.get("last_reviewed")
        if not isinstance(lr, str):
            issues.append(f"{label}: last_reviewed must be a string 'YYYY-MM-DD'")
        else:
            try:
                datetime.date.fromisoformat(lr)
            except ValueError:
                issues.append(f"{label}: last_reviewed {lr!r} is not a valid ISO date")

    for field in ("node_ids", "external_entities", "tickers", "mitigation_watch"):
        if field in entry and not isinstance(entry.get(field), list):
            issues.append(f"{label}: {field} must be a list")

    issues += _walk_dirty_strings(entry, label)
    return issues


def validate_dataset(source_doc, now=None):
    """Full hard-fail validation of a loaded chokepoints_source.json dict.

    Returns a list of issue strings; empty = every entry is valid. Does NOT include
    node_ids cross-reference warnings (that's warn-only — see crossref_node_ids), which
    are collected separately into `validation.node_crossref_warnings` by the caller.
    """
    if now is None:
        now = _utc_now()
    if not isinstance(source_doc, dict):
        return ["source: document must be an object"]

    chokepoints = source_doc.get("chokepoints")
    if not isinstance(chokepoints, list):
        return ["source: 'chokepoints' must be a list"]

    issues = []
    seen_ids = {}
    for i, entry in enumerate(chokepoints):
        issues += validate_entry_schema(entry, i)

        if not isinstance(entry, dict):
            continue

        eid = entry.get("id")
        if isinstance(eid, str):
            if eid in seen_ids:
                issues.append(f"chokepoints[{i}]: duplicate id {eid!r} "
                               f"(first seen at index {seen_ids[eid]})")
            else:
                seen_ids[eid] = i

        lr = entry.get("last_reviewed")
        if isinstance(lr, str):
            try:
                d = datetime.date.fromisoformat(lr)
                if d > now.date():
                    issues.append(f"chokepoints[{i}] ({eid!r}): last_reviewed {lr!r} is "
                                   f"in the future relative to generated_at "
                                   f"({now.date().isoformat()})")
            except ValueError:
                pass  # already flagged by validate_entry_schema

    return issues


# --------------------------------------------------------------------------- node cross-reference (warn only)


def build_node_id_set(capital_web_doc):
    """capital_web.json dict -> set of node ids. Empty set if doc is falsy/malformed."""
    if not capital_web_doc:
        return set()
    nodes = capital_web_doc.get("nodes") or []
    return {n.get("id") for n in nodes if isinstance(n, dict) and n.get("id")}


def crossref_node_ids(entry, valid_node_ids):
    """Return warning strings (never hard-fail issues) for node_ids not present in
    valid_node_ids. Empty list = every node_id resolved (or the entry has none)."""
    warnings = []
    eid = entry.get("id")
    n = len(valid_node_ids)
    for nid in entry.get("node_ids") or []:
        if nid not in valid_node_ids:
            warnings.append(f"{eid}: node_ids id '{nid}' not found in capital_web.json "
                             f"({n} nodes checked)")
    return warnings


# --------------------------------------------------------------------------- build-time enrichment


def rollup_needs_verification(entry):
    """True if ANY claim on this entry has needs_verification=true. Never hand-set in
    the source file — always computed here."""
    return any(bool(c.get("needs_verification")) for c in (entry.get("claims") or []))


def build_graph_lookup(graph_analysis_doc):
    """graph_analysis.json dict -> {node_id: {"is_articulation": bool, "betweenness":
    float}}. Empty dict if the doc is absent/malformed — callers must treat an empty
    lookup as 'degrade gracefully', not as an error."""
    if not graph_analysis_doc:
        return {}
    nodes = graph_analysis_doc.get("nodes") or []
    lookup = {}
    for n in nodes:
        if not isinstance(n, dict):
            continue
        nid = n.get("id")
        if not nid:
            continue
        bw = n.get("betweenness")
        if not isinstance(bw, (int, float)) or isinstance(bw, bool):
            bw = 0.0
        lookup[nid] = {"is_articulation": bool(n.get("is_articulation")), "betweenness": bw}
    return lookup


def join_graph_crossref(entry, graph_lookup):
    """Join one entry's node_ids against graph_lookup (see build_graph_lookup).

    max betweenness / OR-of-is_articulation across the entry's node_ids. Degrades to
    {source_class:"computed", is_articulation:False, betweenness:0.0} when graph_lookup
    is empty, node_ids is empty, or none of the entry's node_ids are present in the
    lookup — corroborating evidence only, never a hard dependency."""
    default = {"source_class": "computed", "is_articulation": False, "betweenness": 0.0}
    if not graph_lookup:
        return dict(default)

    node_ids = entry.get("node_ids") or []
    is_articulation = False
    max_betweenness = 0.0
    found_any = False
    for nid in node_ids:
        info = graph_lookup.get(nid)
        if info is None:
            continue
        found_any = True
        if info.get("is_articulation"):
            is_articulation = True
        bw = info.get("betweenness") or 0.0
        if bw > max_betweenness:
            max_betweenness = bw

    if not found_any:
        return dict(default)
    return {"source_class": "computed", "is_articulation": is_articulation,
            "betweenness": max_betweenness}


def build_entries(source_doc, valid_node_ids, graph_lookup):
    """Assumes source_doc already passed validate_dataset with zero hard-fail issues.

    Returns (entries, node_crossref_warnings) — entries are the curated fields plus the
    two build-time-added fields (needs_verification, graph_crossref); warnings are the
    flattened warn-only node_ids cross-reference messages across all entries."""
    entries = []
    warnings = []
    for raw in source_doc.get("chokepoints") or []:
        entry = dict(raw)
        warnings += crossref_node_ids(entry, valid_node_ids)
        entry["needs_verification"] = rollup_needs_verification(entry)
        entry["graph_crossref"] = join_graph_crossref(entry, graph_lookup)
        entries.append(entry)
    return entries, warnings


# --------------------------------------------------------------------------- summary


def compute_summary(entries, valid_node_ids):
    """entries: output of build_entries (curated fields + needs_verification +
    graph_crossref). valid_node_ids: set from build_node_id_set. Pure aggregation."""
    n_entries = len(entries)
    by_category = {}
    by_layer = {}
    n_claims = n_fact = n_reported = n_rumored = 0
    n_needs_verification = 0
    all_node_ids = set()

    for e in entries:
        category = e.get("category")
        if category is not None:
            by_category[category] = by_category.get(category, 0) + 1

        for layer in e.get("layers") or []:
            by_layer[layer] = by_layer.get(layer, 0) + 1

        claims = e.get("claims") or []
        n_claims += len(claims)
        for c in claims:
            cls = c.get("class")
            if cls == "fact":
                n_fact += 1
            elif cls == "reported":
                n_reported += 1
            elif cls == "rumored":
                n_rumored += 1

        if e.get("needs_verification"):
            n_needs_verification += 1

        all_node_ids.update(e.get("node_ids") or [])

    resolved = {nid for nid in all_node_ids if nid in valid_node_ids}
    unresolved = all_node_ids - resolved

    return {
        "n_entries": n_entries,
        "by_category": by_category,
        "by_layer": by_layer,
        "n_claims": n_claims,
        "n_fact": n_fact,
        "n_reported": n_reported,
        "n_rumored": n_rumored,
        "n_needs_verification": n_needs_verification,
        "n_node_ids_total": len(all_node_ids),
        "n_node_ids_resolved": len(resolved),
        "n_node_ids_unresolved": len(unresolved),
    }
