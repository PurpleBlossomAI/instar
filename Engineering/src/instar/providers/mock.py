# SPDX-License-Identifier: Apache-2.0
"""Deterministic mock backend — the hermetic default.

Mock mode is not a toy. It is how you read the data flow, write a fixture, wire
a policy, and get a green CI run without spending a token or holding an API key.
Output text and token counts are a pure function of ``(sample.id, model)``, so
two runs of the same fixture produce byte-identical results.

Numbers from a mock run are **deterministic placeholders, not a measurement**.
Every report Instar writes says so on its face.
"""

from __future__ import annotations

import hashlib

from instar.core.traffic import TrafficSample
from instar.providers.base import Backend, CompletionResult, estimate_tokens, sample_text


class MockBackend(Backend):
    """Reproducible synthetic completions.

    ``latency_s`` lets you give two mock arms different simulated speeds so a
    gateway comparison produces a non-degenerate spread.
    """

    def __init__(self, name: str = "mock", *, latency_s: float = 0.01) -> None:
        self.name = name
        self._latency = latency_s

    def complete(self, sample: TrafficSample, model: str) -> CompletionResult:
        seed = hashlib.sha256(f"{sample.id}:{model}".encode()).hexdigest()
        in_tok = estimate_tokens(sample_text(sample))
        # Deterministic pseudo-output length, capped by the sample's own limit.
        out_tok = 1 + (int(seed[:4], 16) % max(1, sample.max_tokens))
        text = f"[mock:{model}] response to {sample.feature} ({sample.id})"
        return CompletionResult(
            text=text,
            model=model,
            input_tokens=in_tok,
            output_tokens=out_tok,
            latency_s=self._latency,
            ok=True,
        )
