# Terra 6.1 orchestration experiment

Status: candidate configuration, not a demonstrated universal optimum.
Source branch: `experiment/terra-6.1-orchestrator`.
Baseline: `personal` at `dce7cd6617aa6f46a7927ca8d27b7eac5c8fe12d`.

The alternate source lives in `experiments/terra/`. The existing `orchestrator/`,
its receipt-bound installer, and `personal`/`main` remain unchanged. Do not merge
this experiment into the stable branch before local runtime and task evaluation.
A draft comparison PR tracks the experiment because repository Issues are disabled.

## Configuration

| Responsibility | Model | Effort |
| --- | --- | --- |
| Primary coordinator | GPT-6.1 Terra | High |
| Architecture/planning | GPT-6.1 Sol | High |
| Difficult engineering/debugging | GPT-6.1 Sol | High |
| Code discovery / factual research | GPT-6 Luna | Medium |
| Bounded implementation / test execution | GPT-6 Luna | High |
| Browser/computer/frontend specialist | GPT-6.1 Terra | XHigh |
| Independent reviews, including design/security/final quality | GPT-6 Astra | XHigh |
| Generic fallback | GPT-6.1 Sol | Medium |

At most four spawned threads, not a requirement to spawn four. Named role files
pin their settings; an explicit spawn effort does not override a file's pin.
The Sol architect plans, but does not independently approve its own plan/work.
Astra review uses fresh context and real artifacts. Terra visual observation and
Luna test execution supply evidence, not a substitute for required Astra review.

Use more reasoning where evidence shows it matters. Do not default everything to
Max, spawn agents mechanically, duplicate work, or claim that published benchmark
scores prove this topology is best. Root `--root-effort` is an explicit trial knob;
High is the starting configuration, not a scientific claim of optimality.

## Why a launcher rather than a named Codex profile?

The inspected current `ConfigProfile` schema supports root model/effort but not an
entire agent roster. Named profiles alone would leave the installed specialists in
place. The launcher instead supplies session-only `--config` overrides for root,
four global agent defaults and the eight explicit role-file paths. Current source
loads declared role files by config-layer precedence.

It does not modify the installed configuration, agents, skills, global AGENTS.md,
authentication, permission/approval settings, providers, MCP/plugins, service tier,
voice/audio settings or existing receipt. It does not change CODEX_HOME or copy
credentials. Ordinary Codex runtime may still write its normal session state.
The experiment intentionally does not force experimental context management,
currently marked unavailable in the documentation.

Matching role names override existing roles only in that launched session. Other
custom roles remain available; the selected skill instructs the root to use the
bundled roles. The skill is referenced by its absolute source path in the initial
prompt. It is not installed as a second globally auto-selected orchestrator.
The user's project instructions remain in force. The explicit workflow selection
replaces only the old orchestration topology.

## Local adoption

Have KETA perform this through an actual local Codex thread, not a cloud-only
workspace. First inspect the live CLI, global instructions, model catalog, tools,
worktrees, local changes and private receipt. Previous local state is not proof.
Use the existing receipt-bound checkout for stable maintenance only. For this
experiment, deliberately create or reuse a separate registered worktree on the
experimental branch. This does not migrate the stable receipt or bypass its guard.
Do not switch/reset the stable checkout, discard local commits, or rewrite hashes.

From the experimental checkout, after reviewing and trusting its Mise file:

```sh
mise run terra:validate
mise run terra:test
mise run orchestrator:test
mise run terra:compatibility
mise run terra:plan -- --project /absolute/path/to/project
mise run terra:launch -- --project /absolute/path/to/project
```

`terra:check` runs the first four checks, including the unchanged stable test suite.
The Python launcher itself requires Python 3.11+ and no third-party dependencies.
The tests use pytest and PyYAML through Mise. An equivalent direct preview is:

```sh
python3 scripts/terra_orchestrator.py plan --project /absolute/path/to/project
```

