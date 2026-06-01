"""RED tests for the news-processing core (Playwright fetches; this layer processes)."""
from aiinvest import news


# --- classify_certainty(): Rule #5 — label filed / reported / rumored ---

def test_filing_language_is_filed():
    assert news.classify_certainty("OpenAI filed its S-1 with the SEC today") == "filed"


def test_rumor_language_is_rumored():
    assert news.classify_certainty(
        "Anthropic is reportedly in talks to raise at a $350B valuation") == "rumored"


def test_announcement_language_is_reported():
    assert news.classify_certainty("Nvidia announced record Q1 datacenter revenue") == "reported"


def test_plain_text_defaults_to_reported():
    assert news.classify_certainty("The market moved today.") == "reported"


# --- tag_entities(): which stack names does the article mention? ---

INDEX = {"nvidia": "NVDA", "nvda": "NVDA", "openai": "OpenAI", "anthropic": "Anthropic"}


def test_tag_entities_matches_names_case_insensitively():
    tags = news.tag_entities("NVIDIA expands its deal with OpenAI", INDEX)
    assert tags == ["NVDA", "OpenAI"]


def test_tag_entities_uses_word_boundaries():
    # "amd" must not match inside "lambda"; ensure no false positive here either.
    tags = news.tag_entities("Lambda raised a round", {"amd": "AMD"})
    assert tags == []


def test_tag_entities_dedupes_repeats():
    tags = news.tag_entities("Nvidia, Nvidia, NVDA again", INDEX)
    assert tags == ["NVDA"]


# --- normalize_article(): stamped record with tags + certainty ---

RAW = {
    "title": "Anthropic reportedly weighing an IPO",
    "url": "https://example.com/a",
    "source": "example.com",
    "published": "2026-05-29",
    "summary": "Sources say Anthropic could file later this year.",
}


def test_normalize_article_stamps_and_enriches():
    art = news.normalize_article(RAW, "2026-05-30T14:00:00Z", INDEX)
    assert art["tickers"] == ["Anthropic"]
    assert art["certainty"] == "rumored"
    assert art["retrieved_at"] == "2026-05-30T14:00:00Z"
    assert art["source_class"] == "news-html"
    assert art["url"] == "https://example.com/a"


# --- dedupe(): same URL appears once ---

def test_dedupe_keeps_first_per_url():
    arts = [{"url": "u1", "title": "a"}, {"url": "u1", "title": "b"}, {"url": "u2", "title": "c"}]
    out = news.dedupe(arts)
    assert [a["url"] for a in out] == ["u1", "u2"]


# --- bare_symbol(): strip exchange prefix, uppercase ---

def test_bare_symbol_strips_exchange_prefix():
    assert news.bare_symbol("NYSE:VST") == "VST"
    assert news.bare_symbol("nasdaq:ceg") == "CEG"


def test_bare_symbol_plain_ticker_uppercased():
    assert news.bare_symbol("nvda") == "NVDA"


def test_bare_symbol_tolerates_none_and_whitespace():
    assert news.bare_symbol(None) == ""
    assert news.bare_symbol("  msft  ") == "MSFT"


# --- parse_finnhub(): epoch datetime -> ISO UTC, project fields ---

def test_parse_finnhub_converts_epoch_to_iso_utc():
    items = [{
        "category": "company",
        "datetime": 1748736000,  # 2025-06-01T00:00:00Z
        "headline": "Nvidia announced a new chip",
        "id": 1,
        "related": "NVDA",
        "source": "Reuters",
        "summary": "Details here.",
        "url": "https://example.com/n1",
    }]
    out = news.parse_finnhub(items)
    assert len(out) == 1
    raw = out[0]
    assert raw["title"] == "Nvidia announced a new chip"
    assert raw["url"] == "https://example.com/n1"
    assert raw["source"] == "Reuters"
    assert raw["summary"] == "Details here."
    assert raw["published"] == "2025-06-01T00:00:00Z"


def test_parse_finnhub_tolerates_missing_or_bad_fields():
    out = news.parse_finnhub([{"headline": "no url no time"}])
    assert len(out) == 1
    assert out[0]["title"] == "no url no time"
    assert out[0]["url"] is None
    assert out[0]["published"] is None


def test_parse_finnhub_handles_non_list():
    assert news.parse_finnhub(None) == []
    assert news.parse_finnhub({}) == []


# --- parse_yahoo_rss(): stdlib xml.etree, tolerate missing fields ---

_YAHOO_XML = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel>
  <item>
    <title>OpenAI in talks to raise capital</title>
    <link>https://finance.yahoo.com/news/openai-1</link>
    <pubDate>Sun, 01 Jun 2025 12:30:00 GMT</pubDate>
    <description>Sources say a deal could come soon.</description>
  </item>
  <item>
    <title>Headline with no description or date</title>
    <link>https://finance.yahoo.com/news/x-2</link>
  </item>
</channel></rss>"""


def test_parse_yahoo_rss_extracts_items():
    out = news.parse_yahoo_rss(_YAHOO_XML)
    assert len(out) == 2
    first = out[0]
    assert first["title"] == "OpenAI in talks to raise capital"
    assert first["url"] == "https://finance.yahoo.com/news/openai-1"
    assert first["summary"] == "Sources say a deal could come soon."
    # RFC-822 pubDate normalized to ISO-8601 UTC
    assert first["published"] == "2025-06-01T12:30:00Z"
    assert first["source"] == "Yahoo Finance"


def test_parse_yahoo_rss_tolerates_missing_fields():
    out = news.parse_yahoo_rss(_YAHOO_XML)
    second = out[1]
    assert second["title"] == "Headline with no description or date"
    assert second["url"] == "https://finance.yahoo.com/news/x-2"
    assert second["summary"] is None
    assert second["published"] is None


def test_parse_yahoo_rss_handles_garbage():
    assert news.parse_yahoo_rss("") == []
    assert news.parse_yahoo_rss("not xml at all <<<") == []


# --- is_safe_alias(): suppress common-word / too-short tickers in free-text tagging ---

def test_is_safe_alias_rejects_common_word_tickers():
    for bad in ("AI", "ON", "SO", "NOW", "NET", "ARM", "APP", "ALL", "ARE",
                "TEAM", "FIG", "LEU"):
        assert news.is_safe_alias(bad) is False, bad


def test_is_safe_alias_rejects_one_and_two_char():
    for bad in ("S", "D", "F", "MU", "ET", "PH"):
        assert news.is_safe_alias(bad) is False, bad


def test_is_safe_alias_accepts_real_tickers_and_names():
    for ok in ("AMZN", "NVDA", "DELL", "openai", "anthropic", "c3.ai", "Arm Holdings"):
        assert news.is_safe_alias(ok) is True, ok


def test_tag_entities_does_not_tag_common_word_alias():
    # 'AI' (C3.ai) must NOT be tagged from the word "AI" in a headline.
    idx = news.build_name_index({lbl: [a for a in aliases if news.is_safe_alias(a)]
                                 for lbl, aliases in {"AI": ["AI"], "NVDA": ["NVDA"]}.items()})
    tags = news.tag_entities("NVDA's new AI chip ships", idx)
    assert "NVDA" in tags
    assert "AI" not in tags
