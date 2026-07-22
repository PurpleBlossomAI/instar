# SPDX-License-Identifier: Apache-2.0
"""Captured-traffic format for replay.

A :class:`TrafficSample` is one LLM call, captured so it can be replayed offline
against any model, provider, or routing policy. The format is **PII-free by
construction**: there is no tenant id, user id, or raw-customer-content field.
When capturing from a real service, redact prompts to synthetic stand-ins before
writing a fixture — never persist real customer data here.

A fixture is a ``.jsonl`` file, one sample per line. A fixture represents one
*workload*: the trace of AI calls a real workflow makes (a support triage pass,
a campaign build, a sales follow-up). Measuring a workload — rather than a
single prompt — is the whole point: it captures the background jobs and
refinement loops that a "run it once and read the meter" estimate misses.

The ``feature`` field is your own dotted key. Instar attaches no meaning to it
beyond what your :class:`~instar.core.catalog.FeatureCatalog` assigns.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from instar.core.catalog import VALID_CATEGORIES


@dataclass
class TrafficSample:
    """One captured LLM call, ready to replay. PII-free by construction."""

    id: str
    feature: str
    messages: list[dict[str, Any]]
    max_tokens: int = 1024
    system: str | None = None
    temperature: float | None = None
    # Optional per-sample category override. Normally left None so the
    # FeatureCatalog decides; set it when one call in a feature is special.
    category: str | None = None
    # Free-form, non-PII metadata. Recognized keys:
    #   gold                  — correct label, for classification scoring
    #   cadence               — how often a scheduled job fires
    #   static_prefix_tokens  — size of a cacheable prompt prefix
    #   warm                  — True if this call reads a warm cache
    meta: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category is not None and self.category not in VALID_CATEGORIES:
            raise ValueError(
                f"sample {self.id!r}: category {self.category!r} "
                f"must be one of {sorted(VALID_CATEGORIES)} or None"
            )

    def to_json(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict[str, Any]) -> TrafficSample:
        return cls(
            id=d["id"],
            feature=d["feature"],
            messages=d["messages"],
            max_tokens=d.get("max_tokens", 1024),
            system=d.get("system"),
            temperature=d.get("temperature"),
            category=d.get("category"),
            meta=d.get("meta", {}),
        )


def load_traffic(path: str | Path) -> list[TrafficSample]:
    """Load a JSONL fixture (one sample per line; blank lines ignored)."""
    samples: list[TrafficSample] = []
    with open(path, encoding="utf-8") as fh:
        for lineno, raw in enumerate(fh, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                samples.append(TrafficSample.from_json(json.loads(line)))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
                raise ValueError(f"{path}:{lineno}: bad traffic sample: {e}") from e
    if not samples:
        raise ValueError(f"no samples found in {path}")
    return samples


def save_traffic(path: str | Path, samples: list[TrafficSample]) -> None:
    """Write samples to a JSONL fixture."""
    with open(path, "w", encoding="utf-8") as fh:
        for s in samples:
            fh.write(json.dumps(s.to_json(), ensure_ascii=False) + "\n")
