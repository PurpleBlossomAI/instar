# SPDX-License-Identifier: Apache-2.0
"""Feature catalog — the map from your feature keys to routing categories.

A *feature* is one named AI touchpoint in your product or department workflow
("support.ticket_classification", "campaign.copy_generation"). A *category*
says how much quality that touchpoint can afford to lose:

- ``FOREGROUND`` — a person is waiting on this output and will judge it.
- ``BACKGROUND`` — it runs on a schedule or behind the scenes; nobody is
  watching a spinner, so a cheaper model is often good enough.

That split is the cheapest defensible routing rule there is, and it is the one
thing a harness cannot guess for you: only you know which of your features a
user actually watches. So the catalog is **your** config, not ours — load it
from JSON with :meth:`FeatureCatalog.from_json` and pass it wherever a category
is needed.

Resolution order for a sample's category:

1. the sample's own ``category`` field, if the fixture declares one;
2. the catalog's ``categories`` map, keyed by ``feature``;
3. the catalog's ``default`` (``FOREGROUND`` unless you say otherwise).

Defaulting to FOREGROUND is deliberate: an unclassified feature is treated as
quality-sensitive, so forgetting to catalog something costs you money, never
quality.
"""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # avoid a runtime import cycle: traffic imports nothing from here
    from instar.core.traffic import TrafficSample

FOREGROUND = "foreground"
BACKGROUND = "background"
VALID_CATEGORIES = frozenset({FOREGROUND, BACKGROUND})


@dataclass(frozen=True)
class FeatureCatalog:
    """Your feature-key → category map.

    Construct directly for tests, or load a JSON file shaped like::

        {
          "default": "foreground",
          "categories": {
            "support.ticket_classification": "background",
            "campaign.copy_generation": "foreground"
          }
        }
    """

    categories: Mapping[str, str]
    default: str = FOREGROUND

    def __post_init__(self) -> None:
        if self.default not in VALID_CATEGORIES:
            raise ValueError(
                f"default category {self.default!r} must be one of {sorted(VALID_CATEGORIES)}"
            )
        for feature, category in self.categories.items():
            if category not in VALID_CATEGORIES:
                raise ValueError(
                    f"feature {feature!r} has category {category!r}; "
                    f"must be one of {sorted(VALID_CATEGORIES)}"
                )

    @classmethod
    def empty(cls, default: str = FOREGROUND) -> FeatureCatalog:
        """A catalog that classifies nothing — everything falls to ``default``."""
        return cls(categories={}, default=default)

    @classmethod
    def from_json(cls, path: str | Path) -> FeatureCatalog:
        """Load a catalog from a JSON file. See the class docstring for the shape."""
        with open(path, encoding="utf-8") as fh:
            data: Any = json.load(fh)
        if not isinstance(data, dict):
            raise ValueError(f"{path}: catalog must be a JSON object")
        categories = data.get("categories", {})
        if not isinstance(categories, dict):
            raise ValueError(f"{path}: 'categories' must be a JSON object")
        default = data.get("default", FOREGROUND)
        if not isinstance(default, str):
            raise ValueError(f"{path}: 'default' must be a string")
        return cls(
            categories={str(k): str(v) for k, v in categories.items()},
            default=default,
        )

    def to_json(self) -> dict[str, Any]:
        return {"default": self.default, "categories": dict(self.categories)}

    def category_for_feature(self, feature: str) -> str:
        """Category for a bare feature key, ignoring any per-sample override."""
        return self.categories.get(feature, self.default)

    def category_for(self, sample: TrafficSample) -> str:
        """Category for a sample: its own declaration wins, else the map, else default."""
        if sample.category is not None:
            return sample.category
        return self.category_for_feature(sample.feature)

    def unknown_features(self, features: Iterable[str]) -> list[str]:
        """Feature keys not present in the map — i.e. the ones silently taking the
        default. Surface these so a run never quietly mis-categorizes traffic."""
        if isinstance(features, str):
            raise TypeError("features must be an iterable of feature keys, not a single string")
        return sorted(set(features) - set(self.categories))
