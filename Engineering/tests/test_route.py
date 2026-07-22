# SPDX-License-Identifier: Apache-2.0
"""The routing runner: cost accounting, quality aggregation, and failure honesty."""

import pytest

from instar.core.catalog import BACKGROUND, FOREGROUND, FeatureCatalog
from instar.core.route import run_route, run_sweep
from instar.core.traffic import TrafficSample
from instar.policies import AllStrongPolicy, ClassifierPolicy, FeatureCategoryPolicy
from instar.policies.base import STRONG, WEAK, RoutingDecision, RoutingPolicy
from instar.providers.base import Backend, CompletionResult
from instar.providers.mock import MockBackend
from instar.rubrics.base import Judge, JudgeResult

CATALOG = FeatureCatalog({"bg.job": BACKGROUND, "fg.chat": FOREGROUND})
PRICING = {"strong-m": (10.0, 50.0), "weak-m": (1.0, 5.0)}

RUN_KWARGS = {"strong_model": "strong-m", "weak_model": "weak-m", "pricing": PRICING}


def _samples() -> list[TrafficSample]:
    return [
        TrafficSample(id=f"bg{i}", feature="bg.job", messages=[{"role": "user", "content": "x"}])
        for i in range(3)
    ] + [
        TrafficSample(id=f"fg{i}", feature="fg.chat", messages=[{"role": "user", "content": "y"}])
        for i in range(2)
    ]


class _FixedJudge(Judge):
    name = "fixed"

    def __init__(self, score: float = 0.8) -> None:
        self._score = score

    def score(
        self, sample: TrafficSample, strong: CompletionResult, weak: CompletionResult
    ) -> JudgeResult:
        return JudgeResult(self._score, "fixed")


class _BrokenBackend(Backend):
    name = "broken"

    def complete(self, sample: TrafficSample, model: str) -> CompletionResult:
        return CompletionResult.failure(model, "billing problem")


def _run(policy: RoutingPolicy, **overrides: object) -> object:
    kwargs = dict(
        policy=policy,
        strong_backend=MockBackend("strong"),
        weak_backend=MockBackend("weak"),
        judge=_FixedJudge(),
        **RUN_KWARGS,
    )
    kwargs.update(overrides)
    return run_route(_samples(), **kwargs)  # type: ignore[arg-type]


def test_control_saves_nothing_and_scores_perfectly() -> None:
    r = _run(AllStrongPolicy())
    assert r.weak_count == 0
    assert r.cost.saved_usd == pytest.approx(0.0)
    assert r.cost.routed_usd == pytest.approx(r.cost.baseline_usd)
    assert r.mean_quality_all == 1.0
    assert r.mean_quality_routed_weak is None


def test_routing_background_work_saves_money() -> None:
    r = _run(FeatureCategoryPolicy(CATALOG))
    assert r.weak_count == 3
    assert r.cost.routed_usd < r.cost.baseline_usd
    assert r.cost.saved_pct > 0


def test_calls_kept_strong_score_one_by_definition() -> None:
    r = _run(FeatureCategoryPolicy(CATALOG))
    strong_rows = [o for o in r.outcomes if o.target == STRONG]
    assert strong_rows
    assert all(o.quality == 1.0 for o in strong_rows)


def test_routed_weak_quality_reports_only_the_moved_calls() -> None:
    """The headline number that is not diluted by free 1.0s."""
    r = _run(FeatureCategoryPolicy(CATALOG), judge=_FixedJudge(0.6))
    assert r.mean_quality_routed_weak == pytest.approx(0.6)
    assert r.mean_quality_all > 0.6  # diluted by the strong calls


def test_rows_report_the_category_the_decision_was_made_on() -> None:
    """Without the catalog the row could only show what the fixture declared,
    which is rarely what actually drove the routing decision."""
    r = _run(FeatureCategoryPolicy(CATALOG), catalog=CATALOG)
    by_id = {o.id: o for o in r.outcomes}
    assert by_id["bg0"].category == BACKGROUND
    assert by_id["fg0"].category == FOREGROUND


def test_rows_fall_back_to_unspecified_without_a_catalog() -> None:
    r = _run(FeatureCategoryPolicy(CATALOG))
    assert all(o.category == "unspecified" for o in r.outcomes)


def test_every_sample_produces_an_auditable_row() -> None:
    r = _run(FeatureCategoryPolicy(CATALOG))
    assert len(r.outcomes) == 5
    assert all(o.reason for o in r.outcomes)


