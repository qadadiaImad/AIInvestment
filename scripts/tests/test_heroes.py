import pathlib

from aiinvest import heroes

REMOTION_PUBLIC = pathlib.Path(__file__).resolve().parents[2] / "remotion" / "public"

ALL_LAYERS = (
    "L0-energy",
    "L1-chips",
    "L2-infra",
    "L4-application",
    "Q1-hardware",
    "Q3-software",
    "Q5-applications",
    "Q4-security",
)


def test_layer_heroes_covers_all_eight_live_layers():
    assert set(heroes.LAYER_HEROES) == set(ALL_LAYERS)


def test_hero_for_layer_known():
    assert heroes.hero_for_layer("Q4-security") == "heroes/Q4-security.jpg"


def test_hero_for_layer_unknown_falls_back_to_default():
    assert heroes.hero_for_layer("not-a-real-layer") == "heroes/_default.jpg"


def test_hero_for_layer_none_falls_back_to_default():
    assert heroes.hero_for_layer(None) == "heroes/_default.jpg"


def test_hero_for_layer_paths_are_static_file_relative():
    # no leading slash -- staticFile()-relative, not a URL path
    for layer in ALL_LAYERS:
        path = heroes.hero_for_layer(layer)
        assert not path.startswith("/")
        assert path.startswith("heroes/")


def test_every_layer_hero_file_exists_on_disk():
    for layer in ALL_LAYERS:
        rel = heroes.hero_for_layer(layer)
        assert (REMOTION_PUBLIC / rel).is_file(), f"missing hero file for {layer}: {rel}"


def test_default_hero_file_exists_on_disk():
    rel = heroes.hero_for_layer(None)
    assert (REMOTION_PUBLIC / rel).is_file()


def test_hero_abs_path_resolves_under_given_public_dir(tmp_path):
    result = heroes.hero_abs_path("Q4-security", tmp_path)
    assert result == tmp_path / "heroes" / "Q4-security.jpg"


def test_hero_abs_path_unknown_layer_resolves_default(tmp_path):
    result = heroes.hero_abs_path("nope", tmp_path)
    assert result == tmp_path / "heroes" / "_default.jpg"


def test_hero_abs_path_none_layer_resolves_default(tmp_path):
    result = heroes.hero_abs_path(None, tmp_path)
    assert result == tmp_path / "heroes" / "_default.jpg"
