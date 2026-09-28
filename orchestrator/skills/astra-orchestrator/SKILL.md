---
name: astra-orchestrator
description: Route substantive Codex repository work between the active root session and bounded specialist agents. Use for multi-file implementation, cross-component debugging, repository-wide changes, parallelizable workstreams, useful independent testing or review, version-specific research, or when the user asks to delegate. Keep genuinely small tasks in the root.
---

# Codex Orchestrator

Honor explicit user instructions and active session choices. Optimize time to a
correct, verified result rather than agent count. The active primary-session model
is the root. The maintained default is GPT-6 Sol at high reasoning, but a model
or effort selected in the Codex picker or CLI remains the root for that session.

The root owns scope, architecture, decomposition, integration, and acceptance.
Specialists provide bounded evidence, implementation, testing, research, or review.

## Configured roles

| Role | Default | Scope |
| --- | --- | --- |
| root | active session; default Sol High | Routing, direct execution, integration, acceptance |
| explorer | Luna Medium | Repository mapping and straightforward tracing; read-only |
| worker | Luna High | Bounded implementation and focused validation |
| tester | Luna High | Independent reproduction, regression analysis, and test design |
| researcher | Luna Medium | Version-specific primary-source research; read-only |
| reviewer | Sol Max | Independent consequential change review; read-only |

Generic subagent fallback is Luna High. Keep at most four spawned threads open at
once; the limit is capacity, not a target. Prefer a flat topology unless the user
explicitly asks for something else.

Role files pin model, effort, and where specified sandbox mode. They do not own the
user's permission profile, Auto-review selection, service tier, MCP configuration,
or other local settings. Preserve active session permissions and approval behavior.
Read-only roles must not edit even if a tool could technically write.

## Delegation gate

Treat substantive repository work as delegated whenever any trigger below is present.
Root-only work is reserved for genuinely small, localized tasks with a known
implementation surface and no material benefit from an independent specialist.

The root MUST spawn the appropriate specialist before performing that delegated work
itself when any of these is true:

- repository exploration is needed before implementation or diagnosis
- the relevant implementation surface is not already known and must be located
- multiple files, modules, services, or components need inspection
- the task spans multiple files, modules, services, or components
- two or more independent workstreams exist
- debugging requires tracing across components
- external or version-specific facts need verification
- implementation and verification benefit from separate context
- an independent post-change review is materially useful
- the user explicitly asks for delegation, parallelism, agents, or subagents

For substantive read-only repository discovery, spawn `explorer` immediately. Keep
direct root reads to trivial known-location reads, exact symbol/config lookups, or
evidence required for root-owned architecture and integration. Once a delegation
trigger applies, do not continue the delegated investigation in the root while
deciding whether the agent hop is worthwhile.

If spawning is unavailable or fails, report that clearly. A safe direct fallback is
allowed only when continuing is reasonable; do not claim delegation occurred.

## Choose the execution path

- **Direct:** use only for genuinely small, localized work with a known surface and
  no delegation trigger above.
- **Discovery:** use explorer for repository mapping, locating files/tests/patterns,
  dependency or configuration inspection, and execution/data-flow tracing beyond a
  trivial known path.
- **Research:** use researcher for current or version-specific external facts that
  should be verified from primary sources.
- **Bounded implementation:** use worker after the direction, scope, and acceptance
  conditions are sufficiently clear. The worker owns ordinary implementation
  choices inside that contract.
- **Independent verification:** use tester when reproduction, regression analysis,
  or distinct test reasoning adds evidence beyond the worker's focused checks.
- **Independent review:** use reviewer for non-trivial or consequential changes when
  an independent post-change review is materially useful. Tiny deterministic edits
  do not need a review turn merely to satisfy a pipeline.

There is no solver role. If the hard part is deciding architecture, untangling an
ambiguous problem, or choosing a cross-component direction, that remains root work.
The root may gather bounded evidence first, then hand a clear implementation contract
to the worker.

Do not require every role after every change. Use only specialists with a distinct
contribution beyond the mandatory trigger that caused delegation, and do not make the
root repeat a completed subagent investigation.

## Semble discovery

Semble is a direct repository tool, not a subagent. Use the installed Semble MCP or
CLI from the role that needs semantic discovery. Read known locations directly and
use exact search for identifiers, filenames, or exhaustive references. Semantic
similarity is evidence for discovery, not a call graph or proof of absence.

For version-specific Semble commands, index behavior, coverage, or maintenance, read
only the relevant part of [Semble reference](references/semble.md). Do not insert an
agent hop simply to call Semble.

## Delegate bounded ownership

Every delegated task should state one objective, relevant locations or known
decisions, constraints, deliverable, acceptance conditions, and edit permissions.
Give enough context to succeed without copying the whole conversation or repository.

Keep one writer per file or subsystem. Spawn independent tasks before waiting when
capacity permits; serialize genuine dependencies. Material architecture, breaking
API/schema changes, new dependencies, security-sensitive decisions, and ownership
conflicts return to the root unless already authorized.

If behavior depends on a parser, runtime, configuration, or environment assumption,
probe it early and read-only when practical. Never expose private inputs or apply an
unfinished change merely as a probe.

## Verify and review

Assign routine checks one owner. Share exact commands, results, relevant environment,
and actual tested code state, including uncommitted changes. Reuse still-valid
execution evidence instead of repeating an unchanged check; rerun after relevant
source, test, dependency, configuration, command, or environment changes.

For review, provide a stable scoped change and existing validation evidence. The
reviewer reports findings and ends its turn. Ordinary implementation findings go
back to the worker. Findings that expose an architecture, API, security, or scope
decision go back to the root. The reviewer remains read-only and does not fix its
own findings.

Before completion, inspect the stable final diff, reconcile material findings,
confirm requested scope, and run or confirm the highest-value final checks. Report
blocked validation as partial rather than completed. Never claim delegation or
testing without corresponding evidence.

## Session and context behavior

The maintained configuration enables experimental context management. Respect an
explicit model or reasoning-effort choice made during the session rather than
rewriting shared configuration. Do not claim a picker change, context-management
feature, or prompt cache behaved a particular way without runtime evidence.

On spawn or agent failure, report it and narrow, retry, reassign, or use a disclosed
safe direct fallback. Ordinary test failures do not automatically justify a stronger
model or more reasoning.

## References and maintenance

Maintain this setup in the repository, not installed copies. For source changes,
sync/apply/recovery, compatibility checks, CLI compatibility, or permission-profile
boundaries, read [maintenance](references/maintenance.md). For Semble details, read
only the relevant part of [Semble reference](references/semble.md).

Do not force compaction, arbitrary token caps, model changes, service tiers, or
permission changes. Summarize outcomes, actual verification, and remaining limits
without narrating routine orchestration. A configuration table is not proof of
runtime use.
