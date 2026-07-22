# SPDX-License-Identifier: Apache-2.0
"""The shipped fixtures and catalogs stay valid, consistent, and publishable.

These fixtures ship in a public Apache-2.0 repo. The tests below are as much a
safety check as a correctness one: they assert the fixtures remain synthetic and
free of anything that should not have left a private repo.
"""

import json
from pathlib import Path

import pytest

from instar.core.catalog import FeatureCatalog
from instar.core.traffic import TrafficSample, load_traffic

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "Engineering" / "fixtures"
CATALOGS = FIXTURES / "catalogs"

FIXTURE_FILES = sorted(FIXTURES.glob("*.jsonl"))
TRIAGE_LABELS = {
    "billing",
    "bug_report",
    "feature_request",
    "how_to",
    "account_access",
    "cancellation",
}

# Terms that would mean private context leaked into a public fixture.
FORBIDDEN_TERMS = (
    "purple blossom",
    "blossom grove",
    "blossom",
    "planware",
    "signetware",
    "listenware",
    "growthscout",
    "daily_bloom",
    "keystone",
    "db-server",
    "tenant_id",
    "user_id",
)


def test_fixtures_are_present() -> None:
    assert len(FIXTURE_FILES) >= 4


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_fixture_loads(path: Path) -> None:
    assert load_traffic(path)


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_sample_ids_are_unique(path: Path) -> None:
    samples = load_traffic(path)
    ids = [s.id for s in samples]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_every_sample_is_marked_synthetic(path: Path) -> None:
    assert all(s.meta.get("synthetic") is True for s in load_traffic(path))


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_every_sample_has_usable_content(path: Path) -> None:
    for s in load_traffic(path):
        assert s.messages, f"{s.id} has no messages"
        assert any(m.get("content") for m in s.messages), f"{s.id} has empty content"
        assert s.max_tokens > 0


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_no_private_context_leaked(path: Path) -> None:
    """The IP boundary, enforced in CI rather than in a reviewer's memory."""
    text = path.read_text(encoding="utf-8").lower()
    found = [term for term in FORBIDDEN_TERMS if term in text]
    assert not found, f"{path.name} contains private terms: {found}"


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_no_email_addresses(path: Path) -> None:
    assert "@" not in path.read_text(encoding="utf-8")


@pytest.mark.parametrize("path", FIXTURE_FILES, ids=lambda p: p.name)
def test_prompt_lengths_vary(path: Path) -> None:
    """Token estimates come from character count, so uniform fixtures would make
    every cost curve flat and meaningless."""
    lengths = {len(json.dumps(s.messages)) for s in load_traffic(path)}
    assert len(lengths) > 1


# ── the classification workload ─────────────────────────────────────────


def test_triage_fixture_labels_every_sample() -> None:
    samples = load_traffic(FIXTURES / "support-triage.jsonl")
    assert all(s.meta.get("gold") for s in samples)


def test_triage_labels_come_from_the_known_set() -> None:
    samples = load_traffic(FIXTURES / "support-triage.jsonl")
    assert {str(s.meta["gold"]) for s in samples} == TRIAGE_LABELS


def test_triage_is_scorable_without_an_llm_judge() -> None:
    """The reason a classification workload is the best first live test."""
    from instar.providers.base import CompletionResult
    from instar.rubrics.judges import LabelMatchJudge

    samples = load_traffic(FIXTURES / "support-triage.jsonl")
    judge = LabelMatchJudge(TRIAGE_LABELS)
    for s in samples:
        gold = str(s.meta["gold"])
        good = CompletionResult(gold, "m", 1, 1, 0.0)
        assert judge.score(s, good, good).score == 1.0


# ── the caching workload ────────────────────────────────────────────────


def _caching_samples() -> list[TrafficSample]:
    return [
        s
        for s in load_traffic(FIXTURES / "sales-pipeline.jsonl")
        if s.meta.get("static_prefix_tokens")
    ]


def test_the_caching_series_exists() -> None:
    assert len(_caching_samples()) >= 2


def test_the_caching_series_starts_cold_then_runs_warm() -> None:
    """A cache series whose first call is already warm would model nothing."""
    series = _caching_samples()
    assert series[0].meta["warm"] is False
    assert all(s.meta["warm"] is True for s in series[1:])


def test_declared_prefix_size_matches_the_actual_prefix() -> None:
    """A declared prefix that does not match the real system prompt would make
    any caching-saving figure derived from it fiction."""
    from instar.providers.base import estimate_tokens

    for s in _caching_samples():
        declared = int(s.meta["static_prefix_tokens"])
        actual = estimate_tokens(s.system or "")
        assert actual == pytest.approx(declared, rel=0.25), (
            f"{s.id}: declares {declared} prefix tokens but its system prompt is ~{actual}"
        )


# ── catalogs ────────────────────────────────────────────────────────────


def test_example_catalog_covers_every_shipped_feature() -> None:
    catalog = FeatureCatalog.from_json(CATALOGS / "example-departments.json")
    features = {s.feature for path in FIXTURE_FILES for s in load_traffic(path)}
    assert catalog.unknown_features(features) == []


def test_the_all_foreground_catalog_classifies_nothing() -> None:
    catalog = FeatureCatalog.from_json(CATALOGS / "all-foreground.json")
    assert catalog.categories == {}


def test_the_example_catalog_has_both_categories() -> None:
    """A catalog that is all one category cannot demonstrate routing."""
    catalog = FeatureCatalog.from_json(CATALOGS / "example-departments.json")
    assert len(set(catalog.categories.values())) == 2
