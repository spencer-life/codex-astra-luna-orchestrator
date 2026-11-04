# Runtime and activation

Use `experiments/terra/` on `experiment/terra-6.1-orchestrator` as the Terra source.
Use `scripts/terra_orchestrator.py` for session-only activation. Maintain the stable
installer, receipt, and branches through their own workflow.

## Verify effective routing

Use the bundled named roles with their pinned model and effort. The source
validator checks the Terra, Sol, and Luna model and effort pairs in the bundle.
Treat catalog results as advertised availability. Confirm the actual root, child
roles, models, efforts, loaded skill, and available tools in a new session using
raw settings and spawn events. Report conflicting settings or missing capabilities
with the evidence needed to resolve them.

Verify behavior with a targeted, blinded case from the Terra evaluation catalog.
Give the evaluated session the request and fixture. Keep the grading rubric with the
evaluator, then compare observed artifacts and agent activity against it.

## Choose the activation path

For an existing local setup that links to this checkout, review and fast-forward
the source, then verify what a new session loads. The user selects the root model
in Codex. Record the effective selection separately from the loaded skill and
named roles.

For a session-only trial, use the supplied launcher. It reads the bundle's root and
named-role settings and applies them for that session. Its preflight validates the
configured model and effort pairs against a fresh catalog and checks the source,
branch, origin, and CLI. Native startup and launcher preflight are separate paths.
After the trial, start Codex normally to return to the installed defaults.

Preserve user and project permissions, approval settings, providers, plugins, and
service tier. If the required CLI, catalog, model, tools, or role loading is
unavailable, report the specific blocker and the scope already verified.
