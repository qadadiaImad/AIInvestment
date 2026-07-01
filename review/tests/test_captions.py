from captions import parse_captions

SAMPLE = """AI STACK — NARRATED REEL KIT (2026-06-22)
=============== REEL 1 — NVDA (AI CHIPS) ===============
File: reel_nvda_2026-06-22.mp4
Caption:
Every AI chip stock looks expensive except the biggest one.
Hashtags: #nvidia #nvda
=============== REEL 2 — IONQ (QUANTUM) ===============
Caption:
Quantum gets traded like one bet.
Hashtags: #ionq"""


def test_returns_caption_text_per_ticker():
    c = parse_captions(SAMPLE)
    assert "biggest one" in c["NVDA"]
    assert "#nvidia" in c["NVDA"]
    assert "one bet" in c["IONQ"]


def test_empty_input_returns_empty_dict():
    assert parse_captions("") == {}
    assert parse_captions("   \n  ") == {}


def test_long_ticker_like_congress_is_not_dropped():
    # regression: a >6-char ticker (CONGRESS) must still be parsed
    txt = ("=============== REEL 4 — CONGRESS (VAN EPPS) ===============\n"
           "Caption:\nThey oversee it, then trade it.\nHashtags: #congress")
    c = parse_captions(txt)
    assert "CONGRESS" in c
    assert "trade it" in c["CONGRESS"]
