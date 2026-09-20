# Personal Astra orchestrator

The maintained setup is on the [`personal` branch](https://github.com/spencer-life/codex-astra-luna-orchestrator/tree/personal), in [`orchestrator/`](orchestrator/). The installed Codex files are applied copies of this source.

**ChatGPT and Codex: read and edit the same files on `personal`, then validate, review, commit, and apply.** See [PERSONAL.md](PERSONAL.md) for the exact workflow and recovery instructions.

```sh
mise run orchestrator:validate
mise run orchestrator:plan
# After review and commit:
mise run orchestrator:apply
```

`main` remains an original-project reference branch. The inherited `profiles/`, guides, `setup.sh`, and `setup.ps1` are upstream reference material, **not the installer for this personal setup**. Do not use them to update the installed customization. Original-project changes must be reviewed separately; upstream PR #15 is not adopted.

Defaults: Astra Low root/reviewer; Luna High explorer/worker/tester and fallback; Luna Medium researcher/Semble search; three concurrent subagents, no nested delegation by default. The research verifier retains its imported settings and instructions unchanged.

The source contains only the orchestrator skill, seven role files, and selected orchestration settings. Credentials, machine permissions, MCP/app configuration, sessions, and logs stay local. The apply workflow preserves unrelated configuration and stops if managed installed files have drifted.

Original project: [donvito/codex-astra-luna-orchestrator](https://github.com/donvito/codex-astra-luna-orchestrator). Licensed under [Apache 2.0](LICENSE).
