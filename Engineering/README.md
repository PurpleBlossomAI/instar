# Engineering

Code, tests, examples, fixtures, docs source, and engineering notes for Instar. This is where the harness gets built and where design decisions about *how* to build it get recorded.

## Contents (target)

Most of this is placeholder as of 2026-07-21 — see `../Planning/Project-Plan.md` §10 for the two-week sprint that fills it in.

- **`src/instar/`** — the Python package. Layout: `core/`, `providers/`, `policies/`, `rubrics/`, `reporters/`, `cli/`. See Project-Plan §4 for the module split.
- **`fixtures/`** — synthetic, PII-free workload fixtures used by examples and tests. Customer-derived fixtures stay in the private repo (see IP boundary).
- **`examples/`** — runnable end-to-end walkthroughs. `instar run examples/hello.yaml` in `--mock` mode is the v0.1 "proof of life."
- **`tests/`** — `pytest`. Mock-mode always green; live-provider tests behind a marker and skipped without secrets.
- **`docs/`** — MkDocs Material source. Published to GitHub Pages. Scaffolded in Week 2 of the sprint.

## Src layout note

The Python package lives at `Engineering/src/instar/` — not at the repo root. `pyproject.toml` (Week-1 sprint task, at the repo root) points its build backend at this path. This is deliberate; see `../CLAUDE.md` §Organization principle for why by-function organization wins over Python-convention.

## Not in this directory

- Governance/tooling files (`pyproject.toml`, `.github/`, `CONTRIBUTING.md`, etc.) live at repo root — GitHub and Python tooling expect them there.
- Strategy, plan, roadmap, naming decisions — those live in `../Planning/`.
- Positioning, announcement drafts, external comms — those live in `../Marketing/`.

## IP boundary reminder

Everything committed here is Apache 2.0 and adoptable by anyone. Per-department rubrics, customer-derived fixtures, and methodology write-ups **do not belong here** — they live in the private Purple Blossom AI repo. See `../CLAUDE.md` §IP boundary and `../Planning/Project-Plan.md` §2. Every PR reviewer holds this line.
