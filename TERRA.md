# Terra 6.1 orchestration experiment

Branch: `experiment/terra-6.1-orchestrator`; draft PR #6 stays unmerged.
Stable baseline: `personal` at `dce7cd6617aa6f46a7927ca8d27b7eac5c8fe12d`.
Status: implementation candidate, not a proven universally optimal configuration.

## Current decision: no Astra

The user excludes Astra because of usage cost. This supersedes the original trial's
Astra reviewer/evaluator recommendation. Use no Astra for implementation, review,
evaluation, fallback or escalation. The validator allows only the three model IDs
below and rejects Astra in root, fallback and every named role. A catalog offering
Astra does not authorize it. Historical repository/skill names are unchanged.

| Responsibility | Model / effort |
| --- | --- |
| Primary coordinator | GPT-6.1 Terra High |
| architect / engineer | GPT-6.1 Sol High |
| reviewer, independent from the author | GPT-6.1 Sol High |
| explorer / researcher | GPT-6 Luna Medium |
| worker / tester | GPT-6 Luna High |
| ui_specialist | GPT-6.1 Terra XHigh |
| Generic fallback, only when no named role fits | GPT-6.1 Sol Medium |

Maximum four concurrent children, not four per role. No worker recursion. No
automatic XHigh/Max escalation or full-team ceremony on small work. Same-model
independent review means a different context, not an author's self-check.

## Explicit delegation, not interchangeable helpers

The skill now requires a routing decision before substantive work. A matching
substantive task is delegated before the root performs it; skipped delegation needs
a concrete user/capability/ownership exception. Trivial known edits stay direct.
Explicit independent review/verification requests override the trivial shortcut.

Role descriptions and instructions distinguish internal discovery from external
research, deciding a contract from solving within it, known implementation from
unknown causes, visual/browser work from backend logic, and execution evidence from
independent critique. One owner per deliverable/file; no generic agent when a named
role fits, no duplicate parent/worker implementation, and no requirement to activate
all eight roles on every task. The skill's routing table is the authoritative guide;
its delegation reference supplies examples and reporting contracts.

A claim that an agent was used is not proof. Local validation records actual spawn
metadata and outputs, including routing exceptions. Fourteen blinded fixture cases
cover all eight roles plus trivial work, unavailable tools and scope boundaries.
Static tests check the specification/configuration, not whether models obey it.

## Activation and isolation

Source is under `experiments/terra/`; launcher is `scripts/terra_orchestrator.py`.
Original `orchestrator/`, its installer, receipts, `personal` and `main` are untouched.
Named Codex profiles cannot currently switch the full roster. The launcher supplies
session-only root/default-agent/role-file overrides and an explicit skill path.
A Git checkout or model-picker change alone does not activate this workflow.

No global config, installed agents/skills, global AGENTS.md, credentials, providers,
permissions/Auto-review, MCP/plugins, service tier/Fast, voice or CODEX_HOME changes.
Normal Codex may still write its own session state. This workflow does not force
experimental context management. Other inherited roles may remain visible; the
skill/launch prompt prohibit using them to evade the roster or no-Astra decision.
This is not a provider-level model/billing firewall; verify effective runtime state.

## Local adoption through KETA

Use a real local WSL/Linux Codex thread. Read applicable AGENTS.md and
[LOCAL-HANDOFF.md](experiments/terra/LOCAL-HANDOFF.md). Inspect the actual CLI,
help/schema, model catalog, instructions, worktrees and private stable receipt.
Keep the stable receipt-bound checkout unchanged. Reuse or create a separate
registered experiment worktree after checking collisions/local work. Do not reset,
force-push, discard unpublished changes or rewrite receipt identity/hashes.

After reviewing and trusting the experimental Mise file:

```sh
mise run terra:validate
mise run terra:test
mise run orchestrator:test
mise run terra:compatibility
mise run terra:plan -- --project /absolute/path/to/disposable-project
mise run terra:launch -- --project /absolute/path/to/disposable-project
```

`terra:check` runs validation, both suites and fresh compatibility. Python 3.11+
is required; the launcher uses only the standard library. Tests use pytest/PyYAML.
The minimum Codex CLI 0.159.0 floor is a prerequisite, not proof of compatibility.
Verify the actual installed release's custom-role schema and runtime behavior.

`plan` is a preview, not installation or a model call. `compatibility` reads a fresh
local catalog by default; supplied catalogs are explicitly offline evidence only.
`launch` requires clean committed experiment source and the expected branch/origin,
obtains a fresh catalog and rejects source drift. It never accepts a cached catalog
as launch proof, silently substitutes a model or automatically reinstalls the CLI.
Role-file pins override spawn defaults; prose does not change reasoning effort.

In a NEW session verify actual root/child models, efforts, loaded skill, tools and
inherited controls from config/events, not self-identification. Inspect any older
trial wrapper/installed copy and update safely; never reapply the old Astra handoff.
Start with a small smoke sample from the evaluation runbook and a fresh Sol High
review. Remaining cases are available for targeted regressions and later comparison;
do not run repeated full evaluations merely because a file changed.

After validation, an optional thin `codex-terra` wrapper may point to this launcher
and current project path, preserving existing commands/shell setup. Dot-created
threads need the same verified overrides. No claimed activation from a root-only
model change. Report unsupported thread-launch capabilities as concrete blockers.

## Exit, updates and promotion

Exit the trial and start Codex normally for the unchanged stable workflow. Existing
sessions do not change retroactively. No global config rollback is needed. Preserve
work and review experiment updates before fast-forwarding. Never run stable
`orchestrator:apply` or `orchestrator:sync` from this branch or merge PR #6 as part of
local activation. Keep private catalogs, logs and configuration out of Git.

A fresh Sol High reviewer checks source and local activation. No review is claimed
merely because a role exists. Before promotion, compare accepted outcomes, missed
requirements, repairs, elapsed time and usage on matched tasks/tooling/service tier.
Use existing usage reports only for what logs establish, not as subscription bills.
Do not infer speed, intelligence or reliable delegation from configuration tests.

## Skill-creator and implementation references

The skill retains a focused entrypoint, discriminating description, conditional
references, authorization boundaries and blinded forward tests. Instructions guide
observable outcomes, not private reasoning. References inspected 2026-10-30:

- [Skill creator](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md), blob `490ccc6c3e0015eb982bb5c108c2df083be2c6c2`.
- [Creator validator](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/skills/src/assets/samples/skill-creator/scripts/quick_validate.py), blob `e27023ece4bd259ef36560e19995eec7b6a345bf`.
- [Custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents), including file pins and inherited permission boundaries.
- [ConfigProfile source](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/config/src/profile_toml.rs).
- [Role loader](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/agent-roles/src/loader.rs).
- [Evaluation runbook](experiments/terra/evals/RUNBOOK.md).

These references do not establish the user's local version, model availability or
a working browser. Unavailable local/model-backed checks remain explicitly unverified.
