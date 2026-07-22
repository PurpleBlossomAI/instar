# SPDX-License-Identifier: Apache-2.0
"""The gateway runner — what does the thing in front of your model cost you?

Runs the same workload through two arms (A and B) and compares per-call
latency: p50, p95, p99, and the delta between them. Each arm is just a
:class:`~instar.providers.base.Backend`, so this compares whatever you point it
at — a hosted router against a self-hosted proxy, a gateway against calling the
provider directly, or two configurations of the same gateway.

Instar takes no view on which gateway you should use, and ships no capability
matrix comparing vendors. Feature checklists go stale, and a vendor's own
comparison table is marketing. What a harness can honestly contribute is the
number nobody publishes about your traffic: the latency your chosen layer
actually adds, measured on your own workload.

**Calls are interleaved** (A, B, A, B, …) rather than run in blocks. Sequential
blocks silently attribute any drift in network conditions or provider load to
whichever arm ran second, which is exactly the difference being measured.
Interleaving spreads that noise across both arms.

Latency is wall-clock from the client, so it includes your network path to each
endpoint. Comparing a service across the internet against one on localhost
measures geography as much as software — put the arms on comparable footing
before drawing a conclusion.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from instar.core.traffic import TrafficSample
from instar.providers.base import Backend, CompletionResult


def percentile(values: list[float], pct: float) -> float:
    """Nearest-rank percentile (``pct`` in 0..100). Stdlib-only; fine for small n.

    With few samples a high percentile is barely meaningful — p99 of 10 calls is
    just the slowest call. Treat the tail figures as indicative until n is well
    into the hundreds.
    """
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    k = max(0, min(len(ordered) - 1, round((pct / 100.0) * (len(ordered) - 1))))
    return ordered[k]


@dataclass
class LatencyStats:
    """Per-arm latency summary, in milliseconds."""

    backend: str
    n_ok: int
    n_err: int
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float


def summarize(backend_name: str, results: list[CompletionResult]) -> LatencyStats:
    """Latency stats over the successful calls in ``results``."""
    ok = [r for r in results if r.ok]
    lat_ms = [r.latency_s * 1000.0 for r in ok]
    mean = (sum(lat_ms) / len(lat_ms)) if lat_ms else 0.0
    return LatencyStats(
        backend=backend_name,
        n_ok=len(ok),
        n_err=len(results) - len(ok),
        p50_ms=percentile(lat_ms, 50),
        p95_ms=percentile(lat_ms, 95),
        p99_ms=percentile(lat_ms, 99),
        mean_ms=mean,
    )


@dataclass
class GatewayResult:
    """A vs B latency comparison over one workload."""

    model: str
    n: int
    a: LatencyStats
    b: LatencyStats
    overhead_p50_ms: float  # a - b
    overhead_p95_ms: float
    overhead_p99_ms: float
    warnings: list[str] = field(default_factory=list)

    @property
    def trustworthy(self) -> bool:
        return self.a.n_err == 0 and self.b.n_err == 0 and not self.warnings

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["trustworthy"] = self.trustworthy
        return d


def run_gateway(
    samples: list[TrafficSample],
    *,
    a_backend: Backend,
    b_backend: Backend,
    model: str,
    repeats: int = 1,
) -> GatewayResult:
    """Replay ``samples`` through both arms, interleaved, and compare latency.

    ``repeats`` replays the whole workload more than once. Latency is noisy;
    a single pass over a short fixture is an anecdote.
    """
    if repeats < 1:
        raise ValueError("repeats must be >= 1")

    a_results: list[CompletionResult] = []
    b_results: list[CompletionResult] = []
    for _ in range(repeats):
        for sample in samples:
            a_results.append(a_backend.complete(sample, model))
            b_results.append(b_backend.complete(sample, model))

    a_stats = summarize(a_backend.name, a_results)
    b_stats = summarize(b_backend.name, b_results)

    warnings: list[str] = []
    total_calls = len(samples) * repeats
    if total_calls < 30:
        warnings.append(
            f"only {total_calls} calls per arm - tail percentiles are indicative at best; "
            f"raise --repeats or use a larger fixture before quoting p95/p99"
        )
    for stats in (a_stats, b_stats):
        if stats.n_err:
            warnings.append(f"{stats.backend}: {stats.n_err}/{total_calls} calls failed")

    return GatewayResult(
        model=model,
        n=total_calls,
        a=a_stats,
        b=b_stats,
        overhead_p50_ms=a_stats.p50_ms - b_stats.p50_ms,
        overhead_p95_ms=a_stats.p95_ms - b_stats.p95_ms,
        overhead_p99_ms=a_stats.p99_ms - b_stats.p99_ms,
        warnings=warnings,
    )
