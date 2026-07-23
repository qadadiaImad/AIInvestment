"""The Daily Screen — copy engine: one ticker's halal-screen data -> A/B hook
props for the SlideStoryReel video, a lint-clean caption, and carousel-kit copy.

`build_daily(ticker, bundle, story, date_str) -> dict` post-processes
`build_reel_props.build_props(...)`'s output:

  1. Rewrites `tickerSub` to the Daily Screen banner.
  2. Inserts a cliffhanger tease beat immediately before the `stamp` beat, so
     the verdict is withheld one beat longer.
  3. Rewrites the endcard into a trust close (method shown, dated, corrected).
  4. Rewrites every ratio VO sentence viscerally (money analogy or limit
     comparison — never a bare percent).
  5. Produces two hook variants — A (specific-number) and B (contrarian) —
     that differ ONLY in `beats[0]`/`vo[0]`, for A/B testing the hook.
  6. Overrides the A hook for "flip" stories (a verdict that just changed).

Every VO line and the caption are lint-checked (`aiinvest.halal_lint`) before
`build_daily` returns; any violation raises `LintError` rather than emit
unvetted copy. A code-enforced gate (`_pre_stamp_leak_violations`) also checks
every beat before the `stamp` beat, in both hook variants, for verdict-leaking
substrings ("pass"/"fail"/"review") — this rail is enforced on every future
template edit, not just by test coverage.

Pure — no file I/O. `copy.deepcopy` is used per variant so the A/B split never
lets one variant's edits bleed into the other.

Educational/research only — not financial or religious advice.
"""
from __future__ import annotations

import copy
import json
import pathlib
import re

import build_reel_props
from build_reel_props import DISCLAIMER
from aiinvest import heroes
from aiinvest.halal_join import screen_card_data
from aiinvest.halal_lint import lint_halal_script, lint_visceral, lint_editorial

# Re-exported so callers only need to import daily_copy (per the task-3 brief).
InsufficientDataError = build_reel_props.InsufficientDataError

# Substrings that would leak the still-hidden verdict before the stamp beat.
# Checked against every variant's joined, lowercased pre-stamp VO — see
# `_pre_stamp_leak_violations` below.
_LEAK_SUBSTRINGS = ("pass", "fail", "review")


# --- plain-words company intro (task-9: owner-requested, replaces the greeting) --

_COMPANY_LINES_PATH = pathlib.Path(__file__).resolve().parent / "company_lines.json"
_company_lines_cache = None


