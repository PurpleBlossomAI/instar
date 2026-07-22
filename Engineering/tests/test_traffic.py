# SPDX-License-Identifier: Apache-2.0
"""The captured-traffic format: parsing, round-tripping, and loud failures."""

import json

import pytest

from instar.core.catalog import BACKGROUND
from instar.core.traffic import TrafficSample, load_traffic, save_traffic

MINIMAL = {"id": "s1", "feature": "a.b", "messages": [{"role": "user", "content": "hello"}]}


def test_from_json_applies_defaults() -> None:
    s = TrafficSample.from_json(dict(MINIMAL))
    assert s.max_tokens == 1024
    assert s.system is None
    assert s.temperature is None
    assert s.category is None
    assert s.meta == {}


def test_round_trips_through_jsonl(tmp_path) -> None:
    original = [
        TrafficSample(
            id="s1",
            feature="a.b",
            messages=[{"role": "user", "content": "hello"}],
            max_tokens=64,
            system="be terse",
            temperature=0.0,
            category=BACKGROUND,
            meta={"synthetic": True, "gold": "billing"},
        )
    ]
    path = tmp_path / "t.jsonl"
    save_traffic(path, original)
    assert load_traffic(path) == original


def test_blank_lines_are_ignored(tmp_path) -> None:
    path = tmp_path / "t.jsonl"
    path.write_text(f"{json.dumps(MINIMAL)}\n\n\n", encoding="utf-8")
    assert len(load_traffic(path)) == 1


def test_an_empty_fixture_is_an_error(tmp_path) -> None:
    path = tmp_path / "empty.jsonl"
    path.write_text("\n\n", encoding="utf-8")
    with pytest.raises(ValueError, match="no samples"):
        load_traffic(path)


def test_a_bad_line_names_its_line_number(tmp_path) -> None:
    """A 400-line fixture with one typo should say which line, not just fail."""
    path = tmp_path / "t.jsonl"
    path.write_text(f"{json.dumps(MINIMAL)}\nnot json\n", encoding="utf-8")
    with pytest.raises(ValueError, match=r":2:"):
        load_traffic(path)


def test_a_missing_required_field_names_its_line_number(tmp_path) -> None:
    path = tmp_path / "t.jsonl"
    path.write_text(json.dumps({"feature": "a.b", "messages": []}), encoding="utf-8")
    with pytest.raises(ValueError, match=r":1:"):
        load_traffic(path)


def test_rejects_an_invalid_category() -> None:
    with pytest.raises(ValueError, match="category"):
        TrafficSample(id="s1", feature="a.b", messages=[], category="urgent")
