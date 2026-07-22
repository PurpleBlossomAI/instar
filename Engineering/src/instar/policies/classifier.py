# SPDX-License-Identifier: Apache-2.0
"""Per-prompt difficulty routing, and the threshold sweep that draws the curve.

:class:`ClassifierPolicy` scores each prompt for difficulty in ``[0, 1]`` and
routes the easy ones to the weak model. Sweeping the threshold is what produces
the cost/quality curve — the artifact that actually answers "how much can we
save before quality starts to hurt?", as opposed to a single point estimate
that tells you nothing about the trade.

The shipped :func:`heuristic_difficulty` scorer is **a stand-in, not a trained
router**. It exists so the harness runs end-to-end out of the box. Replace it
with a real classifier — that is the extension point, and the honest place to
put your effort if you want a publishable number.
"""

from __future__ import annotations

from collections.abc import Callable

from instar.core.catalog import BACKGROUND, FeatureCatalog
from instar.core.traffic import TrafficSample
from instar.policies.base import STRONG, WEAK, RoutingDecision, RoutingPolicy

DifficultyScorer = Callable[[TrafficSample], float]

# Words that tend to mark genuinely harder generative work rather than
# extraction or classification. Crude on purpose — see the module docstring.
HARD_CUES = ("analyze", "strategy", "reason", "plan", "compare", "critique", "synthesize")


def heuristic_difficulty(sample: TrafficSample, catalog: FeatureCatalog | None = None) -> float:
    """Cheap difficulty score in ``[0, 1]``; higher means "needs the strong model".

    Combines prompt length, a few lexical cues, and (if a catalog is given) the
    feature's category. This is a placeholder that produces a plausibly shaped
    curve — it is not a measurement of difficulty and should not be reported as
    one.
    """
    text = (
        (sample.system or "")
        + " "
        + " ".join(
            m.get("content", "") if isinstance(m.get("content"), str) else ""
            for m in sample.messages
        )
    )
    length_score = min(1.0, len(text) / 4000.0)  # ~1k tokens saturates
    cue_score = 0.3 if any(c in text.lower() for c in HARD_CUES) else 0.0
    category = catalog.category_for(sample) if catalog is not None else sample.category
    fg_score = 0.0 if category == BACKGROUND else 0.2
    return min(1.0, length_score + cue_score + fg_score)


class ClassifierPolicy(RoutingPolicy):
    """Route to the weak model when difficulty falls below ``threshold``.

    A low threshold keeps more traffic strong (safer, costlier); a high one
    pushes more to the weak model (cheaper, riskier). Neither end is the
    answer — the curve between them is.
    """

    name = "classifier"

    def __init__(
        self,
        threshold: float = 0.5,
        *,
        scorer: DifficultyScorer | None = None,
        catalog: FeatureCatalog | None = None,
    ) -> None:
        self.threshold = threshold
        self.catalog = catalog
        # Swap in a trained scorer here for a result worth publishing.
        self.scorer: DifficultyScorer = scorer or (lambda s: heuristic_difficulty(s, catalog))

    def decide(self, sample: TrafficSample) -> RoutingDecision:
        score = self.scorer(sample)
        if score < self.threshold:
            return RoutingDecision(WEAK, f"difficulty {score:.2f} < {self.threshold:.2f}", score)
        return RoutingDecision(STRONG, f"difficulty {score:.2f} >= {self.threshold:.2f}", score)