def test_baseline_is_always_the_all_strong_cost() -> None:
    """Even for routed calls, so savings are measured against a real baseline."""
    r = _run(FeatureCategoryPolicy(CATALOG))
    weak_rows = [o for o in r.outcomes if o.target == WEAK]
    assert all(o.baseline_usd > o.routed_usd for o in weak_rows)


def test_a_failed_strong_call_is_recorded_not_silently_free() -> None:
    r = _run(AllStrongPolicy(), strong_backend=_BrokenBackend())
    assert r.error_count == 5
    assert r.cost.baseline_usd == 0.0
    assert not r.trustworthy
    assert all(not o.ok and "billing" in (o.error or "") for o in r.outcomes)


def test_a_failed_weak_call_keeps_its_baseline_and_flags_the_run() -> None:
    r = _run(FeatureCategoryPolicy(CATALOG), weak_backend=_BrokenBackend())
    failed = [o for o in r.outcomes if not o.ok]
    assert len(failed) == 3
    assert all(o.baseline_usd > 0 for o in failed)
    assert not r.trustworthy


def test_failed_calls_are_excluded_from_the_aggregates() -> None:
    """One dead call must not flatter the headline."""
    r = _run(FeatureCategoryPolicy(CATALOG), weak_backend=_BrokenBackend())
    assert r.mean_quality_routed_weak is None
    assert r.mean_quality_all == 1.0  # only the surviving strong calls counted


def test_an_unpriced_model_raises_a_warning() -> None:
    r = _run(AllStrongPolicy(), pricing={"weak-m": (1.0, 5.0)})
    assert any("no pricing" in w for w in r.warnings)
    assert not r.trustworthy


def test_a_clean_run_is_trustworthy() -> None:
    assert _run(FeatureCategoryPolicy(CATALOG)).trustworthy


def test_result_serializes_to_json() -> None:
    d = _run(FeatureCategoryPolicy(CATALOG)).to_json()
    assert d["policy"] == "feature_category"
    assert d["cost"]["saved_pct"] > 0
    assert d["trustworthy"] is True
    assert len(d["outcomes"]) == 5


# ── sweep ───────────────────────────────────────────────────────────────


def _sweep(thresholds: list[float]) -> list[object]:
    return run_sweep(
        _samples(),
        thresholds=thresholds,
        strong_backend=MockBackend("strong"),
        weak_backend=MockBackend("weak"),
        judge=_FixedJudge(0.5),
        policy_factory=lambda t: ClassifierPolicy(threshold=t, catalog=CATALOG),
        **RUN_KWARGS,
    )


def test_sweep_returns_one_point_per_threshold() -> None:
    points = _sweep([0.1, 0.5, 0.9])
    assert [p.threshold for p in points] == [0.1, 0.5, 0.9]


def test_savings_rise_monotonically_with_the_threshold() -> None:
    """This monotonicity is what makes the output a curve worth reading."""
    points = _sweep([0.0, 0.25, 0.5, 0.75, 1.0])
    saved = [p.saved_pct for p in points]
    assert saved == sorted(saved)


def test_more_calls_go_weak_as_the_threshold_rises() -> None:
    points = _sweep([0.0, 0.5, 1.0])
    counts = [p.weak_count for p in points]
    assert counts == sorted(counts)
    assert counts[0] == 0  # threshold 0.0 routes nothing weak


def test_quality_falls_as_savings_rise() -> None:
    """The trade the curve exists to expose."""
    points = _sweep([0.0, 1.0])
    assert points[0].mean_quality_all > points[-1].mean_quality_all


def test_sweep_defaults_to_a_plain_classifier_policy() -> None:
    points = run_sweep(
        _samples(),
        thresholds=[0.5],
        strong_backend=MockBackend("strong"),
        weak_backend=MockBackend("weak"),
        judge=_FixedJudge(),
        **RUN_KWARGS,
    )
    assert len(points) == 1


def test_a_custom_policy_can_be_swept() -> None:
    class _AlwaysWeak(RoutingPolicy):
        name = "always_weak"

        def __init__(self, threshold: float) -> None:
            self.threshold = threshold

        def decide(self, sample: TrafficSample) -> RoutingDecision:
            return RoutingDecision(WEAK, "always")

    points = run_sweep(
        _samples(),
        thresholds=[0.3],
        strong_backend=MockBackend("strong"),
        weak_backend=MockBackend("weak"),
        judge=_FixedJudge(),
        policy_factory=_AlwaysWeak,
        **RUN_KWARGS,
    )
    assert points[0].weak_count == 5
