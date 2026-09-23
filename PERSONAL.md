# Maintaining the personal setup

## One source for ChatGPT and Codex

Use **https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal**.
Installed files are applied copies, not a competing source. Read `AGENTS.md` before
repository changes.

The maintained personal source is:

- `orchestrator/config.toml`: default root, experimental context management, and
  four owned `[agents]` settings.
- `orchestrator/agents/*.toml`: five explicitly configured specialist roles.
- `orchestrator/skills/astra-orchestrator/SKILL.md`: the compact **Codex
  Orchestrator** routing skill. The legacy skill id/path is retained for compatibility.
- `references/maintenance.md` and `references/semble.md`: on-demand guidance.
- `scripts/orchestrator_sync.py`, `mise.toml`, and tests: guarded maintenance.
- `scripts/token_usage.py` and `PERFORMANCE.md`: read-only metrics and limits.

Do not publish the full installed config, credentials, permission profiles, providers,
MCP/app settings, private paths, sessions, logs, receipts, or backups. Do not edit
installed copies as the normal update path.

## Current defaults and routing

The maintained default root is **GPT-6 Sol Medium**. The active session model is the
root, so an explicit picker or CLI choice such as GPT-6 Luna is respected for the
whole primary thread rather than being overwritten by the skill.

Configured specialists:

- explorer: GPT-6 Luna Medium, read-only
- researcher: GPT-6 Luna Medium, read-only
- worker: GPT-6 Luna High, workspace-write
- tester: GPT-6 Luna High, workspace-write
- reviewer: GPT-6 Sol Medium, read-only
- generic fallback: GPT-6 Luna High

There is no solver or Semble-search subagent. Hard architecture or ambiguous
cross-component reasoning stays with the root; once direction is clear, the worker
owns the bounded implementation. Semble is called directly through its MCP/CLI by
the role that needs discovery.

Keep at most four spawned threads open. The cap is capacity, not a target. No
`max_depth` setting is managed in v3; current Codex documents that setting as
V1-only and ignored by V2.

The managed config enables:

```toml
[features.context_management]
experimental_mode = true
```

Treat model/effort picker changes and context-management behavior as runtime facts:
do not claim cache or compaction behavior that was not actually observed.

## Local permissions and voice stay local

The public repository does not own `default_permissions`, named `[permissions]`
profiles such as Workspace Tools, Auto-review/approval configuration, MCP/plugin
settings, service tier, or sandbox policy outside the role-specific restrictions.
The merge/apply path preserves them.

Codex CLI **0.156.0** is the compatibility target checked for this migration. Voice
conversations are enabled by default there, with F8 and `/voice settings`. The
current config schema describes `[audio]` device choices as machine-local and the
broader `[realtime]` section as experimental, so neither is added to this public
managed fragment. Let Codex persist those local preferences.

## Review, commit, and apply

Prerequisites are Git, mise, and uv. In the maintained local `personal` checkout:

```sh
mise trust
mise run orchestrator:sync
mise run orchestrator:validate
mise run orchestrator:test
mise run orchestrator:compatibility --model-catalog /path/to/current-model-catalog.json
mise run orchestrator:plan
# Review and commit local edits before applying them.
mise run orchestrator:apply
mise run orchestrator:status
git push origin personal
```

`sync` fast-forwards only from this fork's `personal` branch. It does not install
an unmerged PR. For remote candidates, review and test their branch first, then merge
approved changes into `personal`. A plan requires the maintained checkout identity;
do not bypass the branch guard to install a feature branch.

The source validator uses the documented model/effort matrix checked **2026-09-22**.
That is structural evidence, not proof of account availability. Before installing new
model selections, run the compatibility check against a fresh local Codex model
catalog and verify the effective selections in a new session. Never silently alias an
unavailable model.

## Receipt version 3 migration

The v3 source contains **nine managed files**: one config fragment, five roles, one
skill, and two references.

### From receipt v1

A direct v1-to-v3 migration:

- adds the two reference files only when their destinations are absent;
- retires `research_verifier.toml` and `semble-search.toml` only when they still
  match the v1 receipt;
- retires the previously managed `agents.max_depth` setting;
- updates the managed model/context/agent settings to v3.

It does **not** create the old v2 solver on the way through.

### From receipt v2

A direct v2-to-v3 migration:

- retires `solver.toml` and `semble-search.toml` only when they still match the
  v2 receipt;
- retires the previously managed `agents.max_depth` setting;
- keeps the already managed reference files;
- updates the managed model/context/agent settings to v3.

Existing-file drift, missing retired files, symlinks, and ownership collisions stop
the migration. Apply backs up every affected path and the prior receipt before writes,
then restores them on rollback when safe.

A genuinely unmanaged installation still requires an explicitly prepared private
baseline. This remains a maintenance workflow, not a blank-machine installer.

## Apply protections and recovery

Apply merges only allowlisted config values while preserving unrelated settings and
comments. In particular, Workspace Tools, `default_permissions`,
`agents.interrupt_message`, Auto-review/approval settings, MCP/apps/plugins,
service tier, voice/audio preferences, and other private machine configuration remain
local.

The workflow validates source structure, exact managed paths, role TOML, skill YAML
and references, model/effort pairs, secret patterns, installed hashes/settings,
symlinks, checkout identity, and concurrent edits. It locks applies, snapshots and
backs up affected state, rechecks before writing, and skips unchanged bytes.

State: `~/.local/state/astra-orchestrator/state.json`  
Backups: `~/.local/state/astra-orchestrator/backups/`

Keep both private because config backups include unrelated local settings. Do not edit
receipt hashes to bypass drift. Preserve newer local work before recovery and restore
files plus the matching receipt from one backup generation only.

After an apply changes configuration, role instructions, or the skill, start a new
Codex session. Apply does not restart running sessions or override an explicit model
selection already active in a thread.

## Original-project updates

`origin` is this fork; `upstream` is
`https://github.com/donvito/codex-astra-luna-orchestrator.git`.
Keep `main` upstream-only. Review upstream fixes separately and port only approved
changes to `personal`; never merge `personal` into `main` or automatically apply
upstream templates.
