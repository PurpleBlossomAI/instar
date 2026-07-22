# Engagement Methodology

> **TL;DR:** A serious LLM cost/quality evaluation isn't one measurement — it's an eleven-phase process (A–K) that starts with framing the business decision and ends with monitoring the deployed choice. Instar is the tool for phases G–I (measure, analyze, report). The other phases are consulting judgment. The process is a loop, not a line: discovery in later phases often sends you back to earlier ones. This document is the shared spine; the private Atelier playbook holds the fillings.

**Status:** first draft, 2026-07-22. Spine to be refined as engagements produce feedback.

---

## What this document is (and isn't)

**Is:** the shared vocabulary and structural map for how Instar fits into a complete LLM measurement engagement. It names each phase, defines what "done" looks like, and annotates which phases are supported by the OSS tool (Instar), which are private consulting methodology (Atelier), and which are mixed.

**Isn't:**

- Not a step-by-step playbook. The playbook — how Atelier actually executes phases A, D, F, J, K, with SOW templates, per-vertical variations, and decision-facilitation scripts — lives in the private Purple Blossom AI repo. See §"What lives where."
- Not a project management framework. The phases describe the *substantive* work of an evaluation, not the calendar or the Gantt chart.
- Not an Instar architecture doc. That's a companion artifact focused on phases G–I; see §Related.

**Audiences:** Instar contributors deciding where their work fits; customers deciding whether to engage; consultants (Atelier or otherwise) using Instar for their own engagements. All three benefit from a public spine.

---

## The loop, not the line

Phases flow generally in order A → K, but a real engagement is a loop. Discovery in phase H (analysis) or I (reporting) routinely invalidates assumptions from A, B, or C — the classic *"the workload was actually three workloads"* moment. A methodology that treats loops as failure produces bad reports; one that treats loops as expected produces good ones.

Common back-edges:

- H → B: analysis reveals the quality dimensions you defined don't capture what matters.
- H → C: analysis reveals the workload sample missed the tail behavior that dominates cost.
- I → A: reporting reveals the customer's real decision is different from the one you scoped.
- K → G: operational drift triggers re-measurement.

When a loop happens, name it out loud. The engagement isn't off-track; it's doing its job.

---

## Phase summary

| # | Phase | IP boundary |
|---|-------|-------------|
| A | Business framing | Private methodology |
| B | Requirements: dimensions + thresholds | Mixed |
| C | Workload characterization | Mixed |
| D | Candidate selection | Private methodology |
| E | Candidate provisioning | Mixed |
| F | Experimental design | Private methodology |
| G | Measurement execution | **Instar core** |
| H | Analysis | Mixed |
| I | Reporting | Mixed |
| J | Recommendation & decision facilitation | Private methodology |
| K | Operationalization & re-measurement | Private (uses Instar) |

*Mixed* = Instar provides the framework, format, or tooling; the specifics per engagement (rubrics, fixtures, credentials, per-audience framing) live with the consultant or the customer.

---

## Phase details

### A. Business framing — *private methodology*

Name the decision the customer is trying to make and the person accountable for it. Without this, everything downstream drifts — you can measure five things well and still miss what the customer needed.

**Done looks like:** a written statement of the decision, the business KPI it moves, and the stakeholder who signs off. If you can't produce all three in one paragraph, the engagement isn't ready to move to B.

### B. Requirements: dimensions + thresholds — *mixed*

Split into two artifacts. (a) *Quality dimensions* — what "good" means for this workload, expressed specifically enough that an LLM judge can score consistently. Instar's rubric framework supports the definition. (b) *Quality thresholds* — the SLOs the chosen configuration must meet on each dimension. Thresholds are business decisions, not measurement decisions, and usually come from a different stakeholder than dimensions do.

**Done looks like:** a rubric spec Instar can execute, plus a threshold table signed off by the phase-A stakeholder.

### C. Workload characterization — *mixed*

Two sub-steps. (a) Characterize the traffic — volume shape, request-type distribution, seasonality, tail behavior. (b) Derive representative fixtures — a replayable, anonymized set of requests that stand in for the real distribution. Instar defines the fixture format and provides synthetic examples; the actual customer-derived fixtures stay in the private engagement, never in the OSS repo.

**Done looks like:** a fixture set that reproduces the customer's real traffic-type distribution within a defensible tolerance, plus notes on what was left out and why.

### D. Candidate selection — *private methodology*

Which routers, models, and policies enter the comparison? A defensible selection names three things per candidate: cost tier, use-case fit, org constraints (data residency, provider ToS, existing procurement). Always include an *incumbent* candidate so the customer can see whether staying put is defensible.

**Done looks like:** a shortlist of 2–4 candidates, each with a one-paragraph justification.

