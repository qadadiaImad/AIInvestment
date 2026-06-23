from index import build_index


def test_groups_reel_with_its_slides_and_assigns_post_id():
    higgs = [
        "reel_nvda_2026-06-22.mp4",
        "reel_nvda_data.png", "reel_nvda_hook.png", "reel_nvda_takeaway.png",
        "v4_crm_1_hook.png", "v4_crm_2_data.png",
        "reels_2026-06-22.txt", "posts_2026-06-21.txt",
        "hero_nvda_2026-06-22.png", "logo_NVDA.png", "voice_nvda_2026-06-22.mp3",
        "_check_anim.png", "reels_manifest.json",  # all excluded
    ]
    content = ["carousel_2026-06-03/CRM/slide_1.html", "carousel_2026-06-03/CRM/brief.md"]
    posts = build_index(higgs, content)

    nvda = next(p for p in posts if p["ticker"] == "NVDA" and p["kind"] == "reel")
    assert nvda["post_id"] == "2026-06-22_NVDA_reel"
    assert nvda["date"] == "2026-06-22"
    assert any(m.endswith("reel_nvda_2026-06-22.mp4") for m in nvda["media"])
    assert any("reel_nvda_data.png" in m for m in nvda["media"])
    assert all(m.startswith("/media/") for m in nvda["media"])
    # scratch excluded
    assert not any(("hero_" in m or "logo_" in m or "voice_" in m or "_check" in m)
                   for m in nvda["media"])

    # v4 image carousel becomes a carousel post for CRM
    assert any(p["ticker"] == "CRM" and p["kind"] == "carousel" for p in posts)
    # content HTML carousel becomes a carousel post for CRM (2026-06-03)
    assert any(p["post_id"] == "2026-06-03_CRM_carousel" for p in posts)


def test_sorted_newest_date_first():
    posts = build_index(["reel_ionq_2026-06-21.mp4", "reel_nvda_2026-06-22.mp4"], [])
    assert posts[0]["date"] >= posts[-1]["date"]


def test_post_id_shape():
    posts = build_index(["reel_adbe_2026-06-22.mp4"], [])
    assert posts[0]["post_id"] == "2026-06-22_ADBE_reel"


def test_congress_alias_attaches_cong_slides_and_no_junk_post():
    # regression: the congress reel is reel_congress_*.mp4 but its slides are reel_cong_*/v4_cong_*.
    # The CONG->CONGRESS alias must attach them to the reel; no 0000-00-00 junk post may appear.
    posts = build_index(
        ["reel_congress_2026-06-22.mp4", "reel_cong_hook.png",
         "v4_cong_1_hook.png", "v4_cong_2_card.png"], [])
    ids = [p["post_id"] for p in posts]
    assert "2026-06-22_CONGRESS_reel" in ids
    assert not any(p["date"] == "0000-00-00" for p in posts)
    congress = next(p for p in posts if p["post_id"] == "2026-06-22_CONGRESS_reel")
    assert any("reel_cong_hook.png" in m for m in congress["media"])
    assert any("v4_cong_1_hook.png" in m for m in congress["media"])


def test_orphan_png_with_no_bundle_is_dropped_not_fabricated():
    # a v4 PNG whose ticker has no reel/carousel bundle is dropped (no synthetic 0000-00-00 post)
    posts = build_index(["v4_zzz_1_hook.png"], [])
    assert posts == []
