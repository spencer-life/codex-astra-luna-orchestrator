# Delegation and evidence contracts

## Assignment

Supply only the context needed to act correctly:

- Outcome and observable acceptance criteria, including important non-goals.
- Exact repository/worktree, relevant files/symbols and authoritative references.
- Exclusive writable paths, or no-edit scope; UI inspection/implementation mode.
- Constraints, dependent work, available tools and permissions; who owns shared files.
- Expected deliverables and the specific checks that would establish completion.

Use outcome-oriented assignments rather than prescribing private reasoning steps.
Do not send the entire parent transcript. The model should inspect raw artifacts
and explain decisions with concise evidence, not disclose private chain-of-thought.

## Ownership and sequencing

Before parallel writes, separate ownership by files or truly independent worktrees.
Do not assign one shared config, lockfile, schema or component to multiple writers.
If scope expands, obtain a parent decision and revise ownership before editing.
A waiting dependency is not useful parallelism: start the dependent work only when
its contract is stable. Keep one owner for routine checks and share the evidence.
Workers do not recursively spawn; the parent controls the total thread budget.

Do not poll repeatedly while a writer is making progress. Use completion signals
when available. Reuse a context for follow-up on the same coherent task; retire it
at a meaningful boundary. Only the parent integrates and decides acceptance.

## Result

Return a compact report with:

- Outcome and files/artifacts actually changed, with commit/worktree context.
- Commands, results and environment assumptions; links or paths to raw evidence.
- Requirements satisfied, gaps, material risks and decisions needed.

No self-assigned approval labels. No claims that tests, model calls, visual reviews
or external actions occurred without tool evidence. Distinguish static inspection,
execution checks and independent review.

## Independent review

Use a fresh Astra XHigh reviewer. Give it the original requirements, real diff,
relevant code, test evidence and permitted scope. Initially withhold the author's
proposed verdict, suspected bug and solution story when they could bias the review.
A developer who authored the implementation cannot independently review it.
Test execution by the tester and visual observation by Terra provide evidence;
they do not replace a requested Astra independent review.

Resolve findings against the artifacts, not reviewer prestige. Have the owner fix
confirmed defects, rerun affected checks, and obtain a fresh or appropriately
continued independent check on the changed scope. Do not silently downgrade a
required review because the model is unavailable. Report that gate as blocked.

## Escalation and persistence

Escalate to Sol engineering when a bounded worker discovers coupled reasoning,
unclear failure behavior, or a failed approach that needs a new hypothesis.
Escalate a technical decision to the architect before expanding scope. Use Astra
for independent assessment of consequential decisions, not routine lookup work.

Stop repeating an operation when the blocker is unchanged or the next action would
exceed authorization. Gather a discriminating observation, choose a materially
different evidence-backed approach, or report the missing permission/capability.
Do not keep adding agents or increasing effort to compensate for absent tools.
If the entire problem outgrows a Terra root, propose a new Sol-led session with a
compact checkpoint; do not claim a model switch occurred merely by instructing it.

## Checkpoint for another session

Preserve user intent, accepted decisions, constraints, unresolved questions,
completed work, evidence locations, current branch/commit and the next action.
Leave inspectable implementation details and live state for the receiving Codex
to verify. Include unavailable checks and do not turn plans into completed work.
