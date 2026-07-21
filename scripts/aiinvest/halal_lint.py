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
    """Digit strings + spelled-digit fragments a script may legitimately contain."""
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
        forms.add(" ".join(_WORDS[d] for d in head if d in _WORDS))
        if head in ("13",): forms.add("thirteen")
        if head in ("30",): forms.add("thirty")
        if head in ("38",): forms.add("thirty-eight")
        if head in ("21",): forms.add("twenty-one")
        if head in ("9",): forms.add("nine")
    return {f for f in forms if f}


def lint_halal_script(script, card):
    errs = []
    low = script.lower()
    if re.search(r"\bis\s+(fully\s+)?halal\b", low):
        errs.append('forbidden claim: "is halal" — say "passes the AAOIFI screen"')
    if re.search(r"\bis\s+haram\b", low):
        errs.append('forbidden claim: "is haram" — say "fails the screen" / "the screen flags it"')
    if DISCLAIMER not in low:
        errs.append(f'missing spoken disclaimer line: "{DISCLAIMER}"')
    if not any(f in low for f in _spoken_forms(card)):
        errs.append("no number in the script matches the joined screen data — scripts must cite real figures")
    return errs
