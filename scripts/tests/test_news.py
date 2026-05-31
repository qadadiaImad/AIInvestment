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
