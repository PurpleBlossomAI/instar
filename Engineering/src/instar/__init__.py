# SPDX-License-Identifier: Apache-2.0
"""Instar — an open-source harness for measuring LLM workloads.

Run your own workloads through candidate models, providers, and routing
policies, and get defensible cost, quality, and latency numbers — so a decision
about which model mix to use for which team rests on evidence rather than on a
vendor's benchmark.

Instar measures. It does not route production traffic, and it takes no view on
which provider you should pick.

Start here::

    from instar.core.traffic import load_traffic
    from instar.core.route import run_route

Or from a shell::

    instar route --traffic your-workload.jsonl --policy feature_category
"""

__version__ = "0.1.0.dev0"
