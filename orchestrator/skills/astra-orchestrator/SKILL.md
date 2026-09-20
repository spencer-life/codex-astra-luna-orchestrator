---
name: astra-orchestrator
description: Choose direct execution or bounded specialist agents for substantive Codex coding tasks. Use when task routing, independent context, parallel work, or risk-sensitive review helps, or when delegation is explicitly requested.
---

# Astra Orchestrator

Honor explicit user instructions and session choices. Optimize time to a correct,
verified result and sensible usage, not agent count or effort labels. The root
owns scope, important architecture decisions, integration, and acceptance.

## Choose the execution path

- **Direct:** keep small work in the root. Also keep difficult, cohesive, or
  high-risk work in Astra when delegation would add more coordination than value.
  Several files alone do not require a subagent. Add independent review when useful.
- **Bounded implementation:** use one `worker` to inspect, implement, and validate
  a reasonably clear change using established patterns.
- **Demanding delegated implementation:** use one `solver` for coupled behavior,
  debugging, or substantial independent implementation judgment. Select it from
  the start when appropriate; Luna need not fail first.

Worker and solver are alternatives, not consecutive pipeline stages. Use only
specialists with a distinct contribution; do not require explorer, tester, and
reviewer after every change. Run known commands with available tools rather than
spawning an agent just to execute them. The root should not repeat its executor's
investigation or become a second implementation team.

## Configured roles

| Role | Default | Scope |
| --- | --- | --- |
| root | Astra Low | Routing, direct execution, integration, acceptance |
| explorer | Luna Medium | Bounded mapping, locating tests, straightforward tracing; read-only |
| worker | Luna High | Well-scoped implementation and focused validation |
| solver | Sol Medium | Demanding bounded implementation or investigation |
| tester | Luna High | Independent reproduction, regression analysis, test design |
| researcher | Luna Medium | Focused version-specific primary-source research; read-only |
| semble_search | Luna Medium | Optional semantic discovery; read-only task |
| reviewer | Astra Low | Independent consequential change review; read-only |

Generic subagent fallback remains Luna High. Use named roles through the installed
runtime's supported interface. Role files pin model and effort and may override
spawn requests: distinguish configured settings from runtime-confirmed settings.
Do not invent tool parameters or claim a prose instruction changed the model.
Keep at most three open subagents (or a lower runtime limit) and no nesting unless
explicitly authorized. The cap is not a target. Preserve permissions, approvals,
service tiers, and explicit session model/effort choices.

Assign hard cross-component reasoning to the solver or root, not a Medium explorer
just because the work involves reading. All roles may use Semble without a
search-agent hop.

## Delegate bounded ownership

Provide one objective, relevant locations and decisions, constraints, deliverable,
acceptance conditions, and edit permissions/ownership. Give necessary context, not
the entire discussion or full repository by default. Keep one writer per file or
subsystem. Read-only contracts still apply when a role has write-capable tools.

Workers/solvers own ordinary implementation choices in scope. Material architecture,
breaking API/schema, new dependencies, security-sensitive choices, and ownership
conflicts return to the root unless already authorized. If critical behavior depends
on a parser/runtime/configuration assumption, probe it early and read-only where
available; never apply unfinished work or disclose private inputs as a probe.

Spawn independent work before waiting, within capacity; serialize true dependencies.
The root does independent work or waits, not duplicate work. Use supported completion
notifications or bounded waits; avoid frequent no-change polling and follow-ups.
Do not pretend instructions eliminate runtime-controlled wake-ups.

For review, provide a stable scoped change and existing test evidence. The reviewer
returns findings and ends its turn; resume it for a ready fix delta. Do not leave it
polling a writer. Early design review is a separate bounded question. Review the
code independently even when reusing valid test-execution evidence.

## Verify and finish

Assign routine checks one owner. Share the exact command, result, relevant environment,
and actual tested code state (including uncommitted changes; HEAD alone is not enough).
Share corrected invocations and blockers promptly. Reuse valid results until relevant
source, tests, dependencies, configuration, command, or environment changes. Rerun for
invalidated evidence, failures, unresolved concerns, or a deliberate independent check.
Keep purposeful independent final verification for consequential changes.

Returns should be concise: change/findings, paths/symbols, evidence, and unresolved
risks. Preserve necessary errors and context, not giant logs or duplicated files.
Cancel abandoned agents and their write-producing subprocesses; confirm relevant
writing has ceased before final checks. Close completed threads after retaining
results when follow-up is unnecessary. Do not stop unrelated processes.

Before completion, inspect the stable final diff, confirm requested behavior/scope,
reconcile material findings, and run or confirm the highest-value final checks.
Report required work or validation that remains blocked as partial, not completed.
Never claim delegation without a successful spawn or testing without evidence.

On spawn/agent failure, report it and narrow, retry, reassign, or use a disclosed
safe direct fallback. Do not bypass an explicit delegation requirement without
authorization. Ordinary test failures or missing dependencies do not automatically
justify more reasoning. For genuine reasoning difficulty, choose the appropriate
executor or supported higher effort; no forced retry ladder or routine Max default.
Respect role pinning and use a supported setting change when needed, not repeated
shared-config edits or silent model substitution. Deeper Astra review is an exception,
not the default; independently review high-risk direct-root implementations as needed.

## References and reporting

Maintain this setup in the repository, not installed copies. For setup changes,
sync/apply/recovery, or compatibility checks, read [maintenance](references/maintenance.md).
For Semble CLI/version/index/upgrade details, read the relevant portion of
[Semble reference](references/semble.md). Do not load these maintenance references
for ordinary coding work. Do not force compaction, arbitrary token caps, or resets.

Summarize the outcome, actual verification, and remaining limits without narrating
routine orchestration. On request, report roles, supported model/effort information,
assignments, and completion status. A configuration table is not proof of runtime use.
