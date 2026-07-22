# SPDX-License-Identifier: Apache-2.0
"""Routing policies: the control, the rules baseline, and the classifier."""

import pytest

from instar.core.catalog import BACKGROUND, FOREGROUND, FeatureCatalog
from instar.core.traffic import TrafficSample
from instar.policies import (
    STRONG,
    WEAK,
    AllStrongPolicy,
    ClassifierPolicy,
    FeatureCategoryPolicy,
    build_policy,
    heuristic_difficulty,
)

CATALOG = FeatureCatalog({"bg.job": BACKGROUND, "fg.chat": FOREGROUND})


def _sample(feature: str, content: str = "hello", system: str | None = None) -> TrafficSample:
    return TrafficSample(
        id=f"s-{feature}",
        feature=feature,
        messages=[{"role": "user", "content": content}],
        system=system,
    )


def test_all_strong_routes_everything_strong() -> None:
    policy = AllStrongPolicy()
    assert policy.decide(_sample("bg.job")).target == STRONG
    assert policy.decide(_sample("fg.chat")).target == STRONG


def test_feature_category_splits_on_the_catalog() -> None:
    policy = FeatureCategoryPolicy(CATALOG)
    assert policy.decide(_sample("bg.job")).target == WEAK
    assert policy.decide(_sample("fg.chat")).target == STRONG


def test_feature_category_with_an_empty_catalog_matches_the_control() -> None:
    """An uncatalogued workload cannot be routed — a useful sanity signal."""
    policy = FeatureCategoryPolicy(FeatureCatalog.empty())
    assert policy.decide(_sample("bg.job")).target == STRONG


def test_decisions_carry_an_auditable_reason() -> None:
    decision = FeatureCategoryPolicy(CATALOG).decide(_sample("bg.job"))
    assert "background" in decision.reason


def test_heuristic_difficulty_stays_in_range() -> None:
    for content in ["", "x", "analyze the strategy " * 500]:
        assert 0.0 <= heuristic_difficulty(_sample("fg.chat", content)) <= 1.0


def test_longer_prompts_score_harder() -> None:
    short = heuristic_difficulty(_sample("bg.job", "hi"))
    long = heuristic_difficulty(_sample("bg.job", "word " * 400))
    assert long > short


def test_hard_cue_words_score_harder() -> None:
    plain = heuristic_difficulty(_sample("bg.job", "list the items"))
    cued = heuristic_difficulty(_sample("bg.job", "analyze the items"))
    assert cued > plain


def test_foreground_scores_harder_than_background() -> None:
    bg = heuristic_difficulty(_sample("bg.job", "same text"), CATALOG)
    fg = heuristic_difficulty(_sample("fg.chat", "same text"), CATALOG)
    assert fg > bg


def test_classifier_routes_easy_calls_weak() -> None:
    policy = ClassifierPolicy(threshold=0.9, catalog=CATALOG)
    assert policy.decide(_sample("bg.job", "hi")).target == WEAK


def test_classifier_keeps_hard_calls_strong() -> None:
    policy = ClassifierPolicy(threshold=0.05, catalog=CATALOG)
    assert policy.decide(_sample("fg.chat", "analyze " * 200)).target == STRONG


def test_a_higher_threshold_never_routes_less_weakly() -> None:
    """Monotonicity is what makes the sweep a curve rather than noise."""
    samples = [_sample("bg.job", "word " * i) for i in range(1, 40)]
    counts = []
    for t in [0.0, 0.25, 0.5, 0.75, 1.0]:
        policy = ClassifierPolicy(threshold=t, catalog=CATALOG)
        counts.append(sum(1 for s in samples if policy.decide(s).target == WEAK))
    assert counts == sorted(counts)


def test_classifier_accepts_a_custom_scorer() -> None:
    """The extension point: swap the heuristic for a trained router."""
    policy = ClassifierPolicy(threshold=0.5, scorer=lambda s: 0.0)
    assert policy.decide(_sample("fg.chat", "analyze " * 200)).target == WEAK


def test_decision_carries_the_score() -> None:
    decision = ClassifierPolicy(threshold=0.5, scorer=lambda s: 0.42).decide(_sample("fg.chat"))
    assert decision.score == pytest.approx(0.42)


@pytest.mark.parametrize("name", ["all_strong", "feature_category", "classifier"])
def test_build_policy_constructs_each_policy(name: str) -> None:
    assert build_policy(name, catalog=CATALOG).name == name


def test_build_policy_rejects_an_unknown_name() -> None:
    with pytest.raises(ValueError, match="unknown policy"):
        build_policy("magic")


def test_build_policy_works_without_a_catalog() -> None:
    assert build_policy("feature_category").decide(_sample("bg.job")).target == STRONG
