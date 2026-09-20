# Personal Astra orchestrator

The maintained setup is on the [`personal` branch](https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal), in [`orchestrator/`](orchestrator/). Installed Codex files are applied copies, not a competing source.

**ChatGPT and Codex: edit the same maintained files, validate, review, commit, then apply.** Read [PERSONAL.md](PERSONAL.md) for the guarded workflow, migration, and recovery; [PERFORMANCE.md](PERFORMANCE.md) explains routing and metrics.

```sh
mise run orchestrator:validate
mise run orchestrator:test
mise run orchestrator:plan
# After review and commit on personal:
mise run orchestrator:apply
mise run orchestrator:status
```

Astra Low coordinates or executes directly. Luna High is the bounded worker/tester and generic fallback; Luna Medium handles bounded exploration/research/search. A Sol Medium solver handles demanding delegated work without first requiring a Luna failure. Astra Low reviews consequential changes; the separate Sol High research verifier is unchanged. Use at most three open subagents, flat unless explicitly authorized. No mandatory specialist pipeline or Fast-mode change.

The source contains one config fragment, eight roles, a compact skill, and two on-demand references. The guarded version-1 to version-2 migration adds the solver and references only when their destinations are absent; existing ownership collisions stop the update. Backups, drift detection, and unrelated settings remain protected. See the maintenance guide before applying.

`main`, inherited `profiles/`, old guides, and `setup.sh`/`setup.ps1` remain upstream reference material, **not this personal setup's installer**. Review original-project updates separately. Upstream PR #15 is not adopted.

Credentials, full machine configuration, MCP/app settings, sessions, private reports, receipts, and backups stay local. Original project: [donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator). Licensed under [Apache 2.0](LICENSE).
