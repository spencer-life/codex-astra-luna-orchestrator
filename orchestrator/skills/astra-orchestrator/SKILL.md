---
name: astra-orchestrator
description: Orchestrate substantive Codex coding work with an Astra Low root, bounded Luna role agents, and an Astra reviewer. Use when delegation, parallel work, or independent review materially helps, or when explicitly requested. Keep genuinely small bounded tasks in the root.
---

# Astra Orchestrator

Explicit user instructions take precedence over this skill. Delegate useful work,
not a checklist of roles. The root owns architecture, integration, and final
acceptance; subagents provide bounded execution and evidence.

## Defaults and configuration

| Role | Model | Default effort |
| --- | --- | --- |
| Root/orchestrator | `gpt-6-astra` | `low` |
| `explorer` | `gpt-5.6-luna` | `high` |
| `worker` | `gpt-5.6-luna` | `high` |
| `tester` | `gpt-5.6-luna` | `high` |
| `researcher` | `gpt-5.6-luna` | `medium` |
| `semble_search` | `gpt-5.6-luna` | `medium` |
| `reviewer` | `gpt-6-astra` | `low` |
| `research_verifier` | Preserve its installed configuration | Unchanged |

The intended routine fallback in `[agents]` is Luna at High effort. Maintained
source lives in the `personal` branch of
https://github.com/spencer-life/codex-astra-luna-orchestrator under
`orchestrator/`. ChatGPT and Codex should read and change those same files.
Make approved changes in the repository, validate and commit them, then run
`mise run orchestrator:apply` from that checkout. Installed files in
`~/.codex/config.toml`, `~/.codex/agents/`, and
`~/.agents/skills/astra-orchestrator/` are applied copies. Do not regenerate
this skill from instructions or edit those copies as the normal update path.
Read `PERSONAL.md` in the repository for the guarded workflow. Review original
project updates separately; never install them automatically over this setup.
This table describes intended defaults, not proof of settings currently loaded.

Preserve an explicitly selected session model, effort, or profile. Do not
rewrite shared configuration, create duplicate roles, or change service tiers
merely to execute or escalate a task.

Select configured roles through the installed runtime's supported spawning
interface, using `agent_type` where available. Role-file settings may override
spawn-time requests. Do not invent parameters or assume a prompt changes the
model or effort. Distinguish requested settings, configured settings, and
runtime-confirmed settings; report uncertainty when the effective setting
cannot be observed.

Routine delegated execution stays on Luna. The root owns justified escalation;
subagents must not silently upgrade themselves or broaden their scope.

## Choose the scope

Classify the task as `root-only` or `delegated` without unnecessary narration.

Use `root-only` when the task is genuinely small and bounded and independent
context would not materially improve it. Multiple files, a routine lookup, or
a little repository reading alone do not force delegation.

Use delegation when a bounded subtask materially benefits from separate
context, independent execution, or parallel work. Examples include substantive
implementation, uncertain execution paths, independent regression validation,
consequential external research, and risk-sensitive review.

For ordinary substantive changes, prefer one Luna worker that inspects its
assigned area, implements, and performs focused validation. The root then
assesses the result. Add specialists only for a distinct contribution.

Once work is delegated, actually spawn an agent before performing that assigned
work in the root. Do not simulate delegation or duplicate the worker's task.
Brief root inspection to establish scope and architecture is appropriate.
An explicit user request for agents or parallelism requires actual delegation;
if spawning is unavailable or fails, follow the failure policy below.

## Select the smallest useful set of roles

- `worker`: Bounded implementation, targeted fixes, and scoped refactoring.
  Inspect the assigned area, implement, and run focused validation.
- `explorer`: Read-only repository mapping, execution/data-flow tracing,
  dependency inspection, and locating relevant code or tests. Use when
  investigation is substantial enough to warrant its own context.
- `tester`: Independent reproduction, regression analysis, coverage design,
  and validation. Keep High effort, but do not invoke it mechanically.
  Test changes require explicit ownership; production fixes return to the
  worker or root for assignment.
- `reviewer`: Read-only independent correctness, security, regression, and
  architectural review when risk or complexity warrants another perspective.
  Return actionable findings and supporting evidence, not unrelated edits.
- `researcher`: Current, version-specific, or externally sourced facts.
  Require primary or authoritative sources, applicable versions, and clear
  separation between verified facts and inference.
- `semble_search`: Read-only bounded semantic discovery when separate search
  context is useful. It is optional, not a gateway; all roles may use available
  Semble tools directly. Do not duplicate an explorer's investigation.
- `research_verifier`: Preserve its installed role and separate research
  workflow. Do not require it after every coding-research task or bypass its
  own invocation requirements when they apply.

Researchers do not edit repository files. Do not turn exploration,
implementation, testing, and review into a mandatory serial pipeline. A worker's
checks, a tester's behavioral evidence, and a reviewer's findings should serve
distinct purposes.

## Delegation contracts and parallelism

Every delegation includes:

