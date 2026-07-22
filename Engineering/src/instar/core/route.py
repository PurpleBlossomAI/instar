# SPDX-License-Identifier: Apache-2.0
"""The routing runner — replay a workload, price it, score it.

For every sample the runner always computes the all-strong baseline cost, then
applies the policy. If the policy routes the call to the weak model, the weak
output is judged against the strong one; if the call stays strong, quality is
``1.0`` by definition because nothing changed.

Two headline numbers come out:

- **percent of spend saved** versus the all-strong baseline;
- **mean quality**, reported both overall and over the routed-weak subset.

The routed-weak figure is the one that matters. Overall mean quality is diluted
by every call that stayed strong and scored a free ``1.0``, so on a workload
that routes 10% of traffic it will look reassuring no matter how badly those
calls went. Quality risk lives entirely in the calls you actually moved.

:func:`run_sweep` runs the classifier policy across several thresholds to
produce the cost/quality curve.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from instar.core.catalog import FeatureCatalog
from instar.core.cost import CostSummary, call_cost_usd, unpriced_models
from instar.core.traffic import TrafficSample
from instar.policies.base import WEAK, RoutingPolicy
from instar.policies.classifier import ClassifierPolicy
from instar.providers.base import Backend, CompletionResult
from instar.rubrics.base import Judge

PricingTable = dict[str, tuple[float, float]]


@dataclass
class SampleOutcome:
    """What happened to one call. These rows make a run auditable."""

    id: str
    feature: str
    category: str
    target: str  # strong | weak
    reason: str
    baseline_usd: float  # all-strong cost for this call
    routed_usd: float  # cost under the policy
    quality: float  # 1.0 if kept strong; judge score if routed weak
    # Wall-clock for the call the user would actually have waited on: the weak
    # call when the policy routed it, the strong call otherwise. Routing to a
    # cheaper model changes latency as well as cost, usually for the better,
    # and a cost study that ignores that is telling half the story.
    baseline_latency_s: float = 0.0
    routed_latency_s: float = 0.0
    # Token counts for the routed call, as reported by the provider. Recorded so
    # a cost figure can be audited: without them a reader has to take the dollar
    # number on faith, and a wrong pricing row is invisible.
    routed_input_tokens: int = 0
    routed_output_tokens: int = 0
    rationale: str = ""
    ok: bool = True  # False if a backend call failed
    error: str | None = None


@dataclass
class RouteResult:
    """Aggregates for one policy over one workload."""

    policy: str
    strong_model: str
    weak_model: str
    n: int
    weak_count: int
    cost: CostSummary
    mean_quality_all: float
    mean_quality_routed_weak: float | None  # None if nothing routed weak
    error_count: int = 0
    warnings: list[str] = field(default_factory=list)
    outcomes: list[SampleOutcome] = field(default_factory=list)

    @property
    def trustworthy(self) -> bool:
        """False if anything happened that should stop you quoting these numbers."""
        return self.error_count == 0 and not self.warnings

    def to_json(self) -> dict[str, Any]:
        d = asdict(self)
        d["cost"] = asdict(self.cost)
        d["trustworthy"] = self.trustworthy
        return d


def run_route(
    samples: list[TrafficSample],
    *,
    policy: RoutingPolicy,
    strong_backend: Backend,
    weak_backend: Backend,
    judge: Judge,
    strong_model: str,
    weak_model: str,
    pricing: PricingTable | None = None,
    catalog: FeatureCatalog | None = None,
) -> RouteResult:
    """Replay ``samples`` through ``policy`` and measure cost and quality.

    ``catalog`` is used only to label each row with the category the routing
    decision was actually made on. Without it the report can only show what the
    fixture happened to declare, which is rarely what drove the decision.
    """
    outcomes: list[SampleOutcome] = []
    weak_qualities: list[float] = []

    for sample in samples:
        decision = policy.decide(sample)
        if catalog is not None:
            category = catalog.category_for(sample)
        else:
            category = sample.category or "unspecified"

        strong: CompletionResult = strong_backend.complete(sample, strong_model)
        # A failed call is recorded loudly, never as a silent $0. Excluding it
        # from the aggregates keeps one dead call from flattering the headline;
        # counting it in error_count keeps the run from looking clean.
        if not strong.ok:
            outcomes.append(
                SampleOutcome(
                    id=sample.id,
                    feature=sample.feature,
                    category=category,
                    target="strong",
                    reason="strong call failed",
                    baseline_usd=0.0,
                    routed_usd=0.0,
                    quality=0.0,
                    ok=False,
                    error=strong.error,
                )
            )
            continue

        baseline_usd = call_cost_usd(
            strong_model, strong.input_tokens, strong.output_tokens, pricing=pricing
        )

        if decision.target == WEAK:
            weak = weak_backend.complete(sample, weak_model)
            if not weak.ok:
                outcomes.append(
                    SampleOutcome(
                        id=sample.id,
                        feature=sample.feature,
                        category=category,
                        target=WEAK,
                        reason="weak call failed",
                        baseline_usd=baseline_usd,
                        routed_usd=0.0,
                        quality=0.0,
                        ok=False,
                        error=weak.error,
                    )
                )
                continue
            routed_usd = call_cost_usd(
                weak_model, weak.input_tokens, weak.output_tokens, pricing=pricing
            )
            verdict = judge.score(sample, strong, weak)
            quality = verdict.score
            rationale = verdict.rationale
            routed_latency_s = weak.latency_s
            routed_call = weak
            weak_qualities.append(quality)
        else:
            routed_usd = baseline_usd
            quality = 1.0
            rationale = "kept on strong model; unchanged by definition"
            routed_latency_s = strong.latency_s
            routed_call = strong

        outcomes.append(
            SampleOutcome(
                id=sample.id,
                feature=sample.feature,
                category=category,
                target=decision.target,
                reason=decision.reason,
                baseline_usd=baseline_usd,
                routed_usd=routed_usd,
                quality=quality,
                baseline_latency_s=strong.latency_s,
                routed_latency_s=routed_latency_s,
                routed_input_tokens=routed_call.input_tokens,
                routed_output_tokens=routed_call.output_tokens,
                rationale=rationale,
            )
        )

    ok_outcomes = [o for o in outcomes if o.ok]
    baseline_total = sum(o.baseline_usd for o in ok_outcomes)
    routed_total = sum(o.routed_usd for o in ok_outcomes)
    mean_q_all = sum(o.quality for o in ok_outcomes) / len(ok_outcomes) if ok_outcomes else 0.0
    mean_q_weak = (sum(weak_qualities) / len(weak_qualities)) if weak_qualities else None

    warnings: list[str] = []
    missing = unpriced_models([strong_model, weak_model], pricing=pricing)
    if missing:
        warnings.append(
            f"no pricing for {', '.join(missing)} - those calls were costed at $0, "
            f"so the totals understate real spend"
        )

    return RouteResult(
        policy=policy.name,
        strong_model=strong_model,
        weak_model=weak_model,
        n=len(outcomes),
        weak_count=len(weak_qualities),
        cost=CostSummary.of(baseline_total, routed_total),
        mean_quality_all=mean_q_all,
        mean_quality_routed_weak=mean_q_weak,
        error_count=sum(1 for o in outcomes if not o.ok),
        warnings=warnings,
        outcomes=outcomes,
    )


@dataclass
class SweepPoint:
    """One point on the cost/quality curve."""

    threshold: float
    saved_pct: float
    mean_quality_all: float
    mean_quality_routed_weak: float | None
    weak_count: int


def run_sweep(
    samples: list[TrafficSample],
    *,
    thresholds: list[float],
    strong_backend: Backend,
    weak_backend: Backend,
    judge: Judge,
    strong_model: str,
    weak_model: str,
    policy_factory: Any = None,
    pricing: PricingTable | None = None,
    catalog: FeatureCatalog | None = None,
) -> list[SweepPoint]:
    """Cost/quality points across classifier thresholds.

    ``policy_factory`` takes a threshold and returns a policy; it defaults to a
    plain :class:`ClassifierPolicy`. Override it to sweep a policy of your own
    (a trained router, or one carrying a feature catalog).
    """
    factory = policy_factory or (lambda t: ClassifierPolicy(threshold=t))
    points: list[SweepPoint] = []
    for threshold in thresholds:
        result = run_route(
            samples,
            policy=factory(threshold),
            strong_backend=strong_backend,
            weak_backend=weak_backend,
            judge=judge,
            strong_model=strong_model,
            weak_model=weak_model,
            pricing=pricing,
            catalog=catalog,
        )
        points.append(
            SweepPoint(
                threshold=threshold,
                saved_pct=result.cost.saved_pct,
                mean_quality_all=result.mean_quality_all,
                mean_quality_routed_weak=result.mean_quality_routed_weak,
                weak_count=result.weak_count,
            )
        )
    return points
