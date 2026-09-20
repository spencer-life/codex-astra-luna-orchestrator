# Performance and measurement

Maintained source: `personal`. Decisions and documentation checked September 20, 2026.
This is an on-demand maintenance reference, not instructions every coding agent loads.

## Selected baseline, not a proven universal optimum

Keep Astra Low root/reviewer; use Luna Medium for bounded exploration/research/search,
Luna High for bounded implementation/testing and fallback, and Sol Medium as the
new demanding-task solver. The unused custom research verifier is removed.
No permanent Terra role, routine Max, Fast-mode change, or dynamic model router is added.

Select direct Astra execution when a difficult cohesive task would otherwise cause
more handoffs and root rework. Select Luna for clear bounded execution, Sol for more
independent implementation judgment. Worker and solver are alternatives; do not pay
for a failed Luna attempt merely to qualify for stronger execution. Preserve the
three-agent cap, flat topology, ownership, approvals, and meaningful verification.

Public model/effort comparisons informed the candidate policy, not a measured win for
this exact setup. Role pins are intentional: a custom agent file can override spawn
requests. The installer validates the selected pairs against a dated documented
matrix; the optional local catalog check and actual runtime evidence are distinct.

## Evidence and references

- [Codex subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents):
  bounded contracts, model/effort selection, and configuration precedence.
- [Astra skill guidance](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra):
  focused guidance and on-demand references instead of an elaborate mandatory pipeline.
- [Reasoning](https://developers.openai.com/api/docs/guides/reasoning) and
  [latency](https://developers.openai.com/api/docs/guides/latency-optimization):
  effort is a tradeoff; reduce unnecessary interactions and parallelize independent work.
- [Prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching):
  reusable input processing is not a free new response or proof a request was useful.
- [Official Sol](https://developers.openai.com/api/docs/models/gpt-5.6-sol),
  [Luna](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
  [Terra](https://developers.openai.com/api/docs/models/gpt-5.6-terra), and
  [Astra](https://developers.openai.com/api/docs/models/gpt-6-astra): documented effort support.
- [Artificial Analysis: Sol Medium/Luna High](https://artificialanalysis.ai/models/comparisons/gpt-5-6-luna-high-vs-gpt-5-6-sol-medium)
  and [Astra Low/Sol Medium](https://artificialanalysis.ai/models/comparisons/gpt-6-astra-low-vs-gpt-5-6-sol-medium):
  public capability, output, latency, and cost comparisons. Index scores are not
  percentages of intelligence. Calculated decode time excludes first-token latency
  and overhead; it is not a completed Codex coding task. API benchmark cost is not
  subscription consumption. Data may change after this decision.

The implementation audit found reviewer no-update polling, repeated unchanged test
runs, duplicated invocation diagnosis, and late real-config compatibility testing.
Those support the coordination fixes. The same audit also found valuable independent
review and real correctness repairs: do not remove verification to make a run faster.
The private session/report stays outside the repository.

## Coordination and context

Review a ready change, return findings, and resume for a ready delta rather than
polling a writer. Assign routine checks one owner and share command, result,
environment, and actual working-tree state. HEAD alone is not a dirty-tree snapshot.
Reuse valid execution evidence while reviewing code independently. Rerun affected
checks after relevant changes, failures, or concerns; retain deliberate independent
final verification for consequential work.

Probe critical parser/runtime/configuration assumptions early and read-only against
the real environment when available. Representative fixtures do not prove local
compatibility. Keep private inputs local and never apply unfinished changes as a probe.

Keep root context focused on decisions and evidence, not another copy of the worker's
investigation. The main skill and Semble role now link installed references; load only
relevant sections. Do not force compaction, fixed token caps, model switches, or cache
resets to chase a benchmark. Do not weaken apply protections for insignificant speed.

## Read-only reports

Use the existing mise task with local arguments:

```sh
mise run orchestrator:usage --root ROOT_ID
mise run orchestrator:usage --root ROOT_ID --include-guardian
mise run orchestrator:usage --root ROOT_ID --since START_ISO8601 --until END_ISO8601 --format json
```

Replace placeholders locally. Both timestamps require Z or a UTC offset. Select from
recorded task events: start inclusive, end exclusive. Whole response records are
counted by recorded timestamps, not prorated across inference boundaries. The caller
must verify that the interval actually covers the intended task.

Full recorded thread/session spans include overlap and inactivity; never sum them
or call them compute time. The reporter does not infer inference, queue, tool waits,
idle time, or repairs from missing evidence. `--date` limits discovered files, not
event timestamps, and can omit threads on other days. Scoped reports require an
explicit root, not `--latest` or `--date`. Legacy cumulative-only usage and missing
record timestamps cannot support scoped allocation; malformed JSONL is rejected.
Wait for a stable log rather than accepting a silently truncated report.

Reports separate included, excluded automatic-review, and all discovered usage.
Reasoning is included in output, not added again. Model/effort may be mixed or unknown.
`response_metrics` supplies per-thread/model input sample count, mean, minimum, and
maximum input size. These are repeated request input sizes, not unique context.
Requested service tiers come only from recorded turn context; response-record tiers
come only from an explicit usage-record field. Missing fields remain unknown. A
requested tier is not proof of a served tier, and neither field is fabricated from
current config. Unknown or newer log formats need local compatibility verification.

### Standard-rate comparison, not billing

A dated rate card from [official Codex pricing](https://learn.chatgpt.com/docs/pricing)
is embedded for a consistent comparison. Rates checked 2026-09-20, credits per one
million uncached input / cached input / output tokens:

| Model | Uncached | Cached | Output |
| --- | ---: | ---: | ---: |
| Astra | 250 | 25 | 1250 |
| Sol | 100 | 10 | 500 |
| Terra | 50 | 5 | 300 |
| Luna | 5 | 0.5 | 30 |

The formula is `((input - cached) * uncached_rate + cached * cached_rate + output * output_rate) / 1e6`.
Output already includes reasoning. The result is a **Standard-rate credit equivalent**
for comparison irrespective of observed service tier, not a bill, actual allowance
charge, or a current live quote. Fast multipliers, promotions, tools, and long-context
adjustments are not applied. Refresh the dated card deliberately when using new rates.

Each estimate needs a known model and explicit valid uncached/cached/output accounting.
Missing cached usage is not assumed zero. Unknown models or incomplete records have
no full estimate; known priced subtotals and unpriced counts remain visible. Missing
or legacy thread usage also prevents a complete total. Excluded approvals stay separate.
Use this to locate expensive interactions, not to equate expensive work with wasted work.

Allowance labels use recorded `window_minutes`, not primary/secondary slot names.
Missing/reset-changed snapshots are not a comparable consumption delta. Account-level
percentage movement is not a task bill and may cover a different interval or other work.

Logs, private reports, catalog files, paths, receipts, and backups stay local. Only
synthetic fixtures belong in this public repository. JSON reports are not safe to
publish merely because the summary looks harmless.

## Observe normal tasks after applying

Compare accepted outcomes, real task elapsed time, meaningful repair turns, missed
requirements, response counts, input sizes, and token/weighted categories with recorded
model/effort/tier. Mark timing and service-tier unknowns honestly. Record task outcomes
and repairs from evidence; do not infer them from the number of tool calls. A few
representative tasks are enough for the next decision; no telemetry service or broad
benchmark platform is needed. Passing code tests proves neither improved agent behavior
nor a measured speedup. Local validation and a new Codex session remain required.
