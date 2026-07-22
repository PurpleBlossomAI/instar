# SPDX-License-Identifier: Apache-2.0
"""The gateway runner: percentiles, interleaving, and honest small-n warnings."""

import pytest

from instar.core.gateway import percentile, run_gateway, summarize
from instar.core.traffic import TrafficSample
from instar.providers.base import Backend, CompletionResult
from instar.providers.mock import MockBackend


def _samples(n: int = 4) -> list[TrafficSample]:
    return [
        TrafficSample(id=f"s{i}", feature="a.b", messages=[{"role": "user", "content": "x"}])
        for i in range(n)
    ]


class _RecordingBackend(Backend):
    """Appends its name to a shared log so call ordering can be asserted."""

    def __init__(self, name: str, log: list[str], latency_s: float = 0.01) -> None:
        self.name = name
        self.log = log
        self.latency_s = latency_s

    def complete(self, sample: TrafficSample, model: str) -> CompletionResult:
        self.log.append(self.name)
        return CompletionResult(
            text="ok", model=model, input_tokens=1, output_tokens=1, latency_s=self.latency_s
        )


class _BrokenBackend(Backend):
    name = "broken"

    def complete(self, sample: TrafficSample, model: str) -> CompletionResult:
        return CompletionResult.failure(model, "connection refused")


# ── percentile ──────────────────────────────────────────────────────────


def test_percentile_of_nothing_is_zero() -> None:
    assert percentile([], 50) == 0.0


def test_percentile_of_one_value_is_that_value() -> None:
    assert percentile([7.0], 99) == 7.0


def test_percentile_picks_by_nearest_rank() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]
    assert percentile(values, 0) == 1.0
    assert percentile(values, 50) == 3.0
    assert percentile(values, 100) == 5.0


def test_percentile_is_order_independent() -> None:
    assert percentile([5.0, 1.0, 3.0], 50) == percentile([1.0, 3.0, 5.0], 50)


# ── summarize ───────────────────────────────────────────────────────────


def test_summarize_excludes_failures_from_latency() -> None:
    results = [
        CompletionResult("a", "m", 1, 1, latency_s=0.010),
        CompletionResult.failure("m", "boom", latency_s=99.0),
    ]
    stats = summarize("arm", results)
    assert stats.n_ok == 1
    assert stats.n_err == 1
    assert stats.mean_ms == pytest.approx(10.0)


# ── run_gateway ─────────────────────────────────────────────────────────


def test_calls_are_interleaved_not_blocked() -> None:
    """Sequential blocks would attribute any drift to whichever arm ran second."""
    log: list[str] = []
    run_gateway(
        _samples(3),
        a_backend=_RecordingBackend("a", log),
        b_backend=_RecordingBackend("b", log),
        model="m",
    )
    assert log == ["a", "b", "a", "b", "a", "b"]


def test_overhead_is_the_a_minus_b_delta() -> None:
    r = run_gateway(
        _samples(),
        a_backend=MockBackend("slow", latency_s=0.030),
        b_backend=MockBackend("fast", latency_s=0.010),
        model="m",
    )
    assert r.overhead_p50_ms == pytest.approx(20.0)
    assert r.overhead_p95_ms == pytest.approx(20.0)
    assert r.overhead_p99_ms == pytest.approx(20.0)


def test_a_faster_arm_a_yields_negative_overhead() -> None:
    r = run_gateway(
        _samples(),
        a_backend=MockBackend("fast", latency_s=0.010),
        b_backend=MockBackend("slow", latency_s=0.030),
        model="m",
    )
    assert r.overhead_p50_ms < 0


def test_repeats_multiply_the_call_count() -> None:
    r = run_gateway(
        _samples(4),
        a_backend=MockBackend("a"),
        b_backend=MockBackend("b"),
        model="m",
        repeats=10,
    )
    assert r.n == 40
    assert r.a.n_ok == 40


def test_repeats_must_be_positive() -> None:
    with pytest.raises(ValueError, match="repeats"):
        run_gateway(
            _samples(), a_backend=MockBackend("a"), b_backend=MockBackend("b"), model="m", repeats=0
        )


def test_a_small_sample_warns_about_tail_percentiles() -> None:
    """p99 of 8 calls is just the slowest call; say so rather than imply rigor."""
    r = run_gateway(_samples(4), a_backend=MockBackend("a"), b_backend=MockBackend("b"), model="m")
    assert any("tail percentiles" in w for w in r.warnings)
    assert not r.trustworthy


def test_a_large_enough_sample_does_not_warn() -> None:
    r = run_gateway(_samples(40), a_backend=MockBackend("a"), b_backend=MockBackend("b"), model="m")
    assert r.warnings == []
    assert r.trustworthy


def test_failures_are_counted_and_reported() -> None:
    r = run_gateway(_samples(40), a_backend=_BrokenBackend(), b_backend=MockBackend("b"), model="m")
    assert r.a.n_err == 40
    assert any("failed" in w for w in r.warnings)
    assert not r.trustworthy


def test_result_serializes_to_json() -> None:
    r = run_gateway(_samples(40), a_backend=MockBackend("a"), b_backend=MockBackend("b"), model="m")
    d = r.to_json()
    assert d["n"] == 40
    assert d["a"]["backend"] == "a"
    assert d["trustworthy"] is True
