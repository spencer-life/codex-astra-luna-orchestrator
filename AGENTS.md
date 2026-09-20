# Codex project instructions

## Maintained personal source

On `personal`, `orchestrator/` is the only maintained installation source.
Read `PERSONAL.md` before changing or applying it. ChatGPT and Codex must edit
the same repository files, validate, review, and commit before applying with
`mise run orchestrator:apply`. Never reconstruct the skill from a prompt or
silently overwrite an edited installed copy.

Keep `main` as upstream reference. Do not merge personal changes into `main`,
automatically install upstream templates, or adopt upstream PR #15. Inherited
`profiles/` and `setup.*` are reference material, not the personal apply path.
Preserve unrelated local configuration. Do not import full machine configs,
credentials, session history, logs, or machine-specific paths into this repo.

Use Conventional Commit subjects (`feat:`, `fix:`, `docs:`, `chore:`, with an
optional scope) consistent with the existing customization commits.

## Delegation

For complex coding tasks, use the `astra-orchestrator` skill when its trigger conditions match.

The root agent owns architecture, decomposition, integration, and final verification.
Prefer specialized subagents for bounded exploration, implementation, testing, review, and technical research.

Do not delegate trivial work merely for parallelism.
Do not let multiple implementation agents edit the same files without explicit ownership boundaries.
User instructions always take precedence over this orchestration policy.
