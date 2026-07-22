# SPDX-License-Identifier: Apache-2.0
"""Rule-based routing policies.

Two policies with no model and no training behind them:

- :class:`AllStrongPolicy` — the control. Everything goes to the strong model.
  This is the baseline every saving is measured against, and you should always
  run it first.
- :class:`FeatureCategoryPolicy` — the cheapest defensible real policy. Send
  background work to the cheap model, keep foreground work strong.

The second one is worth taking seriously before anything cleverer. It needs no
classifier, it is trivially explainable to a stakeholder ("we only spend
premium tokens where a person is waiting"), and on a workload with a large
scheduled-job floor it captures most of the available saving. Measure it before
you reach for a learned router.
"""

from __future__ import annotations

from instar.core.catalog import BACKGROUND, FeatureCatalog
from instar.core.traffic import TrafficSample
from instar.policies.base import STRONG, WEAK, RoutingDecision, RoutingPolicy


class AllStrongPolicy(RoutingPolicy):
    """Control: route every call to the strong model."""

    name = "all_strong"

    def decide(self, sample: TrafficSample) -> RoutingDecision:
        return RoutingDecision(STRONG, "control: everything strong")


class FeatureCategoryPolicy(RoutingPolicy):
    """Background → weak, foreground → strong, per your feature catalog.

    Spends quality only where somebody is watching. Requires a
    :class:`~instar.core.catalog.FeatureCatalog`; with an empty catalog every
    feature falls to the default (foreground), which makes this policy behave
    exactly like the control — a useful sanity check, and a signal that you
    have not catalogued your features yet.
    """

    name = "feature_category"

    def __init__(self, catalog: FeatureCatalog) -> None:
        self.catalog = catalog

    def decide(self, sample: TrafficSample) -> RoutingDecision:
        category = self.catalog.category_for(sample)
        if category == BACKGROUND:
            return RoutingDecision(WEAK, "background feature → weak model")
        return RoutingDecision(STRONG, f"{category} feature → strong model")
