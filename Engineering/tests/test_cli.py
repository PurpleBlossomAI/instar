# SPDX-License-Identifier: Apache-2.0
"""The CLI end to end, in mock mode: no keys, no network, no spend."""

import json
from pathlib import Path

import pytest

from instar.cli.main import build_parser, main

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES = REPO_ROOT / "Engineering" / "fixtures"
SAMPLE = FIXTURES / "sample-traffic.jsonl"
CATALOG = FIXTURES / "catalogs" / "example-departments.json"


def _run(args: list[str], tmp_path: Path) -> int:
    return main([*args, "--runs-dir", str(tmp_path)])


def test_parser_requires_a_subcommand() -> None:
    with pytest.raises(SystemExit):
        build_parser().parse_args([])


def test_route_runs_and_writes_a_report(tmp_path: Path) -> None:
    code = _run(["route", "--traffic", str(SAMPLE), "--catalog", str(CATALOG)], tmp_path)
    assert code == 0
    d = tmp_path / "route-feature_category-mock"
    assert (d / "report.md").is_file()
    assert (d / "result.json").is_file()


@pytest.mark.parametrize("policy", ["all_strong", "feature_category", "classifier"])
def test_every_policy_runs_from_the_cli(policy: str, tmp_path: Path) -> None:
    code = _run(
        ["route", "--traffic", str(SAMPLE), "--catalog", str(CATALOG), "--policy", policy],
        tmp_path,
    )
    assert code == 0
    assert (tmp_path / f"route-{policy}-mock" / "result.json").is_file()


def test_the_control_policy_saves_nothing(tmp_path: Path) -> None:
    _run(["route", "--traffic", str(SAMPLE), "--policy", "all_strong"], tmp_path)
    payload = json.loads(
        (tmp_path / "route-all_strong-mock" / "result.json").read_text(encoding="utf-8")
    )
    assert payload["cost"]["saved_usd"] == 0.0


def test_a_catalog_unlocks_real_routing(tmp_path: Path) -> None:
    """Without a catalog nothing is background, so nothing can be routed weak."""
    _run(["route", "--traffic", str(SAMPLE), "--label", "no-cat"], tmp_path)
    _run(["route", "--traffic", str(SAMPLE), "--catalog", str(CATALOG), "--label", "cat"], tmp_path)
    without = json.loads((tmp_path / "no-cat" / "result.json").read_text(encoding="utf-8"))
    with_cat = json.loads((tmp_path / "cat" / "result.json").read_text(encoding="utf-8"))
    assert without["weak_count"] == 0
    assert with_cat["weak_count"] > 0


def test_sweep_writes_a_curve(tmp_path: Path) -> None:
    code = _run(
        [
            "route",
            "--traffic",
            str(SAMPLE),
            "--catalog",
            str(CATALOG),
            "--sweep",
            "0.2,0.5,0.8",
        ],
        tmp_path,
    )
    assert code == 0
    d = tmp_path / "route-sweep-mock"
    payload = json.loads((d / "result.json").read_text(encoding="utf-8"))
    assert [p["threshold"] for p in payload["points"]] == [0.2, 0.5, 0.8]
    assert (d / "sweep.csv").is_file()


def test_sweep_rejects_a_non_numeric_threshold(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="comma-separated"):
        _run(["route", "--traffic", str(SAMPLE), "--sweep", "0.2,abc"], tmp_path)


def test_a_custom_pricing_table_is_honored(tmp_path: Path) -> None:
    pricing = tmp_path / "pricing.json"
    pricing.write_text(json.dumps({"mock-strong": [100.0, 500.0]}), encoding="utf-8")
    _run(
        ["route", "--traffic", str(SAMPLE), "--pricing", str(pricing), "--policy", "all_strong"],
        tmp_path,
    )
    payload = json.loads(
        (tmp_path / "route-all_strong-mock" / "result.json").read_text(encoding="utf-8")
    )
    # mock-weak is absent from the custom table, so the run warns rather than
    # silently costing those calls at zero.
    assert any("no pricing" in w for w in payload["warnings"])


def test_a_custom_label_names_the_run_directory(tmp_path: Path) -> None:
    _run(["route", "--traffic", str(SAMPLE), "--label", "my-run"], tmp_path)
    assert (tmp_path / "my-run" / "report.md").is_file()


def test_a_missing_fixture_fails_loudly(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="not found"):
        _run(["route", "--traffic", str(tmp_path / "nope.jsonl")], tmp_path)


def test_a_malformed_fixture_reports_a_message_not_a_traceback(tmp_path: Path) -> None:
    """A typo on line 3 of a fixture is user error; it should read like one."""
    bad = tmp_path / "bad.jsonl"
    bad.write_text('{"id":"a","feature":"f","messages":[]}\nnot json\n', encoding="utf-8")
    with pytest.raises(SystemExit, match=":2:"):
        _run(["route", "--traffic", str(bad)], tmp_path)


def test_a_malformed_catalog_reports_a_message(tmp_path: Path) -> None:
    bad = tmp_path / "bad.json"
    bad.write_text('{"categories": {"a.b": "sideways"}}', encoding="utf-8")
    with pytest.raises(SystemExit, match="sideways"):
        _run(["route", "--traffic", str(SAMPLE), "--catalog", str(bad)], tmp_path)


def test_route_can_point_an_arm_at_an_openai_compatible_endpoint() -> None:
    """The self-hosted-small-model case: the weak arm must be reachable by URL."""
    from instar.cli.main import _live_backend
    from instar.providers.anthropic import AnthropicBackend
    from instar.providers.openai_compat import OpenAICompatBackend

    weak = _live_backend("weak", "http://localhost:8000", "MY_KEY")
    assert isinstance(weak, OpenAICompatBackend)
    assert weak.endpoint == "http://localhost:8000/v1/chat/completions"
    assert isinstance(_live_backend("strong", None, None), AnthropicBackend)


def test_route_accepts_the_provider_url_flags() -> None:
    args = build_parser().parse_args(
        ["route", "--weak-url", "http://localhost:8000", "--weak-key-env", "K"]
    )
    assert args.weak_url == "http://localhost:8000"
    assert args.weak_key_env == "K"


def test_gateway_runs_and_writes_a_report(tmp_path: Path) -> None:
    code = _run(["gateway", "--traffic", str(SAMPLE)], tmp_path)
    assert code == 0
    payload = json.loads((tmp_path / "gateway-mock" / "result.json").read_text(encoding="utf-8"))
    assert payload["a"]["backend"] == "arm-a"
    assert payload["b"]["backend"] == "arm-b"


def test_gateway_arms_can_be_named(tmp_path: Path) -> None:
    _run(
        ["gateway", "--traffic", str(SAMPLE), "--a-name", "litellm", "--b-name", "direct"],
        tmp_path,
    )
    payload = json.loads((tmp_path / "gateway-mock" / "result.json").read_text(encoding="utf-8"))
    assert payload["a"]["backend"] == "litellm"


def test_gateway_repeats_multiply_the_workload(tmp_path: Path) -> None:
    _run(["gateway", "--traffic", str(SAMPLE), "--repeats", "5"], tmp_path)
    payload = json.loads((tmp_path / "gateway-mock" / "result.json").read_text(encoding="utf-8"))
    assert payload["n"] == 50


def test_live_gateway_requires_both_urls(tmp_path: Path) -> None:
    with pytest.raises(SystemExit, match="a-url"):
        _run(["gateway", "--traffic", str(SAMPLE), "--live", "--a-url", "http://x"], tmp_path)
