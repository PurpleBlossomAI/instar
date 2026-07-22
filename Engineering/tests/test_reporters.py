# SPDX-License-Identifier: Apache-2.0
"""Reporters: files land where promised, and caveats travel with the numbers."""

import json

from instar.core.catalog import BACKGROUND, FeatureCatalog
from instar.core.gateway import run_gateway
from instar.core.route import run_route, run_sweep
from instar.core.traffic import TrafficSample
from instar.policies import ClassifierPolicy, FeatureCategoryPolicy
from instar.providers.base import Backend, CompletionResult
from instar.providers.mock import MockBackend
from instar.reporters import report_gateway, report_route, report_sweep
from instar.rubrics.judges import MockJudge

CATALOG = FeatureCatalog({"bg.job": BACKGROUND})
PRICING = {"strong-m": (10.0, 50.0), "weak-m": (1.0, 5.0)}


def _samples() -> list[TrafficSample]:
    return [
        TrafficSample(id=f"s{i}", feature="bg.job", messages=[{"role": "user", "content": "x"}])
        for i in range(4)
    ]


class _BrokenBackend(Backend):
    name = "broken"

    def complete(self, sample: TrafficSample, model: str) -> CompletionResult:
        return CompletionResult.failure(model, "billing problem")


def _route_result(strong_backend: Backend | None = None, pricing=PRICING):
    return run_route(
        _samples(),
        policy=FeatureCategoryPolicy(CATALOG),
        strong_backend=strong_backend or MockBackend("strong"),
        weak_backend=MockBackend("weak"),
        judge=MockJudge(CATALOG),
        strong_model="strong-m",
        weak_model="weak-m",
        pricing=pricing,
    )


def test_route_report_writes_both_files(tmp_path) -> None:
    d = report_route(_route_result(), "run-1", mock=True, runs_dir=tmp_path)
    assert (d / "result.json").is_file()
    assert (d / "report.md").is_file()
    assert d == tmp_path / "run-1"


def test_route_report_json_is_valid_and_complete(tmp_path) -> None:
    d = report_route(_route_result(), "run-1", mock=True, runs_dir=tmp_path)
    payload = json.loads((d / "result.json").read_text(encoding="utf-8"))
    assert payload["policy"] == "feature_category"
    assert len(payload["outcomes"]) == 4


def test_a_mock_report_says_so_on_its_face(tmp_path) -> None:
    """These files get pasted into decks. The caveat has to travel with them."""
    d = report_route(_route_result(), "run-1", mock=True, runs_dir=tmp_path)
    md = (d / "report.md").read_text(encoding="utf-8")
    assert "MOCK RUN" in md
    assert "not a measurement" in md


def test_a_live_report_carries_no_mock_banner(tmp_path) -> None:
    d = report_route(_route_result(), "run-1", mock=False, runs_dir=tmp_path)
    assert "MOCK RUN" not in (d / "report.md").read_text(encoding="utf-8")


def test_failed_calls_are_announced_above_the_numbers(tmp_path) -> None:
    result = _route_result(strong_backend=_BrokenBackend())
    d = report_route(result, "run-1", mock=False, runs_dir=tmp_path)
    md = (d / "report.md").read_text(encoding="utf-8")
    assert "calls FAILED" in md
    assert md.index("calls FAILED") < md.index("| metric | value |")


def test_an_unpriced_model_warning_reaches_the_report(tmp_path) -> None:
    result = _route_result(pricing={"weak-m": (1.0, 5.0)})
    d = report_route(result, "run-1", mock=False, runs_dir=tmp_path)
    assert "no pricing" in (d / "report.md").read_text(encoding="utf-8")


def test_route_report_lists_every_per_call_decision(tmp_path) -> None:
    d = report_route(_route_result(), "run-1", mock=True, runs_dir=tmp_path)
    md = (d / "report.md").read_text(encoding="utf-8")
    for i in range(4):
        assert f"`s{i}`" in md


def test_route_report_flags_the_dilution_of_overall_quality(tmp_path) -> None:
    d = report_route(_route_result(), "run-1", mock=True, runs_dir=tmp_path)
    assert "routed-weak" in (d / "report.md").read_text(encoding="utf-8")


def test_nested_run_directories_are_created(tmp_path) -> None:
    d = report_route(_route_result(), "a/b/c", mock=True, runs_dir=tmp_path / "deep")
    assert d.is_dir()


# ── sweep ───────────────────────────────────────────────────────────────


def _sweep_points():
    return run_sweep(
        _samples(),
        thresholds=[0.2, 0.6],
        strong_backend=MockBackend("strong"),
        weak_backend=MockBackend("weak"),
        judge=MockJudge(CATALOG),
        strong_model="strong-m",
        weak_model="weak-m",
        policy_factory=lambda t: ClassifierPolicy(threshold=t, catalog=CATALOG),
        pricing=PRICING,
    )


def test_sweep_report_writes_a_csv_for_charting(tmp_path) -> None:
    d = report_sweep(
        _sweep_points(),
        "s-1",
        mock=True,
        strong_model="strong-m",
        weak_model="weak-m",
        runs_dir=tmp_path,
    )
    csv_text = (d / "sweep.csv").read_text(encoding="utf-8")
    assert csv_text.splitlines()[0].startswith("threshold,saved_pct")
    assert len(csv_text.strip().splitlines()) == 3  # header + 2 points


def test_sweep_report_writes_markdown_and_json(tmp_path) -> None:
    d = report_sweep(
        _sweep_points(),
        "s-1",
        mock=True,
        strong_model="strong-m",
        weak_model="weak-m",
        runs_dir=tmp_path,
    )
    assert (d / "report.md").is_file()
    payload = json.loads((d / "result.json").read_text(encoding="utf-8"))
    assert len(payload["points"]) == 2


# ── gateway ─────────────────────────────────────────────────────────────


def test_gateway_report_writes_files_and_names_both_arms(tmp_path) -> None:
    result = run_gateway(
        _samples(), a_backend=MockBackend("proxy"), b_backend=MockBackend("direct"), model="m"
    )
    d = report_gateway(result, "g-1", mock=True, runs_dir=tmp_path)
    md = (d / "report.md").read_text(encoding="utf-8")
    assert (d / "result.json").is_file()
    assert "proxy" in md
    assert "direct" in md


def test_gateway_report_carries_the_small_sample_warning(tmp_path) -> None:
    result = run_gateway(
        _samples(), a_backend=MockBackend("a"), b_backend=MockBackend("b"), model="m"
    )
    d = report_gateway(result, "g-1", mock=True, runs_dir=tmp_path)
    assert "tail percentiles" in (d / "report.md").read_text(encoding="utf-8")
