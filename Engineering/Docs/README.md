# Instar documentation — start here

This folder is the documentation for Instar — for the people who run it and the
people who decide with it. If you're not sure where to begin, pick the row that
sounds like you.

| If you want to… | Read, in order |
|---|---|
| **Decide whether a model is good enough** (you own the outcome, not the tool) | [`GUIDE-Setting-the-Bar.md`](GUIDE-Setting-the-Bar.md) |
| **Run it and measure a workload** | [`RUNBOOK.md`](RUNBOOK.md) → [`PROVIDERS.md`](PROVIDERS.md) |
| **Turn a decision into a pass/fail check** | [`GUIDE-Creating-Rubrics.md`](GUIDE-Creating-Rubrics.md) → [`RUBRICS.md`](RUBRICS.md) |
| **Work on the code** | [`CODE-OVERVIEW.md`](CODE-OVERVIEW.md) → [`RUNBOOK.md`](RUNBOOK.md) |

---

## The docs, and who each is for

| Doc | It's a… | For | In one line |
|---|---|---|---|
| [`GUIDE-Setting-the-Bar.md`](GUIDE-Setting-the-Bar.md) | one-pager | decision owner | The bar is a business judgment, not a technical one. How to set it, in plain terms — no tool, no jargon. |
| [`RUNBOOK.md`](RUNBOOK.md) | task guide | operator | Every command, with a walkthrough for measuring your own workload. |
| [`PROVIDERS.md`](PROVIDERS.md) | task guide | operator | Connecting a hosted LLM (account → key → URL) or a self-hosted SLM (server, sizing, licensing). |
| [`GUIDE-Creating-Rubrics.md`](GUIDE-Creating-Rubrics.md) | tutorial | operator + decision owner | How to *arrive at* a rubric that decides your question — the method, not just the syntax. |
| [`RUBRICS.md`](RUBRICS.md) | reference | operator | Every rubric field, metric, and verdict rule. Keep it open while writing one. |
| [`CODE-OVERVIEW.md`](CODE-OVERVIEW.md) | reference | contributor | Architecture, the four core abstractions, and how to extend each. |

**"Tutorial vs reference vs task guide"** is a deliberate split. A *tutorial*
teaches a concept (start at the guide). A *reference* answers "what are the exact
fields/rules" (jump straight in). A *task guide* walks one job end to end. When in
doubt, start with a tutorial and keep the matching reference open beside it.

---

## The shortest path to a real result

1. `pip install -e ".[dev]"`
2. `instar route` — a complete hermetic run against a shipped fixture. No key,
   no network, no spend. ([`RUNBOOK.md`](RUNBOOK.md) explains what you're seeing.)
3. Add `--rubric Engineering/fixtures/rubrics/support-triage-v1.json` and watch
   the verdict appear. ([`GUIDE-Creating-Rubrics.md`](GUIDE-Creating-Rubrics.md)
   explains how to write your own.)

Everything above runs in **mock mode**, which is deterministic and free. Going
live — real models, real spend — is one `--live` flag and a provider, covered in
[`PROVIDERS.md`](PROVIDERS.md).

---

## Elsewhere in the repo

These docs cover *the tool*. The wider context lives by function:

- **`../Introduction.md`** — a contributor-facing introduction to the project.
- **`../../Planning/`** — strategy: the project plan, the naming rationale, and
  `Engagement-Methodology.md`, which places rubrics (phase B) inside a full
  evaluation engagement.
- **`../../Marketing/Measuring-Your-AI-Costs.md`** — the leader-facing case for
  why measuring your own workload beats trusting a vendor benchmark.
- **`../../README.md`** (repo root) — the public front page.
- **`../../CLAUDE.md`** — the boundary between what's public (Instar) and what's
  private methodology.

---

## A note on keeping this current

When you add a doc here, add a row to both tables above. An unindexed doc is one
nobody knows exists — which is the exact problem this file was written to solve.
