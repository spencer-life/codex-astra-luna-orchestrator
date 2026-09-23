# Personal v3 orchestration

The maintained personal setup uses GPT-6 Sol as the default root and GPT-6 Luna for
bounded execution roles. The active session model remains the root, so picker/CLI
overrides are supported.

```text
active root (default Sol Medium)
├── explorer       Luna Medium · read-only
├── researcher     Luna Medium · read-only
├── worker         Luna High   · workspace-write
├── tester         Luna High   · workspace-write
└── reviewer       Sol Medium  · read-only
```

Generic fallback is Luna High. Spawned concurrency is four. Semble is called directly
through its MCP/CLI; there is no solver or Semble-search subagent.

The managed config fragment is:

```toml
model = "gpt-6-sol"
model_reasoning_effort = "medium"

[features.context_management]
experimental_mode = true

[agents]
enabled = true
max_concurrent_threads_per_session = 4
default_subagent_model = "gpt-6-luna"
default_subagent_reasoning_effort = "high"
```

The installer merges only these owned settings. Local permission profiles, Auto-review,
MCP/plugins, service tier, voice/audio settings, and other machine-specific config are
preserved.
