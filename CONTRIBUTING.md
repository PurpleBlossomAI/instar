# Contributing to Instar

Thanks for your interest. This document explains how to contribute effectively during Instar's early stages — what's welcome, what isn't, and how to file issues and PRs we can act on.

**Status:** Instar is pre-v0.1 as of 2026-07-21. Merge rights are deliberately limited to Brian Fromme and Prithvi Devraj through v0.1. Issues and PRs from anyone are welcome; the review cadence is deliberate. See [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §6 for the contribution model in full.

## Before you contribute

Please read:

- [`README.md`](./README.md) — what Instar is, what it isn't, who it's for.
- [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §1 — the anti-scope. If you're proposing something we've said Instar is NOT, we will decline.
- [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §2 — the IP boundary (also summarized below).
- [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md) — Contributor Covenant v2.1. Participating in Instar means agreeing to it.

## What belongs here, what doesn't

Instar is Apache-2.0 OSS. It contains:

- The harness core (run definitions, workflow replay, cost accounting).
- Provider adapters (Anthropic, OpenAI, Google, vLLM, OpenRouter, LiteLLM).
- The routing-policy *interface* and a small number of reference policies.
- The rubric *framework* (how to define and score with an LLM judge), plus one or two illustrative rubrics.
- Reporters (JSON, Markdown, CSV, simple HTML).
- Public synthetic fixtures, PII-free, and docs on how to build your own.
- Reproducibility scaffolding: mock mode, seeded runs, model-ID pinning, CI.

Instar does **not** contain, and PRs adding these will be declined:

- **Per-department or per-customer rubrics.** Marketing brand-voice, Finance extraction, Ops p95-latency rubrics — those are consulting methodology and belong in each firm's private repo. Instar ships a framework; you supply the rubrics.
- **Customer-derived workload fixtures.** Anonymize thoroughly, or better, contribute a synthetic fixture and describe the shape.
- **Methodology write-ups tied to a specific engagement.** SOWs, playbooks, engagement templates — private-repo material.
- **Router replacements.** Instar measures router choices; it does not decide production requests. See [`README.md`](./README.md) §"What Instar is NOT".
- **Observability / trace-storage features.** Langfuse, Helicone, Arize, LangSmith already own that space.
- **Hosted-service scaffolding.** Instar has no SaaS product roadmap.

If a PR is close to the line, open an issue first and describe the intent — we'll tell you which side of the boundary it falls on before you invest.

## Filing issues

Small changes and clear bugs: open an issue. Use the issue templates in `.github/ISSUE_TEMPLATE/` once they land (Week-1 sprint task).

Labels we use (see [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §5):

- `type:` — `feature`, `bug`, `docs`, `provider-adapter`, `policy`, `rubric-framework`, `chore`
- `priority:` — `now`, `soon`, `later`
- `good-first-issue` — bounded, well-specified, no repo-wide context required
- `help-wanted` — anything we would accept a contribution on
- `blocked-by-methodology` — visible flag when something would require exposing private IP

## RFCs

Any change touching the harness API surface, the providers interface, or the routing-policy interface needs a short RFC.

Process:

1. Draft an RFC as `Engineering/docs/rfcs/NNNN-title.md` (`NNNN` = next unused four-digit number).
2. Open a PR with just the RFC. Discussion in review.
3. When accepted, the RFC merges. Implementation PRs reference it.

Everything else — bug fixes, provider bug patches, new fixtures, docs — an issue and PR are enough.

## Opening a PR

**Branching.** Never commit to `main`. Cut a feature branch: `<short-topic>-NN` (e.g., `openai-adapter-01`). Rebase on `main` before opening the PR if it's been a while.

**DCO sign-off.** Every commit must be signed off:

```bash
git commit -s -m "..."
```

The `-s` flag appends a `Signed-off-by:` trailer certifying you have the right to submit the contribution under the project license. Read the [Developer Certificate of Origin](https://developercertificate.org/) for what you're agreeing to. We use DCO instead of a CLA to keep the process light — see [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §6.

**PR checklist** (also enforced by the PR template):

- [ ] Tests pass in mock mode (`pytest -m 'not live'`).
- [ ] `ruff` clean.
- [ ] `mypy --strict` clean on `Engineering/src/`.
- [ ] `CHANGELOG.md` updated under `[Unreleased]` for `type:feature` or breaking changes.
- [ ] License header (SPDX) on every new source file.
- [ ] All commits signed off.
- [ ] Anything in the "does not belong here" list above? If close, note it and explain.

## Development setup

*Placeholder — the code lands in Week 2 of the two-week sprint starting 2026-07-21. This section will be filled in with clone / install / test-run instructions at that point. See [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §10.*

## Review cadence

At v0.1:

- Only Brian Fromme and Prithvi Devraj have merge rights.
- We aim to acknowledge PRs within seven days. Merging can take longer, especially in areas under active design.
- If your PR has been quiet for 14 days, ping it — that's fair.

The ladder past v0.1 is implicit: consistent quality PRs earn triage rights, then merge rights on specific areas. We'll formalize once someone earns it.

## Reporting security issues

Do **not** open a public issue for a security concern. See [`SECURITY.md`](./SECURITY.md) for the disclosure process.

## Reporting Code of Conduct issues

See [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md) §Enforcement.

## Questions

Open a `type:docs`-labeled issue. GitHub Discussions may be enabled later; watch for a note in `CHANGELOG.md` when it happens.
