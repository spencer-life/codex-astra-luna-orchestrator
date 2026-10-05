# Personal Codex orchestrator

## Source and scope

Use the receipt-bound `personal` checkout recorded in
`~/.local/state/astra-orchestrator/state.json`. Read [PERSONAL.md](PERSONAL.md)
before source changes or installation; it owns recovery and migration details.
`orchestrator/` is the installation source; installed files are applied copies.
Preserve local edits and unrelated configuration. Never rewrite receipt identity
or hashes to bypass guards, and never publish private configuration or backups.

`origin` is the personal fork; `upstream` is the original donvito repository.
Keep `main` upstream-only. Inherited `profiles/` and `setup.*` are reference
material; use the guarded personal tasks for installation.

## Update workflow

1. Run `mise run orchestrator:sync` from a clean `personal` checkout.
2. For original-project updates, run `mise run orchestrator:upstream` to fetch and
   preview changes. Port reviewed changes to `orchestrator/`, preserving existing
   model and effort selections unless the user requests different values.
3. Run `mise run orchestrator:check`, review the diff, and commit using a
   Conventional Commit subject. Keep upstream provenance in `PERSONAL.md` current.
4. Run `mise run orchestrator:plan`, inspect the proposed changes, then run
   `orchestrator:apply` and `orchestrator:status` through Mise. Push `personal`.

`main` is the skill preview's last-reviewed upstream snapshot; advance it only
when the corresponding upstream skill changes have been ported. Apply requires
clean committed source. Start a new Codex session after installed instructions change.

## Collaboration

Use `astra-orchestrator` for substantive work and delegate bounded discovery,
implementation, and useful independent checks. The root owns architecture,
integration, and final verification; keep one writer per file.
For performance investigations and usage reporting, read [PERFORMANCE.md](PERFORMANCE.md).
