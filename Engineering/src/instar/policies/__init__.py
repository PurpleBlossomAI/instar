# SPDX-License-Identifier: Apache-2.0
"""Routing policies — the strong-vs-weak hypotheses a run tests."""

from __future__ import annotations

from instar.core.catalog import FeatureCatalog
from instar.policies.base import STRONG, WEAK, RoutingDecision, RoutingPolicy
from instar.policies.classifier import (
    HARD_CUES,
    ClassifierPolicy,
    DifficultyScorer,
    heuristic_difficulty,
)
from instar.policies.rules import AllStrongPolicy, FeatureCategoryPolicy

POLICY_NAMES = (AllStrongPolicy.name, FeatureCategoryPolicy.name, ClassifierPolicy.name)

__all__ = [
    "HARD_CUES",
    "POLICY_NAMES",
    "STRONG",
    "WEAK",
    "AllStrongPolicy",
    "ClassifierPolicy",
    "DifficultyScorer",
    "FeatureCategoryPolicy",
    "RoutingDecision",
    "RoutingPolicy",
    "build_policy",
    "heuristic_difficulty",
]


def build_policy(
    name: str,
    *,
    threshold: float = 0.5,
    catalog: FeatureCatalog | None = None,
) -> RoutingPolicy:
    """Construct a policy by name. ``catalog`` defaults to an empty one."""
    cat = catalog if catalog is not None else FeatureCatalog.empty()
    if name == AllStrongPolicy.name:
        return AllStrongPolicy()
    if name == FeatureCategoryPolicy.name:
        return FeatureCategoryPolicy(cat)
    if name == ClassifierPolicy.name:
        return ClassifierPolicy(threshold=threshold, catalog=cat)
    raise ValueError(f"unknown policy {name!r}; expected one of {list(POLICY_NAMES)}")
