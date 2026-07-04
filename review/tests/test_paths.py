import paths


def test_repo_root_is_parent_of_review():
    # paths.py lives in review/, so REPO_ROOT must contain a 'higgs' dir name in its tree anchor
    assert paths.HIGGS == paths.REPO_ROOT / "higgs"
    assert paths.CONTENT == paths.REPO_ROOT / "content"
    assert paths.FEEDBACK_FILE == paths.REPO_ROOT / "feedback" / "post_comments.json"
    # review/ is a direct child of REPO_ROOT
    assert (paths.REPO_ROOT / "review" / "paths.py").exists()
