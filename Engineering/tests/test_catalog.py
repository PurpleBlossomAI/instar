# SPDX-License-Identifier: Apache-2.0
"""The feature catalog: resolution order, validation, and round-tripping."""

import json

import pytest

from instar.core.catalog import BACKGROUND, FOREGROUND, FeatureCatalog
from instar.core.traffic import TrafficSample


def _sample(feature: str = "a.b", category: str | None = None) -> TrafficSample:
    return TrafficSample(
        id="s1", feature=feature, messages=[{"role": "user", "content": "hi"}], category=category
    )


def test_maps_a_known_feature() -> None:
    cat = FeatureCatalog({"a.b": BACKGROUND})
    assert cat.category_for(_sample("a.b")) == BACKGROUND


def test_unknown_feature_falls_to_default_foreground() -> None:
    """Defaulting to foreground means a forgotten feature costs money, not quality."""
    cat = FeatureCatalog({"a.b": BACKGROUND})
    assert cat.category_for(_sample("never.catalogued")) == FOREGROUND


def test_sample_category_overrides_the_catalog() -> None:
    cat = FeatureCatalog({"a.b": BACKGROUND})
    assert cat.category_for(_sample("a.b", category=FOREGROUND)) == FOREGROUND


def test_custom_default_is_honored() -> None:
    cat = FeatureCatalog({}, default=BACKGROUND)
    assert cat.category_for(_sample("anything")) == BACKGROUND


def test_empty_catalog_classifies_nothing() -> None:
    cat = FeatureCatalog.empty()
    assert cat.categories == {}
    assert cat.category_for(_sample()) == FOREGROUND


def test_rejects_an_invalid_category_value() -> None:
    with pytest.raises(ValueError, match="urgent"):
        FeatureCatalog({"a.b": "urgent"})


def test_rejects_an_invalid_default() -> None:
    with pytest.raises(ValueError, match="default category"):
        FeatureCatalog({}, default="sideways")


def test_unknown_features_reports_the_uncatalogued(tmp_path: object) -> None:
    cat = FeatureCatalog({"a.b": BACKGROUND, "c.d": FOREGROUND})
    assert cat.unknown_features(["a.b", "x.y", "z.z"]) == ["x.y", "z.z"]
    assert cat.unknown_features(["a.b", "c.d"]) == []


def test_from_json_round_trips(tmp_path) -> None:
    path = tmp_path / "cat.json"
    path.write_text(
        json.dumps({"default": FOREGROUND, "categories": {"a.b": BACKGROUND}}), encoding="utf-8"
    )
    cat = FeatureCatalog.from_json(path)
    assert cat.default == FOREGROUND
    assert cat.categories == {"a.b": BACKGROUND}
    assert cat.to_json() == {"default": FOREGROUND, "categories": {"a.b": BACKGROUND}}


def test_from_json_rejects_a_non_object(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("[1, 2, 3]", encoding="utf-8")
    with pytest.raises(ValueError, match="must be a JSON object"):
        FeatureCatalog.from_json(path)


def test_from_json_rejects_a_bad_category(tmp_path) -> None:
    path = tmp_path / "bad.json"
    path.write_text(json.dumps({"categories": {"a.b": "nope"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="nope"):
        FeatureCatalog.from_json(path)