### E. Candidate provisioning — *mixed*

"Install" is one path (self-hosted vLLM); others are API-key wiring, OpenRouter or LiteLLM config, provider-specific SSO. Instar ships provider adapters; the credentials, network config, and rate-limit negotiations are per-engagement. This phase is often the most time-consuming and rarely the most visible — plan accordingly.

**Done looks like:** every candidate is reachable from the harness runner, with credentials in the customer's secret store and adapter config in version control.

### F. Experimental design — *private methodology*

Sample size, seed pinning, run count, retry policy, error taxonomy, rate-limit handling. This phase is what makes the measurement defensible — if a CFO asks "what if you'd run it Monday morning instead of Friday night," you need an answer that isn't a shrug.

**Done looks like:** a written experimental protocol reviewable by someone who wasn't in the room, plus mock-mode dry-runs that validate the protocol executes end-to-end.

### G. Measurement execution — *Instar core*

Run the harness. Mock-mode dry-runs first, then live runs against real providers. This is what Instar does.

**Done looks like:** captured measurements plus complete provenance — model IDs, timestamps, seeds, error logs — sufficient to re-run the experiment months later.

### H. Analysis — *mixed*

Turn measurements into comparisons: Pareto frontier, dominance judgments, per-dimension quality distributions, cost curves, latency profiles. Instar ships analysis primitives; the interpretation ("this candidate dominates on cost with equal quality *for this subset*") is engagement judgment.

**Done looks like:** a written analysis identifying dominant candidates, per-dimension winners, ambiguous trade-offs, and open questions the data can't resolve.

### I. Reporting — *mixed*

Format is audience-specific. CFO report leads with cost and risk; ML team report leads with implementation and trade-offs; exec summary leads with recommendation and confidence. Same analysis, three artifacts. Instar ships reporter templates; per-audience framing is engagement judgment.

**Done looks like:** the artifacts the phase-A stakeholder needs to reach a decision.

### J. Recommendation & decision facilitation — *private methodology*

The report is not the decision. Helping the customer *reach* the decision is the value-add: which candidate to recommend, how to frame trade-offs the report can't resolve, and how to run the meeting where the decision actually gets made. Instar does not help here.

**Done looks like:** a signed-off decision by the phase-A stakeholder, with a written rationale that references the report.

### K. Operationalization & re-measurement — *private methodology (uses Instar)*

Deploy the decision — routing config changes, provider onboarding, quality-drift monitoring. Schedule the next measurement (quarterly, or per major model release). Without this phase, the engagement produces a slide deck, not a change in how the customer runs their AI operations.

**Done looks like:** the decision is in production, drift monitoring is live, and the next measurement is on the calendar.

---

## Cross-cutting: data governance

PII handling, provider terms of service, data residency, retention policies. Touches phases B (what's in scope), C (what fixtures we can build), E (which providers are allowed), G (what gets logged). Best treated as a checklist gate on each phase, not a phase of its own. A governance failure in any of those phases is a stop-work event, not a soft warning.

---

## What lives where

- **This repo (`instar`), `Planning/Engagement-Methodology.md`** — this document. The shared spine. Public.
- **This repo, forthcoming `Engineering/docs/How-Instar-Fits-an-Evaluation.md`** — customer-facing companion; walks through a canonical evaluation using the phase vocabulary and shows where Instar does the work. Depends on the Week-2 code lift so it can show real CLI examples. Public.
- **Private Purple Blossom AI repo, Atelier engagement playbook** — the fillings for phases A, D, F, J, K, plus specifics for the mixed phases (Atelier's rubric templates, per-vertical fixture patterns, decision-facilitation scripts, SOW templates, engagement postmortems). Private.
- **Codebase IP boundary** — see [`Project-Plan.md` §2](./Project-Plan.md). That table covers *what code and fixtures* belong where; this document covers *what engagement work* belongs where. Complementary, not redundant.

Any consultancy adopting Instar can build its own playbook against this spine. That's a feature, not a leak — Instar's value is the tool; Atelier's value is the depth of the doing.

---

## Related

- [`README.md`](../README.md) — what Instar is at a glance.
- [`Project-Plan.md`](./Project-Plan.md) §1 (anti-scope), §2 (IP boundary), §7 (documentation surface).
- [`Naming.md`](./Naming.md) — why "Instar" (an *instar* is a developmental stage; each phase in this methodology is one, in a sense).
- Forthcoming: `Engineering/docs/How-Instar-Fits-an-Evaluation.md`.

---

*This document is a first draft, 2026-07-22. It will evolve as engagements produce feedback on which phases were fuzzy, which loop-backs happened, and which cross-cutting concerns got underweighted. Updates are welcome via PR from Atelier consultants and external adopters alike.*
