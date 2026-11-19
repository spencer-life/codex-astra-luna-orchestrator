# Maintaining the personal setup

## One source for ChatGPT and Codex

Use **https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal**.
Installed files are applied copies, not a competing source. Read `AGENTS.md` before
repository changes.

The maintained personal source is:

- `orchestrator/config.toml`: default root, experimental context management, and
  four owned `[agents]` settings.
- `orchestrator/agents/*.toml`: five explicitly configured specialist roles.
- `orchestrator/skills/astra-orchestrator/SKILL.md`: the maintained upstream
  Astra Orchestrator skill, adapted only to this setup's active-root behavior,
  configured model efforts, and reference links.
- `references/maintenance.md` and `references/semble.md`: on-demand guidance.
- `scripts/orchestrator_sync.py`, `mise.toml`, and tests: guarded maintenance.
- `scripts/token_usage.py` and `PERFORMANCE.md`: read-only metrics and limits.

Do not publish the full installed config, credentials, permission profiles, providers,
MCP/app settings, private paths, sessions, logs, receipts, or backups. Do not edit
installed copies as the normal update path.

## Current defaults and routing

The maintained default root is **GPT-6.2 Sol High**. The active session model is the
root, so an explicit picker or CLI choice such as GPT-6 Luna is respected for the
whole primary thread rather than being overwritten by the skill.

Configured specialists:

- explorer: GPT-6 Luna Medium, read-only
- researcher: GPT-6 Luna Medium, read-only
- worker: GPT-6 Luna High, workspace-write
- tester: GPT-6 Luna High, workspace-write
- reviewer: GPT-6.2 Sol High, read-only
- generic fallback: GPT-6 Luna High

The maintained skill is based on upstream `donvito/codex-astra-luna-orchestrator`
commit `f5efba0`, file
`profiles/GPT6-SolMedium-LunaMax/agents/skills/astra-orchestrator/SKILL.md`.
The source skill was adapted to preserve this setup's active-root behavior and
configured specialist efforts, set the reviewer to GPT-6.2 Sol High, and link the
two repository reference files required by source validation.

The original five role files in `orchestrator/agents/` follow upstream profile
`profiles/GPT6-SolMedium-LunaMax/codex/agents/` at commit
`f5efba0f957a1e3f0671e629ccc2c655725a7e7b`. They retain only this setup's
current `model` and `model_reasoning_effort` values; all other role content
comes directly from that upstream profile. The root handles visual design,
UI implementation that needs visual judgment, and browser/computer-use checks.
Non-visual subtasks can still be delegated when useful.

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
settings, service tier, or sandbox policy. Current custom agents inherit the
parent sandbox and permissions. Non-edit instructions are not separate sandbox
restrictions. The merge/apply path preserves machine-local settings.

Before applying v6, confirm a fresh local catalog advertises `gpt-6.2-sol/high`
for root and reviewer and the configured Luna pairs. Audio device and realtime
preferences remain machine-local.

## Review, commit, and apply

Prerequisites are Git, mise, and uv. In the maintained local `personal` checkout:

```sh
mise trust
mise run orchestrator:sync
mise run orchestrator:check
mise run orchestrator:plan
# Review and commit local edits before applying them.
mise run orchestrator:apply
mise run orchestrator:status
git push origin personal
```

Before choosing a checkout for sync, apply, or recovery, inspect the installed
receipt/state and use its recorded source root. Do not rewrite that identity to move
between duplicate checkouts or apply from a conflicting worktree. Preserve unique
local work before reconciling or resetting the receipt-bound checkout; see the
maintenance reference for the recovery procedure.

`sync` fast-forwards only from this fork's `personal` branch. It does not install
an unmerged PR. For remote candidates, review and test their branch first, then merge
approved changes into `personal`. A plan requires the maintained checkout identity;
do not bypass the branch guard to install a feature branch.

`orchestrator:check` runs source validation, the existing test suite, and compatibility
against a freshly captured `codex debug models` catalog. It verifies that the installed
CLI exposes that command and removes the temporary catalog afterward. It does not
apply files or run a model request. The standalone validation, test, and compatibility
tasks remain available; `orchestrator:compatibility -- --model-catalog PATH` accepts
an explicitly supplied catalog, and `--refresh-catalog` captures a new one.

The source validator uses the documented model/effort matrix updated **2026-11-19** to include GPT-6.2 Sol.
That is structural evidence, not proof of account availability. Before installing new
model selections, run the compatibility check against a fresh local Codex model
catalog and verify the effective selections in a new session. Never silently alias an
unavailable model.

## Receipt version 6 migration

The v6 source has nine managed files: config, five roles, one skill, and two
references. Migration is direct; it never installs the retired UI role on the
way through.

- v1 adds missing references and retires its two obsolete roles.
- v2 retires its two obsolete roles; v1/v2 also retire managed `agents.max_depth`.
- v3 never owned the UI specialist; any custom file at that path is left alone.
- v4/v5 retire `.codex/agents/ui_specialist.toml` only if it matches the receipt.
  A missing, changed, or symlinked former role stops the migration.

The prior role, other affected files, and the prior receipt are backed up before
apply. If application fails, the guarded workflow restores them.

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
Run `mise run orchestrator:upstream` to fetch the original `upstream/main` and
preview changes without modifying maintained or installed files. Role comparisons
exclude only `model` and `model_reasoning_effort`; every other role field is compared.
The skill comparison uses local `main` as the last-reviewed upstream snapshot,
so personal model/effort topology and maintenance links do not create repeated diffs.
The preview reports the exact baseline and candidate commits.

Keep `main` upstream-only. After porting reviewed skill changes and committing them
on `personal`, advance local `main` to the reviewed upstream commit. Leave that
baseline unchanged while skill updates are deferred. Record the imported upstream
commit in the provenance above. Never merge `personal` into `main` or automatically
install upstream templates.