- one concrete objective;
- the relevant files, subsystem, or question;
- necessary context and constraints;
- the deliverable and acceptance criteria; and
- edit permissions and ownership, with disjoint write sets where applicable.

Keep one writer per file or subsystem. Workers may make ordinary local
implementation decisions within their contract. Return scope expansion,
material architecture decisions, breaking changes, new dependencies, and
security-sensitive design choices to the root.

Keep at most three open subagent threads, or fewer if the runtime limit is
lower. Keep delegation flat unless the user explicitly authorizes nesting.
These are orchestration policies; do not assume an undocumented configuration
key enforces them. Do not spawn three agents merely because capacity exists.

Spawn independent work before waiting, within the available capacity. Start
dependent work only when its prerequisites are ready. Reuse relevant findings
rather than restarting discovery in every role. For review, give the reviewer a
stable scoped change and existing validation evidence. A reviewer returns its
findings and ends its turn; the root resumes it with the ready delta when fixes
need review. Do not leave reviewers polling a writer for progress. If an early
design review is useful, assign that bounded question separately from final
review.

Keep returns concise: conclusions, relevant paths and symbols, changes made,
commands and results, risks, and blockers. Return focused evidence rather than
large raw logs or entire files; preserve errors and enough context to verify a
claim. Share a corrected invocation or environment blocker promptly so other
agents do not repeat the same diagnosis.

Use supported waiting and completion mechanisms. While agents run, do genuinely
independent root work or wait for the next required result. Avoid frequent
no-change polling and unnecessary follow-ups. Skill instructions cannot
eliminate runtime-controlled wake-ups.

## Verification, failures, and cleanup

Assign one owner for each routine check. Its evidence includes the exact command,
result, relevant environment, and tested code state (including uncommitted changes;
HEAD alone is insufficient for a dirty tree). Share this concise record with the
root and reviewer. Reuse it while the relevant source, tests, command, dependencies,
configuration, and environment remain unchanged. Rerun affected checks after a
relevant change or failure, an unresolved concern, or a deliberately assigned
independent check. Keep independent final verification for consequential changes;
avoid accidental repetition, not necessary evidence.

When implementation depends on a parser, runtime, or configuration assumption,
validate that assumption early with a focused read-only probe of the real local
environment where available. Do not apply unfinished changes as a probe or expose
private configuration. When access is unavailable, state that limitation and use
a representative fixture without claiming it proves local compatibility. This is
not a mandatory whole-environment audit for ordinary edits.

If spawning or a subagent fails, inspect the reason and report it. Retry,
narrow, or reassign when useful. A disclosed safe root fallback is allowed
when delegation was only an optimization. Do not bypass an explicit delegation
requirement without user authorization. Never report failed work as completed.

Cancel superseded or abandoned agents rather than merely ignoring them.
Before final verification, ensure all agents writing the relevant files and
any write-producing subprocesses they started have finished or been stopped.
Confirm that writing has ceased; a cancellation request alone is not proof.
Do not stop unrelated processes. If relevant writers cannot be stopped or
accounted for, report the blocker rather than claiming a stable final result.

Close completed agent threads after retaining their results when no further
follow-up is needed. Required agents must finish or have their failure/blocker
explicitly reported. Cancel obsolete optional work instead of waiting for it
pointlessly or leaving it running after completion.

Before claiming completion, the root must:

1. Confirm the relevant working state is stable and inspect the final diff.
2. Confirm the requested behavior and scope.
3. Integrate and reconcile material subagent findings.
4. Run or confirm the highest-value affected checks against the final state.
5. State unresolved findings, blockers, or validation that could not be done.

A blocked required check or unfinished requirement means the result is partial,
not fully verified completion.

## Effort escalation

No routine role defaults to Max. Leave `research_verifier` unchanged.

Medium research/search may move to High for substantial interpretation or
conflicting evidence. Luna High may use a supported higher effort for a genuine
reasoning blocker; consider XHigh before Max where available, without forcing
every task through a retry ladder. High-risk Astra reviews may use Medium or
higher effort when warranted. The root remains Low by default unless the user
explicitly selects otherwise.

Do not escalate merely because work involves coding, tools, many files, or a
large context. Ordinary compilation failures, missing dependencies, and unclear
contracts call for diagnosis or clarification, not automatically more reasoning.

Use only supported escalation controls and verify the effective setting.
If a role file or runtime prevents the requested override, disclose that fact
and use a supported alternative or request an explicit setting change. Do not
repeatedly rewrite shared configuration to force per-task escalation.

Keep routine execution on Luna. Replacing a Luna executor with Astra requires
an explicit user request or a demonstrated reasoning blocker that the root
judges warrants model escalation. Explain a justified exception briefly;
do not silently substitute models.

## User-facing completion

Avoid narrating routine agent activity. Summarize what changed, what was
verified, important findings, and remaining limitations.

Never claim delegation without a successful spawn. When asked for delegation
details, report each agent's role, supported model/effort information,
assignment, and completion status. Do not describe configured settings as
runtime-confirmed unless the execution evidence supports that claim.
