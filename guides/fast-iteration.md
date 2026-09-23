# Fast iteration

For latency-sensitive work, prefer a **GPT-6 Luna** root selected in the model picker.
Luna Medium is a good starting point for coordinated edits; Luna Low fits very small,
well-bounded work.

Fast mode is an independent service-tier choice and is not pinned by this repository.
Current GPT-6 Fast usage is charged at a higher Codex credit multiplier, so enable it
per session only when latency is worth the extra usage.

The orchestration skill respects the active session model and service-tier choice.
