# Token and usage measurement

There is no single cost or latency number for this setup. Measure normal tasks from
the rollout logs Codex already writes under `~/.codex/sessions`.

Use the maintained read-only reporter:

```sh
scripts/token_usage.py --list --date YYYY-MM-DD
scripts/token_usage.py --root ROOT_ID
scripts/token_usage.py --root ROOT_ID --since START_ISO8601 --until END_ISO8601 --format json
```

It groups root and subagent threads, separates Auto-review/guardian usage by default,
reports uncached/cached/output tokens, model/effort and service-tier evidence when
recorded, and calculates a Standard-rate credit equivalent.

Rates checked 2026-09-22:

| Model | Uncached input | Cached input | Output |
| --- | ---: | ---: | ---: |
| GPT-6 Astra | 250 | 25 | 1250 |
| GPT-6 Sol | 50 | 5 | 250 |
| GPT-6 Luna | 2.5 | 0.25 | 12.5 |
| GPT-5.6 Sol | 100 | 10 | 500 |
| GPT-5.6 Terra | 50 | 5 | 300 |
| GPT-5.6 Luna | 5 | 0.5 | 30 |

The GPT-5.6 rows remain because the reporter also reads historical sessions. The
credit equivalent is a comparison baseline, not an actual bill or subscription-window
charge.

For a useful v3 comparison, run a few representative tasks with the default Sol
Medium root, then comparable tasks with Luna as the primary session model. Record wall
time, accepted outcome, repair/review turns, cache hit rate, and per-model usage.
Do not infer GPT-6 speed from older GPT-5.6 runs or from intelligence benchmark scores.

See [PERFORMANCE.md](../PERFORMANCE.md) for the current routing assumptions and
measurement limits.
