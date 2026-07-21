# Instar — Claude Context Guide

**Last Updated:** 2026-07-21
**Repo:** `~/projects/PurpleBlossomAI/instar` · GitHub: `PurpleBlossomAI/instar`
**Status:** Freshly created (2026-07-21). Only LICENSE, .gitignore, README, and this Planning/Engineering scaffolding exist. **No code yet.**

---

## What Instar is

Instar is an **open-source LLM measurement harness** (Apache 2.0). It runs a user's own workloads through candidate models, providers, and routing policies, and produces defensible cost/quality/latency numbers — so an organization can decide *which router, which model mix, for which team* on evidence rather than vendor claims.

The name comes from biology — an *instar* is a stage between molts in an insect's development. That fits both the tool's job (measuring the stage-by-stage progression of a workload) and the wider theme (organizations metamorphosing into AI-productive shapes). It's a sibling of the Blossom Grove brand, not a rival to it.

**One-line mission (from README.md):** *"an open-source project to help companies shed their old habits in order to grow and assume a new form of work with AI."*

## What Instar is NOT

- **Not a router.** We do not decide production requests. That's OpenRouter / LiteLLM / Portkey / Kong / Cloudflare AI Gateway territory — a crowded, well-funded space.
- **Not a general eval platform.** Promptfoo / Braintrust / DeepEval already win on breadth.
- **Not an observability/trace store.** Langfuse / Helicone / Arize / LangSmith own that.
- **Not a hosted service.** No SaaS, no dashboard-as-a-product.
- **Not a container for private consulting IP.** Per-department rubrics, workload fixtures derived from customer data, and the methodology write-ups stay in a private Purple Blossom AI repo (see *IP boundary* below).

**Read `Planning/Project-Plan.md` for the full rationale, license reasoning, roadmap model, contribution model, and two-week sprint plan.** This file is orientation; that file is the plan.

---

## Repo state right now

```
instar/
├── CLAUDE.md              # this file
├── LICENSE                # Apache 2.0
├── README.md              # mission stub — full rewrite is a Week-1 sprint item
├── .gitignore
├── Planning/              # by-function: strategy, plan, naming
│   ├── README.md
│   ├── Project-Plan.md    # THE plan; read this second
│   └── Naming.md          # why "Instar" + off-box verifications still owed
├── Engineering/           # by-function: code + engineering notes
│   ├── README.md
│   └── src/instar/
│       └── __init__.py    # empty package placeholder
└── Marketing/             # by-function: positioning, announcements (empty)
    └── README.md
```

Everything else the OSS project needs (CONTRIBUTING.md, CODE_OF_CONDUCT.md, SECURITY.md, CHANGELOG.md, pyproject.toml, .github/workflows/, src code, tests, docs site) is a Week-1 sprint task — see `Planning/Project-Plan.md` §Week-1.

---

## Organization principle: by function, with root-level tooling exceptions

Brian's preference is to organize the repo *by function* — `Engineering/`, `Marketing/`, `Planning/`, and additional functional dirs as needs emerge. Two honest exceptions:

1. **Governance/tooling files must live at the repo root**, because GitHub and Python tooling look for them there:
   - `README.md`, `LICENSE`, `.gitignore` (GitHub display + git)
   - `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md` (GitHub renders these as special files with links from the repo sidebar; moving them under `Planning/` would break that)
   - `.github/` for Actions workflows and issue/PR templates (required at root)
   - `pyproject.toml` (Python packaging convention; can technically be elsewhere with configuration, but root is what every tool expects)
   - `CLAUDE.md` (this file, at root by convention for Claude Code)
2. **The Python `src/instar/` tree lives under `Engineering/`.** The `pyproject.toml` at root will reference `Engineering/src/instar` as the package location via `[tool.setuptools.packages.find]` (or the equivalent for whichever build backend we pick). This is slightly non-standard but supported by every modern Python packager; the by-function organization wins.

When something new comes up that doesn't obviously fit, ask: is it *governance/tooling* (root) or *work* (by-function dir)?

---

## Where to look first

1. `README.md` — the public face; currently a mission stub.
2. `Planning/Project-Plan.md` — the plan. IP boundary, license, sprint, roadmap, contribution model.
3. `Planning/Naming.md` — why Instar, what verifications are still owed off-box.
4. `Engineering/README.md` — what lives in Engineering and the src layout note.

---

## Repo relationship: Instar and gateway-lab

There is a **sibling repo** at `github.com/PurpleBlossomAI/gateway-lab`. That is **Prithvi's** experimental space (testing, paper writing). Instar is Brian's new, curated, packaged, adoptable OSS artifact — created 2026-07-21 as an empty repo rather than renaming gateway-lab, so Prithvi's work isn't disturbed.

