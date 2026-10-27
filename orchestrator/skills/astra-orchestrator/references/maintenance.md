# Maintaining this setup

Maintained source:
https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal

Read the repository's current `AGENTS.md` and `PERSONAL.md` before maintenance.
`orchestrator/` is authoritative; installed `~/.codex/agents/` and
`~/.agents/skills/astra-orchestrator/` files are applied copies. The config fragment
owns only its declared portable settings, not the whole installed
`~/.codex/config.toml`.

Make approved changes in the repository, validate/test/review and commit, then use
the guarded mise sync/compatibility/plan/apply/status workflow. Preserve drift,
unrelated settings, explicit session choices, permissions, MCP/plugins, service tier,
voice/audio preferences, and other machine-local configuration.

## Choosing and recovering the checkout

Before maintenance, inspect the installed state/receipt and select the checkout at
its recorded source root and branch. Reuse that maintained checkout when it exists;
do not rewrite receipt identity to move between duplicate checkouts, and do not
apply from a worktree whose root conflicts with the receipt. Before reconciling or
resetting it, inspect tracked, staged, unstaged, untracked, and local-only Git work.
Preserve any unique work durably before cleanup; never discard it as stale without
checking. Once the receipt-bound checkout is clean and current, run the guarded
sync, validate, test, local-catalog compatibility, plan, apply, and status workflow.

## v4 migration

Receipt v4 has ten managed files: config, six roles (including Terra `visual_qa`),
the skill, and two references.

- v1 -> v4 adds the references and `visual_qa.toml`, retires
  `research_verifier.toml` and `semble-search.toml`.
- v2 -> v4 adds `visual_qa.toml`, retires `solver.toml` and
  `semble-search.toml`.
- v3 -> v4 adds only `visual_qa.toml`.
- v1/v2 also retire the previously managed `agents.max_depth` setting.

Every new managed destination must be absent; an existing Terra file is a collision,
not permission to overwrite. Retired files must match their recorded receipts.
The guarded apply backs up and rolls back new files as well as existing files.
Do not delete receipts or local files to defeat ownership guards.
Follow `PERSONAL.md` for deliberate reconciliation and rollback.

## Models and runtime compatibility

The documented model/effort matrix was refreshed on 2026-10-26 to include GPT-6.1
Terra `xhigh`, alongside GPT-6.1 Sol, GPT-6 Sol, and Luna. `orchestrator:validate` checks structure and that
dated matrix; it does not prove account availability. On Codex CLI 0.156.1,
`codex debug models` emits the raw local catalog JSON accepted by the compatibility
check. It is a debug subcommand,
so after a CLI update first
confirm it remains listed by `codex debug --help`; if it is unavailable or its output
schema changed, stop and inspect the supported local catalog mechanism. Never
fabricate catalog data. For this release, use:

```sh
codex debug models > /tmp/codex-model-catalog.json
mise run orchestrator:compatibility -- --model-catalog /tmp/codex-model-catalog.json
```

against a fresh local catalog, then verify effective root and spawned-role selections
in a new session. Role files pin specialist model/effort. The root is the active
primary-session model: an explicit picker or CLI choice is respected.

The preceding v3 setup was validated with Codex CLI **0.156.1**.
GPT-6.1 Terra requires Codex CLI **0.159.0 or later**; before applying v4,
use an updated compatible stable release and require a fresh local catalog that
advertises `gpt-6.1-terra/xhigh`. The previous validation is historical,
not evidence of local v4 compatibility. Audio
device settings are machine-local, and realtime configuration remains outside this
managed fragment. Let Codex and the local client own those preferences.

Experimental context management is deliberately enabled in the managed config.
`max_depth` is deliberately absent; current Codex marks it V1-only and ignored by V2.

## Permissions boundary

The orchestrator does not own `default_permissions`, Workspace Tools or other named
`[permissions]` profiles, Auto-review/approval selection, MCP/plugin policy, or
service tier. Specialist `sandbox_mode` values only express their role-specific
read/write boundary. Preserve the active local permission configuration.

After applying changed configuration or instructions, start a new Codex session.
The workflow does not restart existing sessions or rewrite an explicitly selected
model in a running thread.
