# Changelog

All notable changes to Instar are documented here. This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

Instar is in **v0.x** — the API surface is unstable until v1.0.0. Breaking changes may land in any 0.y release; we will call them out in the corresponding `### Changed` or `### Removed` section.

## [Unreleased]

### Added

- Repository scaffolding: `Planning/`, `Engineering/`, `Marketing/`, `CLAUDE.md`, initial README stub.
- Governance files: `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant v2.1), `SECURITY.md`, `CHANGELOG.md`.
- `pyproject.toml` with setuptools build backend, PEP 639 SPDX license fields, and configuration for `ruff` (lint + format), `mypy --strict`, and `pytest`. Package located at `Engineering/src/instar/` per `CLAUDE.md` §Organization principle.
- Smoke test at `Engineering/tests/test_smoke.py` — verifies the package installs and imports.
- SPDX license headers on all Python source files.
- CI baseline at `.github/workflows/ci.yml`: four parallel jobs — `ruff check` + `ruff format --check`, `mypy --strict`, `pytest -m 'not live'` on Python 3.11/3.12/3.13, and an SPDX-header check. Runs on push to `main` and on pull requests.

### Changed

- `README.md` rewritten from mission stub to v0.1 shape: two-audience "Who it's for," status callout, install-from-source (PyPI deferred to v0.2), anti-scope, and pointers to `Planning/`.

### Deprecated

- *nothing yet*

### Removed

- *nothing yet*

### Fixed

- *nothing yet*

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
