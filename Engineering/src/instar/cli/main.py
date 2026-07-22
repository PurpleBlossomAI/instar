# SPDX-License-Identifier: Apache-2.0
"""The ``instar`` command line.

Two subcommands:

- ``instar route`` — replay a workload through a routing policy; measure spend
  saved and quality given up. Sweep a threshold to draw the cost/quality curve.
- ``instar gateway`` — replay a workload through two gateways or endpoints;
  compare per-call latency.

Both default to **mock mode**, which is hermetic: no API keys, no network, no
spend. Pass ``--live`` to use real endpoints.

Exit status is ``1`` when a run produced failed calls, so CI can refuse to
publish a report built on partial data.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from instar.core.catalog import FeatureCatalog
from instar.core.cost import load_pricing
from instar.core.gateway import run_gateway
from instar.core.route import run_route, run_sweep
from instar.core.traffic import TrafficSample, load_traffic
from instar.policies import POLICY_NAMES, ClassifierPolicy, build_policy
from instar.providers.anthropic import AnthropicBackend
from instar.providers.base import Backend
from instar.providers.mock import MockBackend
from instar.providers.openai_compat import OpenAICompatBackend
from instar.reporters import DEFAULT_RUNS_DIR, report_gateway, report_route, report_sweep
from instar.rubrics.base import Judge
from instar.rubrics.judges import AutoJudge, LabelMatchJudge, LLMJudge, MockJudge

# Undated model ids on purpose — dated snapshot ids are a recurring 404 source.
DEFAULT_STRONG = os.getenv("INSTAR_STRONG_MODEL", "claude-sonnet-4-6")
DEFAULT_WEAK = os.getenv("INSTAR_WEAK_MODEL", "claude-haiku-4-5")
DEFAULT_GATEWAY_MODEL = os.getenv("INSTAR_GATEWAY_MODEL", "claude-haiku-4-5")

MOCK_STRONG_MODEL = "mock-strong"
MOCK_WEAK_MODEL = "mock-weak"

# Where to look for the default fixture when --traffic is omitted.
_TRAFFIC_SEARCH = (
    Path("sample-traffic.jsonl"),
    Path("fixtures/sample-traffic.jsonl"),
    Path("Engineering/fixtures/sample-traffic.jsonl"),
)


def _resolve_traffic(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    for candidate in _TRAFFIC_SEARCH:
        if candidate.is_file():
            return candidate
    tried = ", ".join(str(p) for p in _TRAFFIC_SEARCH)
    raise SystemExit(
        f"instar: no --traffic given and no default fixture found (looked for: {tried}).\n"
        f"Pass --traffic path/to/workload.jsonl"
    )


def _load_catalog(path: str | None) -> FeatureCatalog:
    if not path:
        return FeatureCatalog.empty()
    return FeatureCatalog.from_json(path)


def _warn_uncatalogued(catalog: FeatureCatalog, samples: list[TrafficSample]) -> None:
    """Tell the user which features fell through to the default category.

    Silence here is how a workload gets mis-costed: an uncatalogued feature is
    treated as foreground and quietly never routed to the cheap model, so the
    savings look worse than they are and nobody can see why.
    """
    features = {s.feature for s in samples if s.category is None}
    unknown = catalog.unknown_features(features)
    if unknown:
        print(
            f"  note: {len(unknown)} feature(s) not in the catalog, defaulting to "
            f"'{catalog.default}': {', '.join(unknown)}",
            file=sys.stderr,
        )


def _cmd_route(args: argparse.Namespace) -> int:
    traffic_path = _resolve_traffic(args.traffic)
    samples = load_traffic(traffic_path)
    catalog = _load_catalog(args.catalog)
    pricing = load_pricing(args.pricing) if args.pricing else None
    mock = not args.live

    strong_model = MOCK_STRONG_MODEL if mock else args.strong_model
    weak_model = MOCK_WEAK_MODEL if mock else args.weak_model

    strong_backend: Backend
    weak_backend: Backend
    judge: Judge
    if mock:
        strong_backend = MockBackend("strong", latency_s=0.020)
        weak_backend = MockBackend("weak", latency_s=0.008)
        judge = MockJudge(catalog)
    else:
        strong_backend = AnthropicBackend("strong")
        weak_backend = AnthropicBackend("weak")
        # Objective label-match wherever a gold label exists; LLM-as-judge for
        # everything else. One judge therefore handles a mixed workload.
        labels = sorted({str(s.meta["gold"]) for s in samples if s.meta.get("gold")})
        label_judge = LabelMatchJudge(labels) if labels else None
        judge = AutoJudge(
            label_judge, LLMJudge(AnthropicBackend("judge"), judge_model=strong_model)
        )

    _warn_uncatalogued(catalog, samples)

    if args.sweep:
        try:
            thresholds = [float(x) for x in args.sweep.split(",") if x.strip()]
        except ValueError as e:
            raise SystemExit(f"instar: --sweep must be comma-separated numbers: {e}") from e
        if not thresholds:
            raise SystemExit("instar: --sweep needs at least one threshold")
        points = run_sweep(
            samples,
            thresholds=thresholds,
            strong_backend=strong_backend,
            weak_backend=weak_backend,
            judge=judge,
            strong_model=strong_model,
            weak_model=weak_model,
            policy_factory=lambda t: ClassifierPolicy(threshold=t, catalog=catalog),
            pricing=pricing,
            catalog=catalog,
        )
        label = args.label or f"route-sweep-{'mock' if mock else 'live'}"
        d = report_sweep(
            points,
            label,
            mock=mock,
            strong_model=strong_model,
            weak_model=weak_model,
            runs_dir=args.runs_dir,
        )
        print(f"sweep -> {d}")
        for p in points:
            mq_weak = (
                "  n/a"
                if p.mean_quality_routed_weak is None
                else f"{p.mean_quality_routed_weak:.3f}"
            )
            print(
                f"  t={p.threshold:.2f}  saved={p.saved_pct:5.1f}%  "
                f"q_all={p.mean_quality_all:.3f}  q_weak={mq_weak}  weak={p.weak_count}"
            )
        return 0

    policy = build_policy(args.policy, threshold=args.threshold, catalog=catalog)
    result = run_route(
        samples,
        policy=policy,
        strong_backend=strong_backend,
        weak_backend=weak_backend,
        judge=judge,
        strong_model=strong_model,
        weak_model=weak_model,
        pricing=pricing,
        catalog=catalog,
    )
    label = args.label or f"route-{policy.name}-{'mock' if mock else 'live'}"
    d = report_route(result, label, mock=mock, runs_dir=args.runs_dir)

    mq_weak = (
        "n/a"
        if result.mean_quality_routed_weak is None
        else f"{result.mean_quality_routed_weak:.3f}"
    )
    print(f"route -> {d}")
    print(
        f"  policy={result.policy}  saved={result.cost.saved_pct:.1f}%  "
        f"q_all={result.mean_quality_all:.3f}  q_weak={mq_weak}  "
        f"weak={result.weak_count}/{result.n}"
    )
    for w in result.warnings:
        print(f"  warning: {w}", file=sys.stderr)
    if result.error_count:
        print(
            f"  {result.error_count}/{result.n} calls FAILED — figures exclude them and "
            f"are NOT trustworthy until you re-run clean",
            file=sys.stderr,
        )
        return 1
    return 0


def _cmd_gateway(args: argparse.Namespace) -> int:
    traffic_path = _resolve_traffic(args.traffic)
    samples = load_traffic(traffic_path)
    mock = not args.live
    model = MOCK_WEAK_MODEL if mock else args.model

    a_backend: Backend
    b_backend: Backend
    if mock:
        # Two arms with different simulated latency, so the mock comparison is
        # non-degenerate and you can see the report take shape.
        a_backend = MockBackend(args.a_name, latency_s=0.012)
        b_backend = MockBackend(args.b_name, latency_s=0.010)
    else:
        if not args.a_url or not args.b_url:
            raise SystemExit("instar: --live gateway runs need both --a-url and --b-url")
        a_backend = OpenAICompatBackend(args.a_url, name=args.a_name, api_key_env=args.a_key_env)
        b_backend = OpenAICompatBackend(args.b_url, name=args.b_name, api_key_env=args.b_key_env)

    result = run_gateway(
        samples,
        a_backend=a_backend,
        b_backend=b_backend,
        model=model,
        repeats=args.repeats,
    )
    label = args.label or f"gateway-{'mock' if mock else 'live'}"
    d = report_gateway(result, label, mock=mock, runs_dir=args.runs_dir)
    print(f"gateway -> {d}")
    print(
        f"  overhead ({result.a.backend} - {result.b.backend}): "
        f"p50 {result.overhead_p50_ms:+.1f}ms  "
        f"p95 {result.overhead_p95_ms:+.1f}ms  "
        f"p99 {result.overhead_p99_ms:+.1f}ms"
    )
    for w in result.warnings:
        print(f"  warning: {w}", file=sys.stderr)
    return 1 if (result.a.n_err or result.b.n_err) else 0


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--traffic", help="workload fixture (.jsonl); defaults to a sample if present")
    p.add_argument("--live", action="store_true", help="use real endpoints instead of mocks")
    p.add_argument("--label", help="run label; output goes to <runs-dir>/<label>/")
    p.add_argument("--runs-dir", default=DEFAULT_RUNS_DIR, help="where to write run output")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="instar",
        description="Measure LLM cost, quality, and latency on your own workloads.",
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    route = sub.add_parser(
        "route", help="replay a workload through a routing policy; measure cost vs quality"
    )
    _add_common(route)
    route.add_argument(
        "--policy",
        default="feature_category",
        choices=list(POLICY_NAMES),
        help="routing policy to test (default: feature_category)",
    )
    route.add_argument("--threshold", type=float, default=0.5, help="classifier policy threshold")
    route.add_argument("--sweep", help="comma-separated thresholds to sweep, e.g. 0.2,0.4,0.6,0.8")
    route.add_argument("--catalog", help="feature catalog JSON mapping features to categories")
    route.add_argument("--pricing", help="pricing table JSON; overrides the placeholder table")
    route.add_argument("--strong-model", default=DEFAULT_STRONG)
    route.add_argument("--weak-model", default=DEFAULT_WEAK)
    route.set_defaults(func=_cmd_route)

    gateway = sub.add_parser(
        "gateway", help="compare two gateways or endpoints on per-call latency"
    )
    _add_common(gateway)
    gateway.add_argument("--model", default=DEFAULT_GATEWAY_MODEL)
    gateway.add_argument("--a-url", help="arm A base url (OpenAI-compatible)")
    gateway.add_argument("--a-name", default="arm-a", help="label for arm A in the report")
    gateway.add_argument("--a-key-env", help="env var holding arm A's API key")
    gateway.add_argument("--b-url", help="arm B base url (OpenAI-compatible)")
    gateway.add_argument("--b-name", default="arm-b", help="label for arm B in the report")
    gateway.add_argument("--b-key-env", help="env var holding arm B's API key")
    gateway.add_argument(
        "--repeats", type=int, default=1, help="replay the workload N times (latency is noisy)"
    )
    gateway.set_defaults(func=_cmd_gateway)

    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    exit_code: int = args.func(args)
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
