# SPDX-License-Identifier: Apache-2.0
"""The judging interface: what did we give up by using the cheaper model?

A :class:`Judge` scores a weak completion **relative to the strong one** on the
same input, in ``[0, 1]``, where ``1.0`` means "the weak output is as good as
the strong output for this call."

Relative scoring is deliberate. The question a cost study has to answer is not
"is this output good?" in the abstract — it is "what do we lose by routing this
call to the cheap model?" Only a paired comparison answers that, and only a
paired comparison stays meaningful when your workload has no ground truth.

Where ground truth *does* exist — classification with known labels — use an
objective scorer instead. It is cheaper, faster, and not itself a model whose
judgment you would then have to validate.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from instar.core.traffic import TrafficSample
from instar.providers.base import CompletionResult


@dataclass(frozen=True)
class JudgeResult:
    """A quality score in ``[0, 1]`` plus the reasoning behind it.

    ``rationale`` lands in the per-sample report rows. A score nobody can audit
    is a number nobody should act on.
    """

    score: float
    rationale: str


class Judge(ABC):
    """Scores a weak completion against the strong baseline."""

    name: str = "abstract"

    @abstractmethod
    def score(
        self,
        sample: TrafficSample,
        strong: CompletionResult,
        weak: CompletionResult,
    ) -> JudgeResult: ...
