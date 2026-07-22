# SPDX-License-Identifier: Apache-2.0
"""Rubrics: thresholds, verdict arithmetic, and the two refusals that matter."""

import json

import pytest

from instar.core.catalog import BACKGROUND, FeatureCatalog
from instar.core.route import run_route
from instar.core.traffic import TrafficSample
from instar.policies import AllStrongPolicy, FeatureCategoryPolicy
from instar.providers.base import Backend, CompletionResult
from instar.providers.mock import MockBackend
from instar.rubrics.base import Judge, JudgeResult
from instar.rubrics.spec import (
    FAIL,
    HIGHER_IS_BETTER,
    LOWER_IS_BETTER,
    MARGINAL,
    METRICS,
    PASS,
    UNMEASURED,
    Dimension,
    Rubric,
    evaluate_rubric,
)

CATALOG = FeatureCatalog({"bg.job": BACKGROUND})
PRICING = {"strong-m": (10.0, 50.0), "weak-m": (1.0, 5.0)}


# ── dimension thresholds ────────────────────────────────────────────────


def _dim(**kw: object) -> Dimension:
    base = {
        "id": "d",
        "metric": "quality.routed_weak_mean",
        "direction": HIGHER_IS_BETTER,
        "pass_at": 0.9,
        "marginal_at": 0.8,
    }
    base.update(kw)
    return Dimension(**base)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    ("value", "expected"),
    [(0.95, PASS), (0.9, PASS), (0.85, MARGINAL), (0.8, MARGINAL), (0.79, FAIL), (0.0, FAIL)],
)
def test_higher_is_better_thresholds(value: float, expected: str) -> None:
    assert _dim().verdict_for(value) == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [(500.0, PASS), (2000.0, PASS), (3000.0, MARGINAL), (5000.0, MARGINAL), (5001.0, FAIL)],
)
def test_lower_is_better_thresholds(value: float, expected: str) -> None:
    dim = _dim(
        metric="latency.p95_ms", direction=LOWER_IS_BETTER, pass_at=2000.0, marginal_at=5000.0
    )
    assert dim.verdict_for(value) == expected


def test_without_a_marginal_band_it_is_pass_or_fail() -> None:
    assert _dim(marginal_at=None).verdict_for(0.89) == FAIL
    assert _dim(marginal_at=None).verdict_for(0.9) == PASS


def test_an_unmeasured_metric_is_never_a_pass() -> None:
    """Silence is not evidence."""
    assert _dim().verdict_for(None) == UNMEASURED


def test_an_unknown_metric_is_rejected_at_construction() -> None:
    """A typo should fail at load time, not become a missing report row."""
    with pytest.raises(ValueError, match="unknown metric"):
        _dim(metric="quality.does_not_exist")


def test_an_invalid_direction_is_rejected() -> None:
    with pytest.raises(ValueError, match="direction"):
        _dim(direction="sideways")


def test_a_marginal_bar_on_the_wrong_side_is_rejected() -> None:
    with pytest.raises(ValueError, match="marginal_at"):
        _dim(pass_at=0.8, marginal_at=0.9)
    with pytest.raises(ValueError, match="marginal_at"):
        _dim(metric="latency.p95_ms", direction=LOWER_IS_BETTER, pass_at=5000.0, marginal_at=2000.0)


# ── rubric construction ─────────────────────────────────────────────────


def test_a_rubric_needs_at_least_one_dimension() -> None:
    with pytest.raises(ValueError, match="no dimensions"):
        Rubric(name="empty", dimensions=[])


def test_duplicate_dimension_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="duplicate"):
        Rubric(name="dupes", dimensions=[_dim(id="a"), _dim(id="a")])


