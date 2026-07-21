# Naming — Instar

**Decision date:** 2026-07-21
**Decided by:** Brian (theme + shortlist) + Claude (candidates + rubric)
**Status:** Name locked. Off-box verifications listed below are still owed before public announcement.

---

## The name

**Instar.**

In biology, an *instar* is a stage between molts in an insect's development. Two reasons it fits:

1. **What the harness does.** A measurement harness observes the *stage-by-stage progression* of an LLM workload — each provider, each rubric evaluation, each routing decision is a discrete instar in the workload's development. The word maps directly to what the tool measures.
2. **What the tool is for.** The customer story is metamorphosis — organizations *becoming* AI-productive. Instar names a stage in that transformation, which fits the sibling brand (Blossom Grove) without competing with it.

The name was chosen from a shortlist of butterfly/transformation-themed candidates. Full deliberation (Brian's four — Butterfly, Chrysalis, Papillon, Psychí — plus five additions — Instar, Eclosion, Imago, Metamorph, Fledge — scored against a 6-factor rubric) lives in MVP1 at `~/projects/PurpleBlossomAI/MVP1/Docs/Experiments/Harness-Service+Product/Project-Name-Candidates.md`. That file is archival; this one is the operational reference.

---

## Availability sanity-check (done 2026-07-21)

- **GitHub org repo:** `github.com/PurpleBlossomAI/instar` — free (was 404 at check time; now claimed by this repo). ✓
- **AI/dev-tools competitive scan:** no dominant "Instar" in the LLM eval / harness / observability space. Incumbents in the category (DeepEval, Promptfoo, Langfuse, EleutherAI `lm-evaluation-harness`) don't collide. ✓
- **Non-conflict noted:** "Instar Group / Instar Logistics" is a Vancouver-based private-equity infrastructure fund — different industry, class 36 (financial services), extremely unlikely to conflict with an open-source software mark. Worth flagging in a formal trademark search but not a blocker.

---

## Still-to-verify (Brian, off-box)

**Not blocking commits to this repo. Blocking public announcement / PyPI push / tagged release.**

1. **PyPI availability.** Check `pip index versions instar` or [pypi.org/project/instar](https://pypi.org/project/instar/). If taken: fall back to `instar-harness` as the *package* name while keeping `instar` as the project + CLI identity. Confirm before Week-1's `pyproject.toml` task in `Project-Plan.md` §10.
2. **Domain reservation.** `instar.io` and `instar.dev` — reserve via preferred registrar, even if we don't put content up. Cheap insurance against a future squatter.
3. **Formal trademark search.** USPTO TESS quick pass for "Instar" in class 9 (software) and class 42 (computer services). The PE-fund use is class 36 (financial services) — different class, low conflict risk.
4. **Notify Prithvi.** Courtesy heads-up on the name and the fork approach (which is *for* his benefit — protects his continuing `gateway-lab` work).

If any of (1)-(3) come back ugly, stop and reopen the naming decision using the full deliberation in the MVP1 archival doc.

---

## Repo strategy: fork, not rename

Instar was created 2026-07-21 as a **new empty repo** at `~/projects/PurpleBlossomAI/instar` rather than renaming `github.com/PurpleBlossomAI/gateway-lab`. Rationale:

- Prithvi keeps iterating on `gateway-lab` (testing + paper writing) without coordination overhead.
- Instar gets clean Apache-2 provenance from commit 1.
- No shared-state action; nothing about Prithvi's remote or working tree changes.
- Convergence question deferred 30–60 days (see `Project-Plan.md` §Repo relationship).

Consequence: MVP1 references to `gateway-lab` **stay as-is** — they still correctly point to Prithvi's active repo. No sweep needed.

---

## Downstream naming

Once Instar is the accepted name, everything inherits from it:

- **Python package:** `instar` (subject to PyPI availability — see verification #1 above).
- **CLI:** `instar` (`instar run`, `instar bench`, `instar report`).
- **Package path:** `Engineering/src/instar/` (per `../CLAUDE.md` §Organization principle).
- **Docs site URL:** GitHub Pages under `purpleblossomai.github.io/instar/` initially; move to `instar.dev` or `instar.io` once reserved.
- **Announcement copy:** to be drafted in `../Marketing/` in Week 2 of the sprint; do not publish until PyPI + domains + trademark are cleared.
