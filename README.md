# Instar

An open-source harness for measuring LLM workloads — cost, quality, and latency — on your own traffic.

> **Status:** pre-release. v0.1.0 targeted for the end of the two-week sprint starting 2026-07-21. Repo scaffolding is landing now; the first runnable example arrives in Week 2. See [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) for the plan.

## Who it's for

Instar answers one question — *which model mix, which router, for which use case, on my traffic?* — for two kinds of adopter:

- **Teams with in-house engineering** — ML platform, AI enablement, or product-engineering groups — who run Instar against their own workloads directly.
- **Leaders who have the AI question but not the plumbing** — heads of marketing, operations, finance, and other AI-adopting functions — who engage a consulting partner to run it on their behalf. Instar is built by the team at Atelier, Purple Blossom AI's consulting practice, which uses it in that role; the tool is Apache 2.0 and any firm can do the same.

Either path produces the same artifact: evidence grounded in *your* workloads, not vendor benchmarks.

## What it looks like

```bash
$ instar run examples/hello.yaml --mock
[instar] loading workflow: examples/hello.yaml
[instar] providers: anthropic, openai (mock mode)
[instar] policy: cost-quality-classifier
[instar] running 50 requests × 3 routes
[instar] ✓ complete — see reports/hello/index.md
```

The workflow YAML declares the requests, the models and routers to compare, the rubrics to score by, and the reporter to produce. `--mock` means no real API calls — deterministic, hermetic, cheap to run in CI. Drop `--mock` and add credentials to hit real providers.

## Install

```bash
# from source (v0.1)
git clone https://github.com/PurpleBlossomAI/instar
cd instar
pip install -e .
```

PyPI publication is deferred to v0.2 (see [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §14) — `pip install instar` requires committing to a stable API surface we're not ready to promise at v0.1.

Python 3.11+.

## Where to go next

- [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) — the plan: IP boundary, roadmap, sprint, open questions.
- [`Planning/Naming.md`](./Planning/Naming.md) — why "Instar," what off-box verifications are still owed before public announcement.
- Docs site — MkDocs Material scaffold arrives in Week 2; will publish to GitHub Pages under `purpleblossomai.github.io/instar/`.

## What Instar is NOT

- **Not a router.** Production routing is the job of OpenRouter, LiteLLM, Portkey, Kong, and Cloudflare AI Gateway. Instar tells you which routing choices *would* have paid off on your traffic.
- **Not a general eval platform.** Promptfoo, Braintrust, and DeepEval already win on breadth.
- **Not an observability store.** Langfuse, Helicone, Arize, and LangSmith already own trace storage.
- **Not a hosted service.** No SaaS, no dashboard-as-a-product.
- **Not a container for consulting IP.** Per-department rubrics and customer-derived fixtures live in their owners' private repos, not here.

Full anti-scope in [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §1.

## License, contributing, security

- **License:** Apache 2.0. See [`LICENSE`](./LICENSE).
- **Contributing:** `CONTRIBUTING.md` is a Week-1 sprint task and will land shortly. Until then, issues and PRs welcome; only Brian and Prithvi have merge rights at v0.1 (see [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §6).
- **Security:** `SECURITY.md` also lands Week 1. Until then, please email security concerns privately rather than opening a public issue.

## Related

[`github.com/PurpleBlossomAI/gateway-lab`](https://github.com/PurpleBlossomAI/gateway-lab) — Prithvi's parallel experimental space. Not the shipped artifact.
