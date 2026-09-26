# Personal Codex orchestrator

The maintained setup is on the
[`personal` branch](https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal),
with installable source under [`orchestrator/`](orchestrator/). Installed Codex
files are applied copies, not a competing source.

**ChatGPT and Codex: edit the same maintained files, validate, review, commit, then
apply.** Read [PERSONAL.md](PERSONAL.md) for the guarded workflow and recovery.
[PERFORMANCE.md](PERFORMANCE.md) records the current routing and measurement basis.

```sh
mise run orchestrator:validate
mise run orchestrator:test
mise run orchestrator:compatibility --model-catalog /path/to/current-model-catalog.json
mise run orchestrator:plan
# After review and merge/commit on personal:
mise run orchestrator:apply
mise run orchestrator:status
```

The default root is GPT-6 Sol at high reasoning. A model or effort selected in the
Codex picker/CLI remains the active root for that session, so a Luna-only session is
supported without rewriting the shared configuration. Explorer/researcher use GPT-6
Luna Medium; worker/tester and generic fallback use GPT-6 Luna High; the independent
read-only reviewer uses GPT-6 Sol High. Spawned concurrency is capped at four.

Semble is used directly through its installed MCP/CLI rather than through a dedicated
subagent. The maintained configuration enables experimental context management.
`max_depth` is no longer managed because current Codex V2 ignores that V1-only
setting.

The v3 maintained source contains **nine files**: one config fragment, five role files,
one routing skill, and two on-demand references. Guarded migration supports both v1
and v2 receipts, retiring obsolete roles and the previously managed `max_depth`
without overwriting unrelated local configuration.

The repository deliberately does **not** own the full `~/.codex/config.toml`.
Workspace Tools permission profiles, Auto-review/approval choices, MCPs/plugins,
service tier, audio devices, voice selection, desktop preferences, credentials, and
machine-specific settings stay local.

Codex CLI 0.156.0 is the compatibility target for this migration. Voice conversations
are enabled by default in that release; no portable voice flag is required here.
Machine-local audio and realtime preferences remain outside the managed fragment.

The skill's filesystem path and frontmatter name remain `astra-orchestrator` for
installation compatibility, while its user-facing heading is **Codex Orchestrator**.

`main`, inherited `profiles/`, and `setup.sh`/`setup.ps1` remain upstream
reference material rather than the personal apply path. Original project:
[donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator).
Licensed under [Apache 2.0](LICENSE).
