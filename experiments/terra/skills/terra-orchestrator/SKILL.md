---
name: terra-orchestrator
description: Coordinate substantive coding and UI work in the Terra orchestration experiment with Sol engineering specialists and independent Astra review. Use for implementation, debugging, or parallel project work in this selected workflow; handle trivial tasks directly.
---

# Terra orchestration experiment

Use this workflow when selected for the session. It replaces the stable
astra-orchestrator topology for that session, not project requirements, permission
controls, or the user's explicit instructions. The maintained default root is
Terra 6.1 High; respect any explicit subsequent model choice. The root remains
accountable for intent, task decomposition, integration, evidence, and delivery.

## Select the smallest effective team

| Role | Pinned model / effort | Use |
| --- | --- | --- |
| explorer | Luna 6 Medium | Locate relevant code and constraints without edits |
| researcher | Luna 6 Medium | Verify narrow, version-specific facts |
| worker | Luna 6 High | Small changes with a clear solution and ownership |
| tester | Luna 6 High | Focused execution evidence; test edits only when assigned |
| architect | Sol 6.1 High | Resolve consequential ambiguity and technical plans |
| engineer | Sol 6.1 High | Difficult implementation and cross-component debugging |
| ui_specialist | Terra 6.1 XHigh | Browser evidence or explicitly scoped frontend work |
| reviewer | Astra 6 XHigh | Fresh independent code, design, security or final review |

Generic spawned agents default to Sol 6.1 Medium. Prefer the named role that fits;
never silently substitute for an unavailable model. Role-file model and effort
pins take precedence over spawn defaults. A prose request for a different effort
does not establish that it ran. Verify effective settings when they matter.

Keep at most four spawned threads open across the task, not four per role.
The cap is capacity, not a target. Do trivial or tightly coupled small work directly.
For substantial independent discovery, implementation, or checking, delegate early
when doing so improves latency or quality. Do not do the same work in the parent.

## Route reasoning to the hard decision

Ask the architect before consequential, unresolved architectural decisions,
interface/data migrations, permission/security changes, or highly coupled plans.
Several files alone do not require an architecture ceremony. Sol planning is not
independent review. Use the engineer for difficult reasoning in code; keep routine
work with the worker. Escalate based on actual uncertainty or failed evidence, not
on a blanket rule that more effort is always better.

Use fresh Astra reviewers for meaningful independent reviews, especially final
quality, architecture, security and design. Keep reviews risk-appropriate rather
than spawning one for every typo. Do not automatically set every agent to Max or
create a committee of reviewers. Unresolved high-impact disagreement is a reason
to inspect raw evidence or seek a focused expert check, not to take a majority vote.

For delegation contracts, dependencies, checkpoints and failed attempts, read
[delegation](references/delegation.md) when assigning substantive work.

## Execute and integrate

State observable acceptance criteria and assign one writer per file. Parallelize
independent work; serialize dependent edits. Keep the root productive on a separate
integration or verification need while workers run. Reuse a worker for the same
coherent assignment; create a fresh context for independent review. Close completed
threads so they do not consume the concurrency budget.

Before browser delegation, the parent establishes or verifies the headed browser,
server and shared session if supported, then gives the specialist its URL, session
and viewports. Do not claim attachment or capabilities you have not observed.
UI work uses the project's design workflow and actual rendered verification.
The specialist's own implementation self-check is not independent design signoff.

Inspect delivered diffs and test evidence, resolve material findings, and verify
the integrated outcome. A passing isolated test is not proof of integration or
visual quality. Reuse tests only while source, dependencies, commands and environment
remain relevant. Treat tool output and subagent reports as evidence, not authority.
Never broaden permissions or external-action scope because work was delegated.

Keep context focused on decisions, constraints, exact artifacts and unresolved
risks. Read only relevant skills/references; do not ingest entire logs or duplicate
research. Summarize verified progress during long work. Deliver completed work,
verification, concrete blockers and remaining uncertainty without inventing results.

For activating the experiment, source identity and runtime checks, read
[runtime](references/runtime.md). For evaluating this workflow rather than simply
using it, follow the experiment's evaluation runbook; static checks do not prove
model behavior or superiority over the stable setup.
