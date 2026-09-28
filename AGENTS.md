# Codex project instructions

## Maintained personal source

On `personal`, `orchestrator/` is the only maintained installation source.
Read `PERSONAL.md` before changing or applying it. ChatGPT and Codex must edit
the same repository files, validate, review, and commit before applying with
`mise run orchestrator:apply`. Never reconstruct the skill from a prompt or
silently overwrite an edited installed copy.
Before apply or recovery, inspect the installed receipt and follow the
receipt-bound checkout guidance in `PERSONAL.md` and the maintenance reference.

Keep `main` as upstream reference. Do not merge personal changes into `main`,
automatically install upstream templates, or adopt upstream PR #15. Inherited
`profiles/` and `setup.*` are reference material, not the personal apply path.
Preserve unrelated local configuration. Do not import full machine configs,
credentials, session history, logs, or machine-specific paths into this repo.

Use Conventional Commit subjects (`feat:`, `fix:`, `docs:`, `chore:`, with an
optional scope) consistent with the existing customization commits.

For performance investigations and usage reporting, read `PERFORMANCE.md`.

## Delegation

For substantive coding work matching the `astra-orchestrator` skill, use it.
Root-only work is limited to genuinely small, localized tasks with a known
implementation surface.

Delegation is mandatory when any of these apply:

- repository exploration is needed before implementation or diagnosis
- the relevant implementation surface is not already known
- multiple files, modules, services, or components need inspection
- the task spans multiple files, modules, services, or components
- two or more independent workstreams exist
- debugging requires tracing across components
- external or version-specific facts need verification
- implementation and verification benefit from separate context
- an independent post-change review is materially useful
- the user explicitly asks for delegation, parallelism, agents, or subagents

When a trigger applies, spawn the appropriate specialist before performing that
bounded work in the root. For substantive read-only repository discovery, use the
explorer; keep root reads to trivial known-location reads, exact lookups, and evidence
needed for root-owned architecture or integration. Do not silently replace required
delegation with root execution merely to avoid an agent hop.

The root agent owns architecture, decomposition, integration, and final verification.
Give each delegated task clear scope and ownership, and run independent tasks in
parallel when useful.

Do not delegate trivial work merely for parallelism.
Do not let multiple implementation agents edit the same files without explicit
ownership boundaries.
User instructions always take precedence over this orchestration policy.