`plan` does not run Codex or modify configuration. `compatibility` obtains a fresh
`codex debug models` catalog after checking CLI help/version. A supplied catalog is
accepted only for explicitly offline compatibility analysis, with freshness marked
unknown. `launch` never accepts supplied/cached catalog evidence. It requires a
clean committed source checkout on the intended branch and origin, checks the
catalog again, and rejects source changes during preflight. Missing models,
unsupported effort, unavailable debug commands or malformed roles stop activation;
there is no silent model fallback or automatic CLI reinstall.

The >=0.159.0 version floor is a prerequisite, not proof of compatibility. Verify
the installed release's schema and real custom-role loading. Do not fabricate a
model catalog or assume the latest public source equals the locally installed CLI.

Start a new experimental session. Confirm actual parent/child models and efforts
from configuration/events and observed tools, not model self-identification. Test
that the exact experiment skill is loaded and no legacy role topology is substituted.
Run bounded smoke tests and independent review before calling adoption successful.
`--prompt` supplies an initial task; without it the session checks availability and
waits for a task. An optional local `codex-terra` shell wrapper may point to this
launcher and pass the current project path, but must preserve existing shell setup
and not overwrite a conflicting command.

## Rollback and ongoing updates

Exit the experimental session and start Codex normally for the unchanged installed
workflow. Running sessions do not change retroactively. No global config rollback
is needed because the launcher does not write it. Verify any optional shell wrapper
before removing it; never delete unrelated files or the stable receipt.

Keep experimental source committed on its branch. Review updates before fetching
and fast-forwarding its worktree; preserve local changes. Do not run
`orchestrator:sync` or `orchestrator:apply` from the experimental branch.
Source validation is not live installation, and a Git checkout alone is not model
activation. Desktop/dot-created threads must use the same verified session overrides
or supported launcher; simply selecting Terra changes only the root.

## Evaluation and delivery gates

Use [the evaluation runbook](experiments/terra/evals/RUNBOOK.md) with blinded
requests and isolated fixtures. Compare the same tasks under the stable setup,
Terra-root-only with existing specialists, and the complete new topology. Keep
service tier, repository snapshot, tools and acceptance criteria matched. Repeat
representative tasks; do not select only a successful run or compare different
efforts while attributing everything to model identity.

Measure accepted outcomes, missed requirements, repair turns, actual elapsed time,
root/child usage, required review findings and unverified behavior. Use the existing
usage reporter for recorded data, not as a claim about billing or task boundaries.
Source/tests/catalog checks do not establish orchestration quality or a speed gain.

Before promoting the experiment, require a fresh Astra XHigh independent review of
its source and actual local launch behavior. Do not claim such a review ran merely
because a reviewer role exists. KETA is the local handoff coordinator, not a required
reviewer for every ordinary project PR.

## Guidance and verified references (2026-10-30)

The skill follows OpenAI skill-creator guidance: a discriminating description,
short decision-oriented entrypoint, conditional references, scope/authority
boundaries, executable checks for deterministic mechanics, and separate blinded
forward-testing. It does not repeat whole manuals or prescribe private reasoning.

- [Skill creator](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/skills/src/assets/samples/skill-creator/SKILL.md), inspected blob `490ccc6c3e0015eb982bb5c108c2df083be2c6c2`.
- [Creator validator](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/skills/src/assets/samples/skill-creator/scripts/quick_validate.py), inspected blob `e27023ece4bd259ef36560e19995eec7b6a345bf`.
- [Custom agents](https://learn.chatgpt.com/docs/agent-configuration/subagents): file pins, inheritance and parent permission boundaries.
- [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference): role config-file overrides and unavailable experimental context management.
- [Profile source](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/config/src/profile_toml.rs): no profile-level agent roster.
- [Role loader source](https://github.com/openai/codex/blob/1da2aefe001b333340fe8b012b18b072c49cc743/codex-rs/agent-roles/src/loader.rs): declared role files and config-layer precedence.

These are implementation references, not evidence that the user's machine has
this release, these models, or a working browser. Keep private logs and catalogs
out of this public repository.
