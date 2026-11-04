---
name: terra-orchestrator
description: Route substantive coding and UI work to the Terra workflow's named specialists. Assign distinct deliverables, reuse owners across turns, and keep small edits with the root.
---

# Terra orchestration

The root owns intent, decomposition, integration, verification, and delivery. Use the
selected root model. The Terra bundle defaults to Terra 6.1 High. Delegate through
the bundled named roles and use the model and effort pinned in each role file.
Follow the user's scope, project requirements, and existing permissions.

## Route the next deliverable

At task entry and each material scope change, identify the next concrete deliverable.
For substantive work that matches a named role, delegate before starting the work
and briefly state the role and assignment. Keep small known edits and inseparable
small tasks with the root. Honor explicit requests for independent review, test
execution, or delegation.

If a fitting role or capability is unavailable, delegation is outside the user's
scope, or the work cannot be separated safely, state the exception and complete
the useful work within the root's scope. Report any required specialist check that
remains blocked.

| Deliverable | Role and pin | Expected result |
| --- | --- | --- |
| Trace internal ownership or a multi-file call or data path | explorer / Luna Medium | Map relevant files, symbols, and constraints |
| Verify an external API, version, or tool fact | researcher / Luna Medium | Return primary-source evidence for the relevant version |
| Decide a consequential contract, invariant, or design tradeoff | architect / Sol High | Recommend a decision and give the implementer its constraints |
| Implement a settled approach with clear acceptance criteria | worker / Luna High | Change the assigned files and run focused checks |
| Diagnose an unknown cause or implement coupled logic within an accepted contract | engineer / Sol High | Reproduce the issue or implement the change and verify the result |
| Inspect rendered UI or implement visual and interaction changes | ui_specialist / Terra XHigh | Return rendered observations or verified changes in the assigned mode |
| Reproduce a failure, execute checks independently, or add assigned tests | tester / Luna High | Report commands, outcomes, and coverage |
| Critique a plan, diff, design, or material result | reviewer / Sol High | Inspect independently in read-only mode and return actionable findings |

Use the table to resolve overlaps. Give internal mapping to the explorer and
external facts to the researcher. Have the architect settle the contract before
an engineer or worker implements it. Use a worker for a known approach and an
engineer for an unknown cause or coupled logic. Give visual work and backend logic
separate ownership. Use the tester for execution evidence and the reviewer for
independent judgment.

## Coordinate the work

Start with one or two useful owners. Add distinct assignments as needed, up to four
concurrent child threads. Keep delegation one level deep, with the root assigning
all child work. Give each deliverable one owner with exclusive writable paths,
clear acceptance criteria, and known dependencies.
Check existing owners and evidence before spawning. Follow up with the same owner
for related work. At capacity, queue distinct work for the next available slot.

Advance independent root work while agents run. Wait when an agent result is needed
to continue. Act on new evidence, and retry after a material change to a blocker.
Retire agents when ownership ends and the runtime supports closing their threads.
For multi-owner assignments, independent reviews, or handoffs, use
[delegation](references/delegation.md).

## Verify and deliver

Use a fresh independent Sol High reviewer for the initial review of requested or
material work, such as contracts, security, data, cross-component behavior, or
user-facing flows. Follow up with the same independent reviewer for focused rechecks
of the same deliverable, including across turns. Start a fresh review when the user
requests fresh eyes, the review scope changes, or the original reviewer is unavailable
or loses independence. Use direct checks for trivial edits.

Reuse applicable test evidence. Assign a tester when independent execution,
reproduction, expensive checks, or missing coverage adds useful evidence. When an
ambiguity, permission, or capability blocks progress, report the observed blocker and
the decision or capability needed.

For release work, record the user's acceptance criteria before implementation and
check behavior against them before packaging. Identify the packaged artifact by
version or digest, then run its required release checks. When the artifact changes,
rerun affected checks and any gates tied to the exact candidate.

Before delegating UI work, verify the required server, headed browser, and shared session
where supported. Give the specialist the URL, session, and target viewports. Apply
the project's design workflow and verify the rendered desktop and mobile behavior.
Report the actual interaction evidence and any missing visual coverage.

Inspect the integrated result, resolve material findings, and rerun affected checks.
Report the roles used, confirmed outcomes, and remaining gaps from actual evidence.
For activation or model verification, use [runtime](references/runtime.md).
