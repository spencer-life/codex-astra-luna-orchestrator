# Maintaining the personal setup

## One source for ChatGPT and Codex

Use **https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal**.
Specify the branch and, for a precise review, the commit. A connection or cached
view does not prove the latest source was inspected. Installed files are applied
copies, not a competing source. Read `AGENTS.md` before repository changes.

Maintain:

- `orchestrator/config.toml`: root selection and only the five owned agent settings.
- `orchestrator/agents/*.toml`: seven explicitly configured coding/research roles.
- `orchestrator/skills/astra-orchestrator/SKILL.md`: the compact routing skill.
- Its `references/maintenance.md` and `references/semble.md`: on-demand guidance.
- `scripts/orchestrator_sync.py`, `mise.toml`, and tests: guarded maintenance.
- `scripts/token_usage.py` and `PERFORMANCE.md`: read-only metrics and limitations.

Do not publish full installed config, credentials, permissions, providers, MCP
servers, apps/plugins, private paths, sessions, logs, receipts, or backups. Do not
regenerate the skill from a prompt or edit installed files as the normal update path.

## Defaults and routing

Astra Low remains root and reviewer. Luna Medium handles bounded exploration,
research, and Semble discovery. Luna High handles bounded implementation, independent
testing, and generic fallback. The new Sol Medium `solver` handles demanding bounded
implementation or investigation. Worker and solver are alternatives, not stages.
Astra can execute difficult cohesive work directly; Luna need not fail first.

Keep three open subagents at most and flat delegation unless explicitly authorized.
The existing `max_depth = 1` value is preserved, not treated as proof that a specific
Codex build enforces it. Preserve explicit session choices, approvals, service tiers,
and existing sandbox settings. Semble's sandbox remains inherited; its assignment is read-only. The obsolete
`research_verifier` role is retired by this migration and is no longer maintained.

These are configured defaults, not proof of a running session's effective selections.
Read `PERFORMANCE.md` for the reasoning and measurement limits, not on every coding task.

## Review, commit, and apply

Prerequisites are Git, mise, and uv. Review `mise.toml` before trusting it. In the
maintained local `personal` checkout:

```sh
mise trust
mise run orchestrator:sync
mise run orchestrator:validate
mise run orchestrator:test
mise run orchestrator:plan
# Review and commit local edits before applying them.
mise run orchestrator:apply
mise run orchestrator:status
# Publish approved local commits without force-pushing:
git push origin personal
```

`sync` fast-forwards only from this fork's `personal` branch. It does not install
anything or merge an unmerged PR. For remote candidates, review and test their
branch first. Merge approved changes into `personal`, then sync, validate/test/plan,
and apply the clean committed result. Reuse valid test evidence when code and the
relevant environment did not change. A plan needs the maintained checkout identity;
do not bypass the `personal` branch guard to install a PR branch.

The source validator uses the documented model/effort matrix checked 2026-09-20;
it is not a live availability test. Before installing new selections, also inspect
your current Codex model catalog and configuration precedence. An optional read-only
check consumes an explicitly chosen local JSON catalog:

```sh
mise run orchestrator:compatibility --model-catalog /path/to/current-model-catalog.json
```

Replace the path locally. The supported input has a `models` array, with each model's
`slug` and `supported_reasoning_levels` objects containing `effort`. Unknown schemas,
missing models, or unsupported efforts fail closed. Refresh or obtain the catalog
using the installed Codex version's documented controls; do not fabricate entries.
A stale catalog, an advertised model, or valid TOML does not prove account access or
actual selection. Check project/profile overrides and effective role/effort in a new
session; do not silently substitute models on failure.

## One-time managed-file migration

The maintained source now contains **11 files**: one config fragment, seven roles,
one skill, and two references. Apply recognizes the original **version-1 receipt
for nine files** and migrates it to version 2 without a new bootstrap or deleting
state. The only new destinations allowed in that migration are:

- `~/.codex/agents/solver.toml`
- `~/.agents/skills/astra-orchestrator/references/maintenance.md`
- `~/.agents/skills/astra-orchestrator/references/semble.md`

Every original managed file must exist and match its recorded state (only the owned
config values are compared). All three added destinations must be absent. An existing
file, even with identical bytes, is an ownership collision: preserve it and reconcile
deliberately. Do not delete it or the receipt merely to silence the guard. New files
are created exclusively, so a late local file cannot be overwritten.

The same migration retires `~/.codex/agents/research_verifier.toml`. The installed
file must still match the version-1 receipt; missing or locally edited content blocks
migration. Apply backs it up before removal and restores it if the migration rolls
back. It is absent from the version-2 receipt and maintained source.

After migration all 11 files are tracked; a missing solver or reference is drift,
not permission to recreate it silently. A genuinely unmanaged installation still
requires an explicitly prepared private baseline of every existing managed file.
This remains a maintenance workflow, not a blank-machine installer.

## Apply protections and recovery

Apply merges only the allowlisted config keys while preserving unrelated settings
and comments. Roles, skill, and references are copied literally. No unrelated files
are removed. In particular, `agents.interrupt_message`, permissions, MCP/app settings,
and private machine configuration remain local.

The workflow checks clean committed source, exact allowed file paths, role TOML,
skill YAML and reference links, documented model/effort pairs, secrets patterns,
installed hashes/values, symlinks, checkout identity, and concurrent edits. It locks
other applies, snapshots and backs up affected state, and rechecks before writing.
It skips unchanged file bytes. Report validation as structural/catalog checks,
not proof that a model was actually invoked. Pattern scans are not a secrecy guarantee.

State: `~/.local/state/astra-orchestrator/state.json`.
Backups: `~/.local/state/astra-orchestrator/backups/`.
The apply output identifies the exact backup. Keep both private: config backups
include unrelated settings. The manifest records each original mode and backup path;
new migration files have `absent: true` instead of a backup file. The prior receipt
is preserved. Do not publish these files to prove installation.

On a write failure, rollback restores attempted changes and the matching receipt,
removes newly created managed files, and removes only empty directories created by
that attempt. It preserves conflicting later edits and reports incomplete rollback
rather than destroying them. Individual file publication is atomic, but a process kill
or machine failure across multiple files may still require manual recovery.

For recovery, preserve newer local work first. Restore originals and the matching
receipt from one backup; for `absent: true` entries remove only the corresponding
files created by that apply after confirming there is no newer work to preserve.
Do not mix backup generations. An old version-1 receipt must have exactly its original
nine managed files; version 2 has eleven. Do not edit receipt hashes to bypass drift.

A moved checkout or changed origin requires deliberate identity reconciliation.
On ordinary drift, compare installed content, maintained source, and the recorded
commit; preserve approved local edits in the repository before reconciling installation.
There is no force-overwrite option. Start a new Codex session after an apply changes
configuration, role instructions, or the skill. Apply does not restart running sessions.

## Original-project updates

`origin` is this fork; `upstream` is
`https://github.com/donvito/codex-astra-luna-orchestrator.git`.
Keep `main` upstream-only. Review upstream fixes separately and port only approved
changes to `personal`; never merge `personal` into `main` or auto-apply upstream changes.
Inherited `profiles/`, old guides, and `setup.sh`/`setup.ps1` remain reference material,
not this setup's installer. Upstream PR #15 is not adopted.

The original interrupted customization checkout and its recovery issues are separate.
This workflow does not repair it, import its private history, or authorize its cleanup.
