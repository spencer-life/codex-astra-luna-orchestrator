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
prove account availability. Use:

```sh
mise run orchestrator:compatibility --model-catalog /path/to/current-model-catalog.json
```

against a fresh local catalog, then verify effective root and spawned-role selections
in a new session. Role files pin specialist model/effort. The root is the active
primary-session model: an explicit picker or CLI choice is respected.

Codex CLI **0.156.0** is the compatibility target for this migration. Voice is enabled
by default in that release. Do not add a portable voice-enable flag: current audio
device settings are machine-local, and realtime configuration remains outside this
managed fragment. Let `/voice settings` and the local client own those preferences.

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
