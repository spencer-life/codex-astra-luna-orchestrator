# Performance and measurement

Maintained source: `personal`. Decisions and documentation checked **September 22,
2026**. This is an on-demand performance reference, not context every coding turn
needs.

## Selected baseline

The v3 starting policy is:

| Role | Model / effort |
| --- | --- |
| root | active session; default GPT-6 Sol High |
| explorer | GPT-6 Luna Medium |
| researcher | GPT-6 Luna Medium |
| worker | GPT-6 Luna High |
| tester | GPT-6 Luna High |
| reviewer | GPT-6 Sol High |
| generic fallback | GPT-6 Luna High |

Semble is a direct MCP/CLI tool, not a subagent. Spawned concurrency is capped at
four. Experimental context management is enabled. No permanent Terra role, solver,
Semble-search agent, routine Max default, forced Fast mode, or dynamic model router
is added.

The active primary-session model remains the root. Selecting GPT-6 Luna in the
picker is therefore a supported fast/cheap root session; the independent reviewer
remains pinned to Sol High when used.

Use the worker when the solution direction is sufficiently clear. Keep architecture,
ambiguous cross-component reasoning, and integration with the root. Tester and
reviewer are selective evidence gates, not mandatory steps for every trivial edit.

## Evidence basis

Primary references:

- [GPT-6 Sol](https://developers.openai.com/api/docs/models/gpt-6-sol)
- [GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)
- [Reasoning guidance](https://developers.openai.com/api/docs/guides/reasoning)
- [Codex pricing](https://learn.chatgpt.com/docs/pricing)
- [Codex changelog](https://learn.chatgpt.com/docs/changelog)
- [GPT-6 skill guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
- [Artificial Analysis GPT-6 Sol release](https://artificialanalysis.ai/models/releases/gpt-6-sol)
- [Artificial Analysis GPT-6 Luna release](https://artificialanalysis.ai/models/releases/gpt-6-luna)

At this decision date, public Artificial Analysis capability/cost results were useful
for effort selection, but complete GPT-6 latency measurements were not available.
Do not turn benchmark intelligence scores into percentages or invent task-speed
ratios. Measure end-to-end speed on real Codex work.

## Coordination and context

Review a ready stable change rather than polling a writer. Assign routine checks one
owner and share command, result, environment, and actual working-tree state. Reuse
still-valid test evidence; rerun after relevant source, test, dependency,
configuration, command, or environment changes.

Keep root context focused on decisions, material evidence, diffs, and unresolved
risks. Use Semble directly where semantic discovery helps. Load the detailed Semble
reference only for version/index/coverage or maintenance questions.

Experimental context management is enabled in the managed config. Treat its effects,
prompt-cache behavior, and mid-session effort/model switching as runtime behavior to
observe rather than assumptions to encode into the routing policy.

## Read-only usage reports

`scripts/token_usage.py` groups recorded Codex rollout events by root session and
reports per-thread/model usage, input sizes, tiers, cache use, and a Standard-rate
credit equivalent.

```sh
mise run orchestrator:usage --root ROOT_ID
mise run orchestrator:usage --root ROOT_ID --include-guardian
mise run orchestrator:usage --root ROOT_ID --since START_ISO8601 --until END_ISO8601 --format json
```

Whole response records are counted by timestamp; the reporter does not infer queue
time, tool waits, compute time, or task boundaries. Auto-review/guardian threads are
separated by default. Requested service tier is not proof of the served tier.

### Standard-rate comparison, not billing

Rates checked **2026-09-22**, credits per one million uncached input / cached input /
output tokens:

| Model | Uncached | Cached | Output |
| --- | ---: | ---: | ---: |
| GPT-6 Astra | 250 | 25 | 1250 |
| GPT-6 Sol | 50 | 5 | 250 |
| GPT-6 Luna | 2.5 | 0.25 | 12.5 |
| GPT-5.6 Sol | 100 | 10 | 500 |
| GPT-5.6 Terra | 50 | 5 | 300 |
| GPT-5.6 Luna | 5 | 0.5 | 30 |

Legacy rates stay in the script so historical session logs remain comparable.

The formula is:

`((input - cached) * uncached_rate + cached * cached_rate + output * output_rate) / 1e6`

Output already includes reasoning. The result is a **Standard-rate credit equivalent**
for comparison, not a bill or actual allowance charge. Fast multipliers, promotions,
tools, and other adjustments are not applied.

## Benchmark the v3 setup

Use a handful of representative real tasks instead of building a large benchmark
harness. For each task record:

- accepted outcome and missed requirements;
- wall-clock completion time;
- repair turns and reviewer findings;
- root and subagent model/effort;
- uncached input, cached input, and output;
- cache hit rate;
- requested/recorded service tier when present.

Useful comparisons are:

1. default Sol High root with the normal specialists;
2. Luna Medium or High as the primary session root via the picker;
3. root-only execution when the task is cohesive enough that delegation adds overhead.

Repeat enough runs to avoid treating one stochastic result as a conclusion.

## Historical sample

The older sample run in repository history used Astra Low plus GPT-5.6 Luna and is
valuable only as a scale reference for orchestration overhead. It is **not** evidence
for GPT-6 v3 speed or usage. Use fresh v3 runs before changing efforts again.

Logs, private reports, local model catalogs, receipts, backups, and machine paths stay
local. Only synthetic fixtures belong in this public repository.
