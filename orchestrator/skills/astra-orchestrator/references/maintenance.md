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

## v3 migration

Receipt v3 has nine managed files: config, five roles, the skill, and two references.

- v1 -> v3 adds the references and retires `research_verifier.toml` plus
  `semble-search.toml`.
- v2 -> v3 retires `solver.toml` plus `semble-search.toml`.
- both legacy migrations retire the previously managed `agents.max_depth` setting.

Retired files must still match their recorded receipt. New v1 reference destinations
must be absent. Do not delete receipts or local files to defeat ownership guards.
Follow `PERSONAL.md` for deliberate reconciliation and rollback.

## Models and runtime compatibility

The documented model/effort matrix was refreshed on 2026-09-22 for GPT-6 Sol and
Luna. `orchestrator:validate` checks structure and that dated matrix; it does not
prove account availability. On Codex CLI 0.156.1, `codex debug models` emits the raw
local catalog JSON accepted by the compatibility check. It is a debug subcommand,
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

This v3 setup was validated with Codex CLI **0.156.1**, whose local catalog
advertised the configured GPT-6 Sol/Luna model and effort pairs. For future changes,
use a current compatible stable Codex release and check its local catalog; 0.156.1 is
the recorded validation version, not a permanent latest-version requirement. Audio
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
