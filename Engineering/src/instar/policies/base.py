# SPDX-License-Identifier: Apache-2.0
"""The routing-policy interface.

A policy answers one question per call: **strong model or weak model?**

Instar does not route production traffic — it measures what a routing rule
*would have* cost and *would have* given up, replayed offline against your own
workload. A policy here is a hypothesis you are testing, not a component you
deploy.

``STRONG`` and ``WEAK`` are relative roles, not model tiers. Whatever you name
as the strong model is the quality baseline the run measures against; the weak
model is the cheaper candidate under test. That might be frontier-vs-cheap, or
hosted-vs-self-hosted, or last-generation-vs-current.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from instar.core.traffic import TrafficSample

STRONG = "strong"
WEAK = "weak"


@dataclass(frozen=True)
class RoutingDecision:
    """Where one call goes, and why.

    ``reason`` is carried into the per-sample report rows so a stakeholder can
    audit any individual decision instead of trusting an aggregate.
    """

    target: str  # STRONG | WEAK
    reason: str
    score: float | None = None


class RoutingPolicy(ABC):
    """Decides strong-vs-weak for each call."""

    name: str = "abstract"

    @abstractmethod
    def decide(self, sample: TrafficSample) -> RoutingDecision: ...
