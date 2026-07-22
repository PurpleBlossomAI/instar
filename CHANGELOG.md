# Changelog

All notable changes to Instar are documented here. This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Instar is in **v0.x** — the API surface is unstable until v1.0.0. Breaking changes may land in any 0.y release; we will call them out in the corresponding `### Changed` or `### Removed` section.

## [Unreleased]

### Added

- **The harness core.** Clean-room port of the internal gateway experiment code into `Engineering/src/instar/`, restructured to the package layout in `Planning/Project-Plan.md` §4:
  - `core/` — `TrafficSample` and JSONL workload fixtures; `FeatureCatalog`; cost math (per-token pricing, prompt-caching model, self-hosting break-even); the routing runner (`run_route`, `run_sweep`); the gateway A/B latency runner (`run_gateway`).
  - `providers/` — `Backend` interface and `CompletionResult`; `MockBackend` (deterministic), `AnthropicBackend` (optional SDK, lazily imported), and `OpenAICompatBackend`.
  - `policies/` — `AllStrongPolicy` (control), `FeatureCategoryPolicy` (rules baseline), `ClassifierPolicy` with a placeholder difficulty scorer and a documented seam for a trained router.
  - `rubrics/` — `LabelMatchJudge` (objective, gold-label), `LLMJudge` (PASS/MARGINAL/FAIL), `AutoJudge` (dispatches per sample), `MockJudge` (deterministic).
  - `reporters/` — `result.json`, Markdown report with per-call decision rows, and `sweep.csv` for charting.
  - `cli/` — `instar route` and `instar gateway`, both defaulting to hermetic mock mode.
- `OpenAICompatBackend` is implemented over `urllib` rather than an SDK, so vLLM, Ollama, LiteLLM, OpenRouter, and OpenAI are all reachable from a stdlib-only install.
- Synthetic, PII-free workload fixtures under `Engineering/fixtures/`: support triage (24 calls, gold labels, objectively scorable), marketing content ops (12, mixed), sales pipeline (10, including a prompt-caching refinement series), and a small mixed smoke sample. Example feature catalogs under `Engineering/fixtures/catalogs/`.
- 203 tests across 10 files, all hermetic. Includes a check that no private product terms leak into the shipped fixtures, enforcing the IP boundary in CI rather than in a reviewer's memory.
- `instar` console-script entry point and an `anthropic` optional-dependency extra.
- `Engineering/Docs/CODE-OVERVIEW.md` (architecture and extension points) and `Engineering/Docs/RUNBOOK.md` (task-oriented, including a walkthrough for measuring your own workload).
- `--strong-url` / `--weak-url` (with matching `--*-key-env`) on `instar route`, so either arm can be any OpenAI-compatible endpoint rather than Anthropic. This is what makes the CLI able to evaluate a self-hosted small model against a frontier baseline. The LLM judge runs on the strong arm.
- Repository scaffolding: `Planning/`, `Engineering/`, `Marketing/`, `CLAUDE.md`, initial README stub.
- Governance files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `SECURITY.md`, `CHANGELOG.md`.
- `pyproject.toml` with setuptools build backend, PEP 639 SPDX license fields, and configuration for `ruff` (lint + format), `mypy --strict`, and `pytest`. Package located at `Engineering/src/instar/` per `CLAUDE.md` §Organization principle.
- Smoke test at `Engineering/tests/test_smoke.py` — verifies the package installs and imports.
- SPDX license headers on all Python source files.
- CI baseline at `.github/workflows/ci.yml`: four parallel jobs — `ruff check` + `ruff format --check`, `mypy --strict`, `pytest -m 'not live'` on Python 3.11/3.12/3.13, and an SPDX-header check. Runs on push to `main` and on pull requests.
- `Planning/Engagement-Methodology.md` — first-draft spine for how Instar fits into a complete LLM evaluation engagement. Names eleven phases (A–K), annotates each with its IP-boundary side (OSS / mixed / private methodology), and frames the process as a loop rather than a line. Companion artifact (`Engineering/docs/How-Instar-Fits-an-Evaluation.md`) planned after the Week-2 code lift; Atelier playbook is a separate, private artifact.
- `Engineering/Introduction.md` — first-pass contributor-facing introduction, written for people Brian is inviting to the project.
- `Marketing/Measuring-Your-AI-Costs.md` — first-pass positioning + evaluation-process primer for leaders. Draft; not for publication until v0.1 gate clears (see `Planning/Naming.md`).

### Changed

- `README.md` rewritten from mission stub to v0.1 shape: two-audience "Who it's for," status callout, install-from-source (PyPI deferred to v0.2), anti-scope, and pointers to `Planning/`. Subsequently corrected to document the CLI that actually exists (`instar route` / `instar gateway` over JSONL workloads) in place of an illustrative YAML interface that was never built.
- The feature-to-category map is now **user-supplied configuration** (`FeatureCatalog`, loaded from JSON) rather than a table baked into the source. An adopter measuring their own marketing or support workload declares their own features; the shipped catalogs are examples. Uncatalogued features default to foreground, so an omission costs money rather than quality, and the CLI names them on stderr.
- Gateway comparison arms are generic and user-specified (`--a-url` / `--b-url`), and calls are interleaved between arms rather than run in blocks, so drift in network or provider conditions cannot be attributed to whichever arm ran second.
- Reports carry their caveats inline — mock banner, failed-call count, unpriced-model warning, and small-sample warnings on tail latency percentiles — because these files get forwarded to people who never ran the tool.

### Removed

- The internal-gateway backend and the curated vendor feature-parity matrix from the source experiment. Both encoded private architecture and neither is runnable or useful outside it. Gateway comparison now measures latency only, on endpoints the user names.

### Deprecated

- *nothing yet*

### Fixed

- Bad input now exits with a message rather than a traceback: a malformed fixture line, an invalid catalog, a missing file, and an uninstalled provider SDK all report cleanly and exit 1.

### Security

- *nothing yet*

<!--
Release template — copy this block above [Unreleased] when tagging a release:

## [X.Y.Z] — YYYY-MM-DD

### Added
### Changed
### Deprecated
### Removed
### Fixed
### Security
-->
