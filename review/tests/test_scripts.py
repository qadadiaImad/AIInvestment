from scripts import list_scripts


def test_classifies_three_kinds_and_excludes_others():
    files = ["reels_2026-06-23.txt", "reels_2026-06-23_kit.md", "posts_2026-06-03.txt",
             "reels_manifest.json", "make_reel.py", "hero_nvda.png", "reel_nvda_2026-06-22.mp4"]
    out = list_scripts(files)
    kinds = {e["name"]: e["kind"] for e in out}
    assert kinds["reels_2026-06-23.txt"] == "reel-script"
    assert kinds["reels_2026-06-23_kit.md"] == "kit"
    assert kinds["posts_2026-06-03.txt"] == "post-script"
    names = [e["name"] for e in out]
    for excluded in ("reels_manifest.json", "make_reel.py", "hero_nvda.png", "reel_nvda_2026-06-22.mp4"):
        assert excluded not in names
    e = next(e for e in out if e["name"] == "reels_2026-06-23.txt")
    assert e["date"] == "2026-06-23"
    assert e["media"] == "/media/higgs/reels_2026-06-23.txt"


def test_sorted_newest_date_first_then_kind():
    files = ["posts_2026-06-03.txt", "reels_2026-06-23.txt", "reels_2026-06-23_kit.md"]
    out = list_scripts(files)
    assert out[0]["date"] == "2026-06-23"
    assert out[-1]["date"] == "2026-06-03"
    d23 = [e["kind"] for e in out if e["date"] == "2026-06-23"]
    assert d23.index("kit") < d23.index("reel-script")


def test_empty_input():
    assert list_scripts([]) == []
