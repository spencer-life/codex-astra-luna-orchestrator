# Maintaining this setup

Maintained source: https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal
Read that repository's current `AGENTS.md` and `PERSONAL.md` before maintenance.
`orchestrator/` is authoritative; installed `~/.codex/agents/` and
`~/.agents/skills/astra-orchestrator/` are applied copies. The config fragment
owns only its declared settings, not the entire installed `~/.codex/config.toml`.

Make approved changes in the repository, validate/test/review and commit, then
use its guarded mise sync/plan/apply/status workflow. A sync does not install an
unmerged PR. Do not regenerate the skill from a prompt or normally edit applied
copies. Preserve drift, unrelated settings, explicit session choices, permissions,
MCP/plugins, and service tiers. Never publish private configuration, logs, receipts,
or backups. Do not use inherited upstream installers or automatically import
upstream profiles; `main` remains upstream reference and PR #15 was not adopted.

The allowlisted migration adds the solver and these references to an existing
v1 receipt. The new destinations must be absent; an unexpected existing file is
a conflict even when its contents appear identical. Do not delete receipts or
local files to defeat that guard. Follow `PERSONAL.md` for deliberate reconciliation
and restoring files plus the matching receipt from one backup.

`orchestrator:validate` checks source structure, metadata, reference paths, and
a documented model/effort matrix; it does not prove account availability. Use
`orchestrator:compatibility --model-catalog PATH` on a current locally obtained
Codex model catalog, then verify effective session/spawn settings locally.
Catalog entries are evidence of advertised support, not proof a request ran.
Role files pin their settings. Never silently alias unavailable model IDs or
rewrite the catalog. Treat `max_depth = 1` as a preserved setting whose local
support needs verification; flat delegation is also an explicit skill policy.

After applying changed configuration/instructions, start a new Codex session.
The workflow does not restart existing sessions or change an explicitly selected
model. Read `PERFORMANCE.md` only for performance investigations and usage reporting.
