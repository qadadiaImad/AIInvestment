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
