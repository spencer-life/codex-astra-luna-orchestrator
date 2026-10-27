---
name: astra-orchestrator
description: Orchestrate complex Codex coding work with the active root session and GPT-6.1 Sol High as the maintained default, GPT-6 Luna specialists, a GPT-6.1 Terra Extra High visual QA specialist, and an independent GPT-6.1 Sol High reviewer. Use for multi-file features, debugging, UI/browser verification, repo-wide changes, parallelizable workstreams, or explicit delegation. Do not use for trivial edits or simple questions.
---

# Orchestrator — GPT-6.1 Sol High + GPT-6 Luna + GPT-6.1 Terra XHigh

The user's explicit instructions take precedence over this skill.

## Topology

- root: active session; maintained default `gpt-6.1-sol` at `high` reasoning
- explorer and researcher: `gpt-6-luna` at `medium` reasoning
- worker and tester: `gpt-6-luna` at `high` reasoning
- visual_qa: `gpt-6.1-terra` at `xhigh` reasoning, in a read-only context
- reviewer: `gpt-6.1-sol` at `high` reasoning, in an independent read-only context

The role files in `.codex/agents/` pin these models and reasoning levels; generic subagents inherit the Luna defaults in `.codex/config.toml`. Terra is opt-in through the named `visual_qa` role; do not silently route generic tasks to Terra. Respect the active root model and do not change it from within a session.

## Delegation

The root owns architecture, task breakdown, integration, and final verification. Keep genuinely small tasks root-only. For work spanning multiple files, independent workstreams, cross-component debugging, or useful independent review, delegate bounded tasks to specialized agents when available. If required delegation is unavailable, report that rather than claiming it happened.

For each delegated task, specify the objective, scope, context, constraints, deliverable, and acceptance criteria. When spawning, select the named role and its pinned model; do not silently replace a Luna worker with the root. Use explorer for mapping code, worker for implementation, tester for verification, researcher for version-specific facts, visual_qa for visual/browser/computer-use inspection, and reviewer for independent post-change review. Do not let multiple workers edit the same files without explicit ownership boundaries.

For UI or design tasks with a runnable interface, assign visual_qa a focused inspection: URLs/routes, viewport sizes, relevant design references, and verification criteria. Ask for browser/screenshot evidence and reproducible findings; do not mistake a source-code review for visual verification. Terra is read-only: assign actual fixes to a writable worker or the root, then repeat targeted visual checks. Keep the independent reviewer for correctness/security and higher-level judgment; Terra does not replace that review. If browser tools are unavailable, report the gap and do not claim visual verification.

Run independent tasks in parallel and serialize dependent work. Prefer exploration, architecture decision, bounded implementation, targeted testing, independent review when useful, then integration and final verification. Do not spawn every role mechanically. Report agent failures and resolve material findings before finishing.

## Verification

Inspect the final diff, verify requested behavior, run relevant tests, and state any validation that could not be performed. Never claim a subagent was used unless it was actually spawned.

For source changes, sync/apply/recovery, compatibility checks, or permission-profile boundaries, read [maintenance](references/maintenance.md). For Semble details, read only the relevant part of [Semble reference](references/semble.md).