**Rules:**
- Instar does not fork gateway-lab's git history. Any code lift is clean-room re-implementation (both repos are internal PurpleBlossomAI work, so there's no license contamination question, but keeping histories separate keeps the story simple).
- Do **not** push commits to gateway-lab from this repo. Prithvi owns it.
- Do **not** conflate them in issues, PRs, or docs. They serve different audiences.
- Convergence question (do the repos eventually merge? does one retire?) is deliberately deferred 30–60 days. See `Planning/Project-Plan.md` §Repo relationship.

---

## IP boundary — what belongs here vs. what stays private

Instar is Apache 2.0 and adoptable. The *methodology* that makes Instar useful in a consulting engagement is private. Rough split:

| Lives here (Instar OSS) | Lives in private Purple Blossom AI repo (MVP1) |
|---|---|
| Harness core, provider adapters, routing policy interface, rubric framework, reporters | Per-department rubrics (Marketing brand voice, Finance extraction, Ops p95 latency, etc.) |
| Public synthetic fixtures + docs on building your own | Customer-derived workload fixtures |
| 2–3 reference routing policies (rules + cost/quality classifier) | Customer-specific routing recommendation logic |
| Reproducibility scaffolding (mock mode, seeded runs, model-ID pinning, CI) | Cost-experiment methodology write-ups, SOW templates, engagement playbooks |

Enforcement:
- Every PR reviewer holds this line. If a PR would leak methodology or customer-derived fixtures, it doesn't merge.
- CONTRIBUTING.md (when written) will spell this out in words a contributor will read.
- If in doubt: default to *not* in Instar; propose it in MVP1's `Docs/Experiments/Harness-Service+Product/` instead.

Details: `Planning/Project-Plan.md` §IP boundary.

---

## Git workflow

Standard feature-branch flow:

1. **Never commit directly to `main`. Never make code changes while on `main`.** If you land here on `main`, create a branch first.
2. Branch naming: `<short-topic>-NN` (e.g., `readme-rewrite-01`, `governance-files-01`).
3. Commit → push → merge to main → delete branch is the normal default on a dev box. Only pause for a PR review if a change is risky (cross-cutting, security-sensitive, infra).
4. Every commit message ends with the standard `Co-Authored-By: Claude ...` trailer.

---

## How Brian likes to work

Compact context so you don't relearn it. Detail lives in MVP1's memory system (`/home/fromme/.claude/projects/-home-fromme-projects-PurpleBlossomAI-MVP1/memory/`); this is a portable subset.

- **Distillation first, depth second.** Lead every non-trivial doc with a one-paragraph or card-shaped TL;DR. Layers below it are fine.
- **Surface gaps in the framing.** On planning/scope tasks, name what's missing from Brian's list, not just sort what he gave you.
- **Pair-author, don't assign homework.** Co-work on artifacts in one session. Don't structure plans as "your part / my part" that reads as homework.
- **Offload cognitive load by proposing scope cuts.** Solo founder is plate-full — actively propose deferrals, don't just execute faster.
- **Push back on naming/framing that contradicts his own point.** Placeholder names or framings that encode what he just said the product *isn't* should be challenged with alternatives.
- **Security/audit and review findings — three buckets:** resolve-now / file-as-backlog / accept-as-residual. Bounded certainty is the goal.
- **Careful actions.** For hard-to-reverse or shared-state actions (force pushes, repo renames, deleting branches, publishing to PyPI, public announcements), pause and confirm. Never assume prior authorization carries.
- **Brian is a creator/dreamer.** Creative breakouts mid-tactical work are fuel, not distraction — honor them, then return cleanly.

---

## What NOT to do here

- Do not push to `PurpleBlossomAI/gateway-lab` (Prithvi's repo).
- Do not create files in this repo that belong in MVP1 (customer engagements, private rubrics, MVP1 backlog tickets, etc.).
- Do not publish to PyPI, tag a release, or make public announcements until the off-box verifications in `Planning/Naming.md` §Still-to-verify are complete.
- Do not delete or restructure `Engineering/src/instar/` without checking `Planning/Project-Plan.md` first — the layout is deliberate.
- Do not add a docs domain, blog, Discord, or telemetry before v0.2. Explicitly deferred (see Project-Plan §Documentation surface).
- Do not add trailing summaries to end-of-turn responses. State what changed and what's next, briefly.

---

## Provenance and full historical context

The design conversation that led to this repo lives in the MVP1 sibling repo at `~/projects/PurpleBlossomAI/MVP1/Docs/Experiments/Harness-Service+Product/`. Read those docs (Harness-Service+Product-Discussion.md, OSS-Project-Plan.md, Project-Name-Candidates.md) if you need the full "why" beyond what's captured here and in `Planning/`.

That MVP1 tree is authoritative for *strategy and market context*; this repo is authoritative for *the OSS project itself*.
