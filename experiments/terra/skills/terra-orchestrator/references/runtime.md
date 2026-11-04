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
the source, then verify what a new session loads. Check the active root selection
against the bundle's supported pairs, separately from the skill and role files.
If it falls outside those pairs, report the selection as a blocker and ask the
user to select a supported root before proceeding with the Terra workflow.

For a session-only trial, use the supplied launcher. It applies root and named-role
overrides for that session. Its preflight checks the clean committed source, branch,
origin, installed CLI, and fresh model catalog. Native startup and launcher
preflight are separate paths. After the trial, start Codex normally to return to the
installed defaults.

Preserve user and project permissions, approval settings, providers, plugins, and
service tier. If the required CLI, catalog, model, tools, or role loading is
unavailable, report the specific blocker and the scope already verified.