def test_from_json_round_trips(tmp_path) -> None:
    path = tmp_path / "r.json"
    path.write_text(
        json.dumps(
            {
                "name": "r1",
                "description": "d",
                "dimensions": [
                    {
                        "id": "acc",
                        "metric": "quality.routed_weak_mean",
                        "direction": "higher_is_better",
                        "pass_at": 0.95,
                        "marginal_at": 0.9,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    rubric = Rubric.from_json(path)
    assert rubric.name == "r1"
    assert rubric.dimensions[0].pass_at == 0.95


def test_from_json_names_a_missing_field(tmp_path) -> None:
    path = tmp_path / "r.json"
    path.write_text(
        json.dumps({"name": "r", "dimensions": [{"id": "a", "metric": "cost.saved_pct"}]}),
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="pass_at"):
        Rubric.from_json(path)


# ── evaluation against a real run ───────────────────────────────────────


class _FixedJudge(Judge):
    name = "fixed"

    def __init__(self, score: float) -> None:
        self._score = score

    def score(
        self, sample: TrafficSample, strong: CompletionResult, weak: CompletionResult
    ) -> JudgeResult:
        return JudgeResult(self._score, "fixed")


class _BrokenBackend(Backend):
    name = "broken"

    def complete(self, sample: TrafficSample, model: str) -> CompletionResult:
        return CompletionResult.failure(model, "boom")


def _samples(n: int = 4) -> list[TrafficSample]:
    return [
        TrafficSample(id=f"s{i}", feature="bg.job", messages=[{"role": "user", "content": "x"}])
        for i in range(n)
    ]


def _run(quality: float = 1.0, policy=None, strong_backend=None):
    return run_route(
        _samples(),
        policy=policy or FeatureCategoryPolicy(CATALOG),
        strong_backend=strong_backend or MockBackend("strong", latency_s=0.5),
        weak_backend=MockBackend("weak", latency_s=0.1),
        judge=_FixedJudge(quality),
        strong_model="strong-m",
        weak_model="weak-m",
        pricing=PRICING,
        catalog=CATALOG,
    )


QUALITY_RUBRIC = Rubric(
    name="q",
    dimensions=[
        Dimension(
            id="acc",
            metric="quality.routed_weak_mean",
            direction=HIGHER_IS_BETTER,
            pass_at=0.95,
            marginal_at=0.85,
        )
    ],
)


def test_a_good_run_passes() -> None:
    assert QUALITY_RUBRIC.evaluate(_run(quality=1.0)).verdict == PASS


def test_a_middling_run_is_marginal() -> None:
    assert QUALITY_RUBRIC.evaluate(_run(quality=0.9)).verdict == MARGINAL


def test_a_bad_run_fails() -> None:
    assert QUALITY_RUBRIC.evaluate(_run(quality=0.1)).verdict == FAIL


def test_the_overall_verdict_is_the_worst_dimension_not_an_average() -> None:
    """A spectacular cost saving must not be able to hide a failing quality score."""
    rubric = Rubric(
        name="mixed",
        dimensions=[
            Dimension(
                id="savings", metric="cost.saved_pct", direction=HIGHER_IS_BETTER, pass_at=1.0
            ),
            Dimension(
                id="acc",
                metric="quality.routed_weak_mean",
                direction=HIGHER_IS_BETTER,
                pass_at=0.99,
            ),
        ],
    )
    verdict = rubric.evaluate(_run(quality=0.1))
    by_id = {d.id: d.verdict for d in verdict.dimensions}
    assert by_id["savings"] == PASS  # cost dimension is comfortably met
    assert by_id["acc"] == FAIL
    assert verdict.verdict == FAIL  # and the whole rubric fails on it


def test_a_dimension_with_nothing_to_measure_taints_the_verdict() -> None:
    """all_strong routes nothing weak, so routed-weak quality has no value."""
    verdict = QUALITY_RUBRIC.evaluate(_run(policy=AllStrongPolicy()))
    assert verdict.dimensions[0].verdict == UNMEASURED
    assert verdict.verdict == UNMEASURED
    assert verdict.unmeasured
    assert any("not a pass" in n for n in verdict.notes)


def test_failed_calls_are_surfaced_as_a_note() -> None:
    verdict = QUALITY_RUBRIC.evaluate(_run(strong_backend=_BrokenBackend()))
    assert any("rests on" in n for n in verdict.notes)


def test_latency_binds_to_the_call_the_user_waited_on() -> None:
    """Routed-weak calls used the fast weak backend, so p95 reflects that."""
    rubric = Rubric(
        name="lat",
        dimensions=[
            Dimension(id="p95", metric="latency.p95_ms", direction=LOWER_IS_BETTER, pass_at=150.0)
        ],
    )
    verdict = rubric.evaluate(_run())
    assert verdict.dimensions[0].value == pytest.approx(100.0)  # the 0.1s weak backend
    assert verdict.verdict == PASS


def test_verdict_records_the_deciding_number() -> None:
    d = QUALITY_RUBRIC.evaluate(_run(quality=0.5)).dimensions[0]
    assert d.value == pytest.approx(0.5)
    assert d.pass_at == 0.95
    assert d.metric == "quality.routed_weak_mean"


def test_verdict_serializes_to_json() -> None:
    payload = QUALITY_RUBRIC.evaluate(_run()).to_json()
    assert payload["verdict"] == PASS
    assert payload["dimensions"][0]["metric"] == "quality.routed_weak_mean"


def test_evaluate_rubric_wrapper_matches_the_method() -> None:
    result = _run()
    assert (
        evaluate_rubric(result, QUALITY_RUBRIC).verdict == QUALITY_RUBRIC.evaluate(result).verdict
    )


@pytest.mark.parametrize("metric", sorted(METRICS))
def test_every_registered_metric_binds_without_error(metric: str) -> None:
    """A metric in the registry that raises would only be discovered in a report."""
    value = METRICS[metric](_run())
    assert value is None or isinstance(value, float)


# ── the shipped example ─────────────────────────────────────────────────


def test_the_shipped_example_rubric_loads() -> None:
    from pathlib import Path

    path = (
        Path(__file__).resolve().parents[2]
        / "Engineering"
        / "fixtures"
        / "rubrics"
        / "support-triage-v1.json"
    )
    rubric = Rubric.from_json(path)
    assert rubric.name == "support-triage-v1"
    assert len(rubric.dimensions) >= 3
    # Every dimension should explain itself; a threshold with no stated reason
    # is one nobody can defend in a review.
    assert all(d.rationale for d in rubric.dimensions)
