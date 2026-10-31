# Runtime boundaries

The experiment is source-controlled under `experiments/terra/` on
`experiment/terra-6.1-orchestrator`. Its launcher is
`scripts/terra_orchestrator.py`. The original `orchestrator/` source and guarded
`orchestrator:apply` workflow remain the stable personal setup.

Do not apply the experiment through the stable installer, rewrite receipt identity
or hashes, change `personal`/`main`, or copy private config/auth into the repository.
The launcher uses session-only CLI model/default-agent/role-file overrides and an
explicit initial skill reference. It does not install a second global skill, edit
AGENTS.md, replace config, copy credentials or change service tiers/permissions.
Normal Codex runtime may still update its own ordinary session state.

Named Codex profiles cannot currently switch the entire agent roster. Do not claim
`codex -p terra` activates this experiment. Use the supplied launcher. The same
role names override matching roles only in that session; unrelated custom roles
remain available. Select the bundled roles for this experiment, not similarly
named substitutes. The skill is loaded by its explicit source path, not a new
global implicit-discovery installation.

Before first use on the real machine: verify the actual executor and installed CLI,
current schema/help, model catalog, inherited project instructions, tools and
permissions. The launcher checks a clean committed experiment checkout, origin,
minimum CLI version and a freshly captured catalog before launching. A catalog
advertisement is not a successful model request. Verify the actual parent and
spawned-role selections in a new session, with raw event/config evidence.

Role-file model/effort pins win over defaults. Custom role instructions do not
create a distinct filesystem sandbox. Use parent permissions and existing approval
controls for enforcement. Current docs mark experimental context management as
unavailable; this experiment does not force that setting or repair stable drift.

Service tier (including Fast/Ultrafast), authentication, providers, MCP/plugins,
voice/audio and approval settings stay local. Do not enable Fast just because a
role is Terra. Respect an explicit existing choice and verify it at runtime.

If a required model, tool, custom-role override or skill cannot load, stop adoption
and report the exact failure. Do not silently alias models or use a legacy custom
role mechanism that the installed release ignores. Exiting the experimental
session and starting Codex normally restores the unchanged installed workflow;
an existing experimental session is not retroactively changed by that action.
