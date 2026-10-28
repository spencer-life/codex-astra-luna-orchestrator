# Personal Codex orchestrator

The maintained setup is on the
[`personal` branch](https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal),
with installable source under [`orchestrator/`](orchestrator/). Installed Codex
files are applied copies, not a competing source.

**ChatGPT and Codex: edit the same maintained files, validate, review, commit, then
apply.** Read [PERSONAL.md](PERSONAL.md) for the guarded workflow and recovery.
[PERFORMANCE.md](PERFORMANCE.md) records the current routing and measurement basis.

```sh
mise run orchestrator:upstream  # Preview original-project changes when updating
mise run orchestrator:check
mise run orchestrator:plan
# After review and merge/commit on personal:
mise run orchestrator:apply
mise run orchestrator:status
```

The default root is GPT-6.1 Sol at high reasoning. A model or effort selected in the
Codex picker/CLI remains the active root for that session, so a Luna-only session is
supported without rewriting the shared configuration. Explorer/researcher use GPT-6
Luna Medium; worker/tester and generic fallback use GPT-6 Luna High; Terra
ui_specialist uses GPT-6.1 Terra Extra High for computer-use, default no-edit
inspection, and explicitly delegated scoped UI implementation; the independent
no-edit reviewer uses GPT-6.1 Sol High. Spawned concurrency is capped
at four. Terra edits project files only in explicitly delegated implementation
mode; inspection is the default. Actual tool permissions and sandboxing are
inherited from the parent Codex session.

The routing skill and role instructions follow the original upstream templates,
with personal model and effort selections retained. The root owns architecture,
integration, and final verification; bounded work and useful independent checks
are delegated to specialists.

Semble is used directly through its installed MCP/CLI rather than through a dedicated
subagent. The maintained configuration enables experimental context management.
`max_depth` is no longer managed because current Codex V2 ignores that V1-only
setting.

The v4 maintained source contains **ten files**: one config fragment, six role files,
one routing skill, and two on-demand references. Guarded migration supports v1,
v2, and v3 receipts, adds the single Terra specialist without overwriting pre-existing files, retires
obsolete roles for v1/v2, and preserves unrelated local configuration.

The repository deliberately does **not** own the full `~/.codex/config.toml`.
Workspace Tools permission profiles, Auto-review/approval choices, MCPs/plugins,
service tier, audio devices, voice selection, desktop preferences, credentials, and
machine-specific settings stay local.

Codex CLI 0.156.1 was the v3 validation target; the Terra role requires Codex CLI
0.159.0 or newer and an available `gpt-6.1-terra/xhigh` catalog entry. Voice conversations
were enabled in 0.156.1; no portable voice flag is required here.
Machine-local audio and realtime preferences remain outside the managed fragment.

The skill's filesystem path and frontmatter name remain `astra-orchestrator` for
installation compatibility, with the upstream orchestrator structure adapted to the configured model efforts.

`main`, inherited `profiles/`, and `setup.sh`/`setup.ps1` remain upstream
reference material rather than the personal apply path. Original project:
[donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator).
Licensed under [Apache 2.0](LICENSE).
