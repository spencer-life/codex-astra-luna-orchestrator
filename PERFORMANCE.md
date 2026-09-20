# Performance and measurement

Maintained setup: `personal`. Research checked September 20, 2026. This is a
maintenance reference, not an extra skill that every agent must load.

## Decision

Keep Astra Low for the root/reviewer; Luna High for explorer/worker/tester;
Luna Medium for research/search; three flat subagents at most. Preserve the
separate research verifier, approvals, sandboxes, and service tiers.

Optimize time to a correct, verified result before raw token totals. This change
addresses unnecessary review polling, repeated checks, late compatibility
probes, and misleading measurements. It does not claim a measured speedup or
that these efforts are a benchmark-proven optimum for the custom topology.

## Why these changes

OpenAI's [Astra guidance](https://developers.openai.com/api/docs/guides/latest-model)
says to calibrate verification and repeat checks for changes, failures, or
unresolved concerns rather than automatically. The
[skills guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra)
favors focused instructions over broad mandatory procedures.

The [subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
places Luna on narrow, clear work and High on logic/assumption/edge-case analysis.
Medium is a balanced default, not proof that every existing High role should be
lowered. More effort can improve difficult reasoning but adds time and tokens.
The [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)
treats effort as a tuning control rather than the first response to quality issues.

[Artificial Analysis: Luna High versus Max](https://artificialanalysis.ai/models/comparisons/gpt-5-6-luna-high-vs-gpt-5-6-luna)
showed Intelligence Index v4.3.2 scores of 32 versus 37, approximately 14k versus
41k output tokens per index task, and 7k versus 28k reasoning tokens. Reasoning
is included in output. Max has a capability benefit but is not free speed.
These are standalone evaluation aggregates, not this orchestrator's outcomes.
AA's "time per task" is calculated decode time excluding first-token latency
and overhead; its end-to-end response metric is a 500-token response calculation.
Neither is a Codex implementation duration or subscription charge.

The [latency guide](https://developers.openai.com/api/docs/guides/latency-optimization)
supports fewer unnecessary requests and genuinely independent parallel work.
[Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching)
reuses input processing, not the answer. A high cache hit rate does not make an
unnecessary request useful or free. Keep stable instructions and concise evidence;
do not add forced compaction, context-window overrides, API-only cache parameters,
or service-tier changes without supported controls and relevant measurements.

## Coordination rules

Review a ready, stable change. Return findings and end the review turn; the parent
resumes review for a ready delta instead of leaving a reviewer polling the writer.
Early design review is a separate bounded assignment, not a live progress monitor.

Assign routine checks an owner. Share the exact command, result, relevant
environment, and tested state, including uncommitted changes. HEAD alone is not a
snapshot of a dirty working tree. Reuse valid execution evidence while reviewing
code independently. Repeat for invalidated evidence, a concrete concern, or a
purposeful independent final check; never skip required acceptance checks.

When a parser/runtime/configuration assumption controls the implementation,
probe it early and read-only against the actual local environment when available.
Keep private inputs local. A representative fixture is useful but is not proof
of real-environment compatibility. No unfinished configuration is applied as a probe.

## Read-only usage reports

Use the maintained mise task; arguments are passed to the script:

```sh
mise run orchestrator:usage --root ROOT_ID
mise run orchestrator:usage --root ROOT_ID --include-guardian
mise run orchestrator:usage --root ROOT_ID --since START_ISO8601 --until END_ISO8601 --format json
```

Replace placeholders locally. Both timestamps require `Z` or an explicit UTC
offset. Choose bounds from task events, not guesswork. The interval is start
inclusive and end exclusive. It counts whole response usage records by their
recorded timestamps, not portions of inference that crossed a boundary. A caller
must verify that the selected range actually represents the desired task.

Full reports retain the recorded session/thread spans, which include inactive
gaps and overlap. Do not sum them or label them compute time. Scoped reports also
show the selected interval, separate from the full recorded span. The reporter
does not infer tool-wait, queue, inference, or idle categories from absent data.

`--date` limits file discovery, not event timestamps; it may omit related threads
on other days. It cannot be combined with scoped reports. Use an exact root ID
rather than `--latest` for reproducible comparisons. Related files must be present.
Legacy cumulative counters cannot be allocated to an interval: scoped reporting
refuses them rather than guessing. Missing usage timestamps also prevent scoping.
Malformed JSONL stops a report instead of silently dropping records; wait until
an actively written log is stable before retrying. Empty usage is flagged as
unavailable, not proof of zero consumption.

Token subtotals explicitly distinguish included agents, excluded automatic
reviews, and all discovered records. Reasoning is already inside output. Reports
retain response counts and mixed effort labels. JSON keeps the existing `threads`
array and adds `measurement`; thread-level `model`/`effort` is last observed
metadata, while `efforts_by_model` describes the counted response records.

Allowance window labels come from recorded `window_minutes`, never the
`primary`/`secondary` slot names. Missing windows/reset metadata remain unknown;
changed windows or reset boundaries are marked non-comparable. Snapshot times
may cover less than the requested interval. Account-level percentage movement
is not an attributable task bill. No API cost is estimated from these counters.

Logs, reports, paths, receipts, and backups remain private. Only synthetic test
fixtures belong in this public repository. Do not publish a raw JSON report to
prove a test passed.

## Evaluate after applying

Compare a few representative tasks with the same success criteria and recorded
model/effort/service tier. Prioritize accepted outcomes, necessary repair turns,
implementation elapsed time, no-update polling, redundant checks, response count,
and token categories. Record unknown time honestly. Check that an apparent speed
improvement did not remove meaningful verification. No always-on telemetry or
new benchmarking platform is required.

Candidate code tests and instruction review do not prove new model behavior.
Local Codex still needs to validate the complete mise workflow and installed-file
plan, confirm current log compatibility privately, then merge into `personal`
and use the guarded sync/apply/status workflow in `PERSONAL.md`.
