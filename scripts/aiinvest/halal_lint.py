"""Rails linter for Karim halal VO scripts. Code-enforced, not convention.

Blocks: 'is halal'/'is haram' verdict claims; missing spoken disclaimer; scripts whose
numbers have no anchor in the joined screen-card data (no invented figures).
"""
from __future__ import annotations

import re

DISCLAIMER = "educational, not financial or religious advice"
_WORDS = {
    "0": "zero", "1": "one", "2": "two", "3": "three", "4": "four", "5": "five",
    "6": "six", "7": "seven", "8": "eight", "9": "nine",
}


def _spoken_forms(card):
    """Digit strings + spelled-digit fragments a script may legitimately contain.

    Spelled-word forms are only generated for number heads with >=2 digits
    ("thirty", "thirty-eight", "twenty-one", "thirteen"). Single-digit heads
    (e.g. "9", "0") are common English words on their own ("nine", "zero")
    and would let unrelated prose falsely anchor the number check, so no
    spelled form is added for them — only their raw digit string.
    """
    nums = set()
    for row in card.get("standards_rows", []):
        for k in ("ratio", "threshold", "margin"):
            m = re.search(r"([\d.]+)", row.get(k, ""))
            if m:
                nums.add(m.group(1))
    for line in (card.get("business_line", ""), card.get("purification_line", "")):
        nums.update(re.findall(r"([\d.]+)", line))
    forms = set()
    for n in nums:
        forms.add(n)
        head = n.split(".")[0]
        if len(head) >= 2:
            forms.add(" ".join(_WORDS[d] for d in head if d in _WORDS))
            if head in ("13",): forms.add("thirteen")
            if head in ("30",): forms.add("thirty")
            if head in ("38",): forms.add("thirty-eight")
            if head in ("21",): forms.add("twenty-one")
    return {f for f in forms if f}


_NUMERIC_FORM = re.compile(r"^[\d.]+$")
_VERDICT_CLAIM = re.compile(
    r"(?:\b(?:is|are|was|were|isn't|aren't|wasn't|weren't|ain't)|'s)"
    r"\s+(?:\w+[\s-]+){0,2}(?:halal|haram)\b")
_CURLY_APOSTROPHES = ("’", "ʼ")


def _form_anchors(form, low):
    """True if `form` is genuinely present in `low`.

    Raw numeric forms (pure digits/dots, e.g. "9.0") are matched with
    boundary guards so a longer figure like "19.05" can't satisfy a card
    figure of "9.0" via bare substring containment. Spelled-word forms keep
    the simple substring check.
    """
    if _NUMERIC_FORM.match(form):
        return re.search(r"(?<![\d.])" + re.escape(form) + r"(?![\d.])", low) is not None
    return form in low


def lint_halal_script(script, card):
    errs = []
    low = script.lower()
    for apo in _CURLY_APOSTROPHES:
        low = low.replace(apo, "'")
    m = _VERDICT_CLAIM.search(low)
    if m:
        hit = m.group(0)
        has_halal = "halal" in hit
        has_haram = "haram" in hit
        if has_halal and not has_haram:
            errs.append('forbidden claim: "is halal" — say "passes the AAOIFI screen"')
        elif has_haram and not has_halal:
            errs.append('forbidden claim: "is haram" — say "fails the screen" / "the screen flags it"')
        else:
            errs.append(
                'forbidden verdict claim ("halal"/"haram") — say "passes the AAOIFI screen" '
                'or "fails the screen" instead')
    if DISCLAIMER not in low:
        errs.append(f'missing spoken disclaimer line: "{DISCLAIMER}"')
    if not any(_form_anchors(f, low) for f in _spoken_forms(card)):
        errs.append("no number in the script matches the joined screen data — scripts must cite real figures")
    return errs


_PCT_RE = re.compile(r"\d+(?:\.\d+)?\s*(?:%|percent|per\s?cent)", re.IGNORECASE)
_ANCHOR_RE = re.compile(
    r"\$|\bcents\b|\bof every\b|\bfor every\b|\blimit(?:s)?\b|\bcap(?:s)?\b"
    r"|\bthreshold(?:s)?\b|\ballowed\b", re.IGNORECASE)


def lint_visceral(lines):
    """Rails for spoken ratios: every percentage needs a plain-money analogy
    ("$X of every $100") or an explicit limit comparison (cap/threshold/allowed),
    never a bare percent left to float unanchored."""
    errs = []
    for line in lines:
        if _PCT_RE.search(line) and not _ANCHOR_RE.search(line):
            errs.append(f"bare ratio with no money analogy or limit comparison: {line!r}")
    return errs


# Fixed exact-match words (no stemming — stemming these would over-ban
# legitimate finance vocabulary, e.g. "risk"/"avoidance" must stay clean).
_EDITORIAL_WORDS = (
    "trap", "too much", "overvalued", "avoid", "risky", "terrible",
    "guaranteed",
)
# Bounded inflection stems for words whose common tenses/forms were slipping
# past the exact-match list (soared/soaring, crashed/crashing, plummeted/
# plummeting, dangerous/dangerously) — reviewed defect. Each stem is still
# word-bounded on both ends via the shared \b(?:...)\b wrapper below, so
# "risk" (not stemmed here) and "avoidance" (not stemmed here) stay clean.
_EDITORIAL_STEMS = (
    r"danger(?:ous|ously)?",
    r"plummet(?:s|ed|ing)?",
    r"soar(?:s|ed|ing)?",
    r"crash(?:es|ed|ing)?",
)
_EDITORIAL_RE = re.compile(
    r"\b(?:"
    + "|".join(w.replace(" ", r"\s+") for w in _EDITORIAL_WORDS)
    + "|" + "|".join(_EDITORIAL_STEMS)
    + r")\b",
    re.IGNORECASE)


def lint_editorial(lines):
    """Rails for factual-extreme copy (the Daily Screen v2 dramatize/hook lines):
    bans buy/sell-adjacent judgment words so a shocking-but-factual number never
    drifts into advice. Word-bounded, case-insensitive; one violation per line
    that contains any banned word (a line with two banned words still only
    reports once)."""
    errs = []
    for line in lines:
        m = _EDITORIAL_RE.search(str(line))
        if m:
            errs.append(
                f"banned editorial/judgment word {m.group(0)!r} — factual-extreme "
                f"tone only, no buy/sell framing: {line!r}")
    return errs


def lint_concept_script(script):
    """Rails for ticker-less concept/explainer scripts: verdict-claim phrasing +
    spoken disclaimer only (no per-ticker number anchor to check)."""
    errs = []
    low = script.lower().replace("’", "'").replace("ʼ", "'")
    if _VERDICT_CLAIM.search(low):
        errs.append('forbidden verdict claim - use screen phrasing, never "is halal/haram"')
    if DISCLAIMER not in low:
        errs.append(f'missing spoken disclaimer line: "{DISCLAIMER}"')
    return errs