def _load_company_lines():
    """Read scripts/aiinvest/company_lines.json once, cache in-process.

    Never raises — a missing/corrupt file just means every ticker falls back
    to `_fallback_descriptor` (see below); the reel must still build."""
    global _company_lines_cache
    if _company_lines_cache is None:
        try:
            _company_lines_cache = json.loads(
                _COMPANY_LINES_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            _company_lines_cache = {}
    return _company_lines_cache


# Human-readable fallback basis per AI/quantum-stack layer, used only when a
# ticker is missing from company_lines.json AND has no business categories.
_LAYER_FALLBACK_BASIS = {
    "L0-energy": "the power business",
    "L1-chips": "the chip business",
    "L2-infra": "the datacenter and cloud business",
    "L3-models": "the AI model business",
    "L4-application": "the software business",
    "Q1-hardware": "the quantum computing hardware business",
    "Q3-software": "the quantum software business",
    "Q4-security": "the digital security business",
    "Q5-applications": "the finance and pharma business",
}


def _fallback_descriptor(ticker, verdict):
    """"the company behind <basis>" — derived from business categories, then
    layer, then a generic basis. Never crashes, never returns an empty string."""
    verdict = verdict or {}
    business = verdict.get("business") or {}
    categories = business.get("categories") or []
    if categories:
        basis = " and ".join(
            str(c).replace("-", " ").replace("_", " ") for c in categories if c)
        if basis:
            return f"the company behind {basis}"
    layer = verdict.get("layer")
    basis = _LAYER_FALLBACK_BASIS.get(layer, "this ticker's business")
    return f"the company behind {basis}"


def _company_descriptor(ticker, verdict):
    """"the company that ..." (mapped) or the "the company behind ..." fallback."""
    lines = _load_company_lines()
    descriptor = lines.get(ticker)
    if descriptor:
        return descriptor
    return _fallback_descriptor(ticker, verdict)


def _company_line(ticker, descriptor):
    return f"{ticker} — {descriptor}."


# --- dramatize: shocking-but-factual line from the binding standards row ----

_PCT_NUM_RE = re.compile(r"([\d.]+)")
_MARGIN_RE = re.compile(r"^([+\-−])\s*(\d+(?:\.\d+)?)\s*pt$")
_MCAP_RE = re.compile(r"mcap|market|cap", re.IGNORECASE)


def _pct_value(s):
    """Parse a screen_card_data row's '561.4%'-style string -> 561.4 (float);
    None for a non-numeric placeholder ('—') or missing field."""
    if not isinstance(s, str):
        return None
    m = _PCT_NUM_RE.search(s)
    return float(m.group(1)) if m else None


def _signed_margin_pt(s):
    """Parse a row's '+9.0pt' / '−531.4pt' margin string -> signed float
    (points), or None if unparseable. Accepts both the unicode minus
    (−, what `_row` in halal_join.py actually emits) and a plain
    ASCII hyphen, defensively."""
    if not isinstance(s, str):
        return None
    m = _MARGIN_RE.match(s.strip())
    if not m:
        return None
    sign, val = m.group(1), float(m.group(2))
    return -val if sign in ("-", "−") else val


# The neutral "nothing to see here" line — also the SHOCK/CLEAN discriminator
# used by `is_shock` (see below): dramatize returns this exact string iff
# every debt line is under its limit.
_CLEAN_LINE = "Every debt line lands under the limit."


def dramatize(card):
    """A factual-extreme one-liner from `card["standards_rows"]`'s binding row
    (the min-signed-margin numeric row — the one closest to, or furthest past,
    its threshold).

      * mcap-relative debt row (binding_label mentions mcap/market/cap) AND
        the row's DISPLAYED multiple (ratio/100 — the real "times what the
        company is worth" figure) is >= 3.0x -> the extreme "owes N times
        ... isn't close" line. Reviewed defect: this used to gate on
        `ratio/threshold >= 3` while displaying `ratio/100`, so a row at
        ~0.9x market cap (over its 30% limit, but nowhere near "isn't
        close") could hit the extreme branch and read as absurd hyperbole
        ("owes 0.9 times ... isn't close"). Gating on the displayed multiple
        itself keeps the claim truthful by construction.
      * severity (`ratio/threshold`) > 1x over the limit (any binding row,
        including an mcap row below the 3x extreme gate) -> the plain
        ratio-vs-limit sentence.
      * otherwise -> the neutral `_CLEAN_LINE`.

    Always $/%/limit-anchored (passes `lint_visceral`); the wording never uses
    a banned editorial word (passes `lint_editorial`) or a "pass"/"fail"/
    "review" token (verdict stays withheld) — by construction, not by luck:
    every branch's string is a fixed template with only numbers/labels
    interpolated. Pure; never raises — a missing/malformed card degrades to
    the neutral line rather than crashing the reel build.
    """
    rows = (card or {}).get("standards_rows") or []
    numeric = []
    for row in rows:
        ratio = _pct_value(row.get("ratio"))
        threshold = _pct_value(row.get("threshold"))
        margin = _signed_margin_pt(row.get("margin"))
        if ratio is None or threshold is None or margin is None:
            continue
        numeric.append((margin, ratio, threshold, row))
    if not numeric:
        return _CLEAN_LINE

    margin, ratio, threshold, binding = min(numeric, key=lambda t: t[0])
    if threshold <= 0:
        return _CLEAN_LINE

    severity = ratio / threshold
    label = binding.get("binding_label") or "debt line"
    is_mcap = bool(_MCAP_RE.search(label))
    times = ratio / 100.0

    if is_mcap and times >= 3.0:
        return (
            f"It owes {times:.1f} times what the whole company is worth — "
            f"the screen's limit is {threshold:.0f}%, and it isn't close.")
    if severity > 1:
        return (
            f"Its {label} sits at {binding['ratio']} — "
            f"past the {binding['threshold']} limit.")
    return _CLEAN_LINE


def is_shock(card):
    """True when `dramatize(card)` returned an over-limit (SHOCK) line rather
    than the neutral all-clear (CLEAN) `_CLEAN_LINE`. Reviewed defect: vo[0]
    used to unconditionally say "But here's the shock: {dramatize_line}",
    which for a CLEAN card produced the self-negating "here's the shock:
    every debt line lands under the limit." This is the signal callers (see
    `_hook_a`) use to pick a truthful connective instead."""
    return dramatize(card) != _CLEAN_LINE


class LintError(Exception):
    """Raised by `build_daily` when any emitted text fails the halal-copy rails."""

    def __init__(self, violations):
        self.violations = list(violations)
        super().__init__("; ".join(self.violations) or "lint violation")


# --- cliffhanger tease beat (verbatim, inserted before the stamp beat) -----

TEASE_BEAT = {
    "kind": "hook",
    "headline": "Three rulebooks have voted.",
    "sub": "The verdict is one tap away — but first, remember what it's based on.",
    "durationInFrames": 90,
}
TEASE_VO = (
    "Three rulebooks have voted. Before the stamp lands — every number you "
    "just saw is the reason."
)

ENDCARD_VO = (
    "Method shown. Dated. Corrected when it changes. Educational, not "
    "financial or religious advice."
)

# --- caption / kit hashtags -------------------------------------------------

HASHTAGS_CORE = "#halalinvesting #islamicfinance #halalstocks #muslimmoney"
_LAYER_HASHTAG = {
    "L0-energy": "#energystocks",
    "L1-chips": "#aistocks",
    "L2-infra": "#aistocks",
    "L3-models": "#aistocks",
    "L4-application": "#aistocks",
    "Q1-hardware": "#quantumstocks",
    "Q3-software": "#quantumstocks",
    "Q4-security": "#quantumstocks",
    "Q5-applications": "#quantumstocks",
}
_DEFAULT_HASHTAG = "#aistocks"

_FLIP_FROM_RE = re.compile(r"flipped\s+([a-z_]+)\s*->", re.IGNORECASE)


# --- shape detection ---------------------------------------------------------

def _worst_bar(bars):
    """Same selection as build_reel_props._worst_bar, kept local to avoid
    reaching into that module's private helpers."""
    numeric = [b for b in bars if isinstance(b.get("ratio"), (int, float))]
    if not numeric:
        return None
    return max(numeric, key=lambda b: (b["ratio"] or 0) - (b["threshold"] or 0))


def _shape_for(bars, overall):
    """flip is handled separately (it overrides Hook A only); this picks the
    template-bank key for Hook B (and, incidentally, documents the shape)."""
    statuses = {b.get("status") for b in bars} - {"unknown"}
    if "pass" in statuses and "fail" in statuses:
        return "split"
    if overall == "not_halal":
        return "fail"
    if overall == "halal":
        return "pass"
    return "review"  # questionable / insufficient_data


# --- Hook A (shocking-but-factual) + Hook B (contrarian) template banks ----

def _hook_a(ticker, worst, donut_pct, descriptor, dramatize_line, shock):
    """Headline stays the specific-number lead (unchanged style); vo0's
    connective is gated on `shock` (see `is_shock`) — reviewed defect: the
    connective used to unconditionally say "But here's the shock:", which
    for a CLEAN (under-every-limit) dramatize line was self-negating ("here's
    the shock: every debt line lands under the limit"). SHOCK cards keep the
    shock framing; CLEAN cards get a truthful non-shock connective instead —
    no fabricated drama, verdict still withheld. Caller guarantees `worst`/
    `donut_pct` aren't both None — see `build_daily`'s InsufficientDataError
    guard, checked BEFORE this is called so that guard fires before any
    card/dramatize work."""
    if worst is not None:
        r = round(worst["ratio"])
        headline = f"${r} of every $100 here is borrowed money."
    else:
        d = round(donut_pct)
        headline = f"${d} of every $100 in revenue here comes from a flagged activity."
    if shock:
        vo0 = f"{ticker} — {descriptor}. But here's the shock: {dramatize_line}"
    else:
        vo0 = (
            f"{ticker} — {descriptor}. And it clears the screen's debt "
            f"test — {dramatize_line}")
    return headline, vo0


# NOTE: no greeting here (owner call, task-9) — every variant opens with the
# plain-words company line (`_company_line`), prepended in `_hook_b` below.
# NOTE: no "{ticker}." repeated inside the template body either (task-3) —
# `_company_line` already names the ticker once; a second bare mention here
# was the "double-ticker seam" the task-3 brief calls out.
_HOOK_B = {
    "split": (
        "The screeners don't agree on this one.",
        "The three rulebooks don't agree on this "
        "one — some clear it, some don't. Let's see why.",
    ),
    "fail": (
        "Everyone assumes this one clears the screen.",
        "Everyone assumes this one clears the "
        "screen. We ran the numbers anyway.",
    ),
    "pass": (
        "This one looks too clean. We checked anyway.",
        "This one looks too clean to flag. We "
        "checked the numbers anyway.",
    ),
    "review": (
        "This one could go either way.",
        "This one could go either way. Here's "
        "what decides it.",
    ),
}


def _hook_b(ticker, shape, company_line):
    headline, vo_tpl = _HOOK_B[shape]
    return headline, f"{company_line} {vo_tpl.format(ticker=ticker)}"


# --- code-enforced pre-stamp verdict-leak gate ------------------------------

def _pre_stamp_leak_violations(props, variant_name):
    """Every beat/VO line before the `stamp` beat must not leak the verdict.

    Code-enforced (not just tested) so a future template edit to either hook
    bank, or `_rewrite_common`, trips this the moment it ships instead of
    waiting for someone to notice a specific ticker's fail-shape copy reads
    "...passes the screen."
    """
    kinds = [b["kind"] for b in props["beats"]]
    try:
        stamp_i = kinds.index("stamp")
    except ValueError:
        stamp_i = len(kinds)
    errs = []
    for i, line in enumerate(props["vo"][:stamp_i]):
        low = str(line).lower()
        for bad in _LEAK_SUBSTRINGS:
            if bad in low:
                errs.append(
                    f"{variant_name}: vo[{i}] leaks verdict word {bad!r} "
                    f"before the stamp beat: {line!r}")
    return errs


# --- flip override (Hook A only; the stamp basis note is shared) -----------

def _apply_flip_basis(props, story):
    m = _FLIP_FROM_RE.search(str(story.get("headline_fact") or ""))
    frm = story.get("from") or (m.group(1).replace("_", " ") if m else "a different verdict")
    prev_date = story.get("prev_date") or "the prior screen"
    stamp_beat = next(b for b in props["beats"] if b["kind"] == "stamp")
    suffix = f"was {frm} on {prev_date}"
    stamp_beat["basis"] = f"{stamp_beat['basis']} · {suffix}" if stamp_beat.get("basis") else suffix


def _apply_flip_hook(props_a):
    props_a["beats"][0]["headline"] = "This verdict just changed."
    props_a["vo"][0] = f"This verdict just changed. {props_a['vo'][0]}"


# --- common (shared-by-both-variants) transform -----------------------------

def _rewrite_common(props, date_str, worst, donut_pct, company_line, dramatize_line):
    """tickerSub, cliffhanger insertion, endcard trust-close, visceral VO
    rewrite. Mutates `props` in place — caller deep-copies first."""
    props["tickerSub"] = f"THE DAILY SCREEN · {date_str}"

    beats, vo = props["beats"], props["vo"]

    # Owner call (task-9): the hook beat's on-screen "sub" becomes the plain-
    # words company line, so viewers READ who the company is while hearing
    # it — replaces build_reel_props's generic _HOOK_SUB. Task-3: a second
    # sentence carries the shock stat onto the hero, since the hero photo is
    # full-bleed behind exactly this beat.
    beats[0]["sub"] = f"{company_line} {dramatize_line}"

    stamp_i = next(i for i, b in enumerate(beats) if b["kind"] == "stamp")
    beats.insert(stamp_i, copy.deepcopy(TEASE_BEAT))
    vo.insert(stamp_i, TEASE_VO)

    for i, b in enumerate(beats):
        if b["kind"] == "bars" and worst is not None:
            r = f"{worst['ratio']:.1f}"
            t = f"{worst['threshold']:.1f}"
            vo[i] = f"{r} percent — that's ${r} of every $100 — against a ${t} limit."
        elif b["kind"] == "donut" and donut_pct is not None:
            vo[i] = (
                f"{donut_pct} percent — that's ${donut_pct} of every $100 in "
                f"revenue — tied to a flagged activity."
            )
        elif b["kind"] == "endcard":
            b["sub"] = f"THE DAILY SCREEN · data as of {date_str}"
            vo[i] = ENDCARD_VO


# --- caption + carousel kit fields ------------------------------------------

def _key_number_sentence(worst, donut_pct):
    if worst is not None:
        r = f"{worst['ratio']:.1f}"
        t = f"{worst['threshold']:.1f}"
        return f"${r} of every $100 here sits in interest-bearing debt, against a ${t} limit the screen allows."
    d = f"{donut_pct}"
    return f"${d} of every $100 in revenue here traces back to a flagged activity."


def _build_caption(ticker, layer, worst, donut_pct, date_str):
    hook = f"{ticker}, halal or not? We ran the {date_str} screen to find out."
    body1 = _key_number_sentence(worst, donut_pct)
    body2 = "Three independent rulebooks each ran the same numbers — the reel breaks down where they agree and where they don't."
    cta = f"Send this to the friend who keeps asking about {ticker}."
    footer = (
        "Educational, not financial or religious advice — not a fatwa, "
        f"not a stock tip.\n{DISCLAIMER}"
    )
    topical = _LAYER_HASHTAG.get(layer, _DEFAULT_HASHTAG)
    hashtags = f"{HASHTAGS_CORE} {topical}"
    return f"{hook}\n\n{body1} {body2}\n\n{cta}\n\n{footer}\n\n{hashtags}"


def _build_kit_fields(ticker, worst, donut_pct, props_a, descriptor):
    screen_head = f"{ticker}: the halal screen, plain-English."
    screen_body = _key_number_sentence(worst, donut_pct)
    screen_body2 = (
        "Three independent rulebooks each ran the same numbers — the video "
        "shows where they agree and where they don't, before the verdict."
    )
    halal_script = " ".join(props_a["vo"])
    return {
        "screen_head": screen_head,
        "screen_body": screen_body,
        "screen_body2": screen_body2,
        "halal_script": halal_script,
        # task-3: the plain-words company descriptor, for the carousel's
        # dedicated company-definition slide (task-4 consumes this).
        "company_def": descriptor,
    }


def _editorial_check_lines(props_a, props_b, caption, dramatize_line):
    """Every line `lint_editorial` (the task-3 banned-judgment-word gate)
    should see: both variants' full VO, the caption, every on-screen `sub`
    (where the dramatize shock line actually lands, per `_rewrite_common`),
    and the raw dramatize line itself (belt-and-suspenders — already covered
    via `sub`/`vo[0]`, but checked directly too)."""
    lines = list(props_a["vo"]) + list(props_b["vo"]) + [caption, dramatize_line]
    for props in (props_a, props_b):
        for b in props["beats"]:
            sub = b.get("sub")
            if isinstance(sub, str):
                lines.append(sub)
    return lines


# --- entry point --------------------------------------------------------------

def build_daily(ticker, halal_bundle, story, date_str):
    """Pure. Raises `InsufficientDataError` (from build_props) or `LintError`
    (this module's own rails gate) rather than emit unvetted copy."""
    props = build_reel_props.build_props(ticker, halal_bundle, story=story)

    verdicts = (halal_bundle or {}).get("verdicts", {}) or {}
    v = verdicts.get(ticker) or {}
    overall = v.get("overall")
    layer = v.get("layer")

    bars_beat = next((b for b in props["beats"] if b["kind"] == "bars"), None)
    donut_beat = next((b for b in props["beats"] if b["kind"] == "donut"), None)
    bars = bars_beat["bars"] if bars_beat else []
    donut_pct = donut_beat["pct"] if donut_beat else None
    worst = _worst_bar(bars)
    shape = _shape_for(bars, overall)

    # Checked BEFORE any card/dramatize work (and before the raise moved out
    # of `_hook_a`) so a verdict with no numeric bar AND no donut split still
    # aborts cleanly rather than reaching `screen_card_data`/`dramatize` with
    # a shape those two don't guarantee they can handle.
    if worst is None and donut_pct is None:
        raise InsufficientDataError(
            f"{ticker}: no numeric bar ratio and no donut percentage — "
            "hook A has no specific number to lead with")

    card = screen_card_data(verdicts, ticker)
    dramatize_line = dramatize(card)
    shock = is_shock(card)

    descriptor = _company_descriptor(ticker, v)
    company_line = _company_line(ticker, descriptor)

    base = copy.deepcopy(props)
    _rewrite_common(base, date_str, worst, donut_pct, company_line, dramatize_line)

    is_flip = bool(story and story.get("kind") == "flip")
    if is_flip:
        _apply_flip_basis(base, story)

    props_a = copy.deepcopy(base)
    props_b = copy.deepcopy(base)

    a_headline, a_vo0 = _hook_a(
        ticker, worst, donut_pct, descriptor, dramatize_line, shock)
    props_a["beats"][0]["headline"] = a_headline
    props_a["vo"][0] = a_vo0
    if is_flip:
        _apply_flip_hook(props_a)

    b_headline, b_vo0 = _hook_b(ticker, shape, company_line)
    props_b["beats"][0]["headline"] = b_headline
    props_b["vo"][0] = b_vo0

    # task-3: sector-theme hero, same for both variants (keyed off the
    # verdict's layer; unknown/missing layer -> heroes/_default.jpg).
    hero_src = heroes.hero_for_layer(v.get("layer"))
    props_a["heroSrc"] = hero_src
    props_b["heroSrc"] = hero_src

    caption = _build_caption(ticker, layer, worst, donut_pct, date_str)
    kit_fields = _build_kit_fields(ticker, worst, donut_pct, props_a, descriptor)

    violations = []
    violations += _pre_stamp_leak_violations(props_a, "props_a")
    violations += _pre_stamp_leak_violations(props_b, "props_b")
    violations += lint_halal_script(" ".join(props_a["vo"]), card)
    violations += lint_halal_script(" ".join(props_b["vo"]), card)
    violations += lint_halal_script(caption, card)
    violations += lint_visceral(props_a["vo"])
    violations += lint_visceral(props_b["vo"])
    violations += lint_editorial(_editorial_check_lines(props_a, props_b, caption, dramatize_line))
    if violations:
        raise LintError(violations)

    return {
        "props_a": props_a,
        "props_b": props_b,
        "caption": caption,
        "kit_fields": kit_fields,
    }
