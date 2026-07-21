# Security policy

## Reporting a vulnerability

**Do not open a public GitHub issue for a security concern.** Instead, email:

**brianfromme@gmail.com** with `[Instar SECURITY]` in the subject line.

*This is a temporary contact for the pre-v0.1 phase. Before the v0.1.0 tag it will move to a dedicated `security@` alias — see [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §9.*

We aim to acknowledge within seven days and to get a fix and disclosure timeline back to you within 30. Default disclosure window is **90 days coordinated** — longer if you need it, shorter if the class of issue justifies it.

## Scope

In scope:

- Any bug in code shipped from this repository.
- Any credential-handling weakness in the harness itself (API keys leaking via logs, reports, fixtures, or reproducibility artifacts).
- Any workflow that could lead a user to accidentally publish sensitive data.

Out of scope:

- Vulnerabilities in third-party providers (Anthropic, OpenAI, Google, vLLM, OpenRouter, LiteLLM). Report those to the provider.
- Vulnerabilities in [`github.com/PurpleBlossomAI/gateway-lab`](https://github.com/PurpleBlossomAI/gateway-lab). Separate repo; report there.
- Weaknesses inherent to running LLM workloads (prompt injection, jailbreaks against a target model). Those are the target's problem, not Instar's.

## What we ask

- Give us reasonable time to respond before publicly disclosing.
- Don't test against systems you don't own or don't have permission to test.
- Don't exfiltrate data beyond what's needed to demonstrate the issue.

## What we won't do

- Pursue researchers who act in good faith.
- Run a bug bounty program (not yet — may reconsider post-v1).

## Supported versions

Pre-v0.1: only `main`. Once v0.1.0 ships, we will support the latest minor version for security fixes. This section will be revised at v0.1.0 release.

## No secrets in the repo

Instar never ships secrets. We enforce this with:

- `detect-secrets` via `pre-commit` (Week-1 sprint task).
- GitHub secret scanning enabled at the org level.
- Dependabot alerts enabled.

If you find a committed secret, report it via the process above and we will rotate.

## Broader security posture

See [`Planning/Project-Plan.md`](./Planning/Project-Plan.md) §9 for the design intent behind this file.
