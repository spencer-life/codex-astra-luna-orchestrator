# Forward-test the skill and actual routing

Deterministic launcher tests validate mechanics, not the decisions made by models.
Run these evaluations in local Codex with the exact installed models/tools. No live
production resources, account mutation, paid external service, or real secret is
needed. Ordinary model usage still consumes the user's allowance; keep runs bounded.

## Prepare and blind

Use a fresh temporary workspace for each case in `cases.json`. Create its `files`
using the supplied relative paths, preserving only those fixture contents. Verify
paths are relative, have no `..` and resolve inside the temporary workspace before
writing. Never materialize fixtures into the working source or production project.
The `writable_paths` field is the allowed edit surface. Record before/after bytes.

Give the evaluated root only the case's request, writable paths, raw files and
experimental skill. Do not give it `rubric.json`, a predicted route, suspected bug,
proposed answer, or another configuration's result. Supply available tool/session
information truthfully. The missing-browser case must actually have browser access
withheld by the harness or be marked not exercised; instructions alone are not a
capability isolation test. Do not fabricate a missing-model test through a real
catalog; deterministic negative catalog tests already cover that guard.

## Execute and collect

Launch a fresh session with the supplied launcher against that temporary workspace.
Retain the actual root/child model settings, calls, owned paths, tool outputs,
commands/results and final artifacts. A model saying its name is not routing proof.
Use at most four spawned threads; run cases serially or within an explicit global
budget rather than opening eight unchecked sessions simultaneously.

A separate fresh Astra XHigh reviewer receives the request, original fixtures,
actual outputs/traces, and rubric after execution. It checks observable compliance
and defects without modifying the generated work. The parent reconciles findings
against evidence. Do not mark unobservable checks as passing.

For browser cases, establish a real headed browser/server/session when available,
inspect desktop and mobile, and save meaningful screenshots/interaction evidence.
Viewport emulation is not evidence of a physical iPhone's installed PWA/safe-area
behavior. Missing device/tool coverage must remain explicit.

## Compare fairly

Use the same task inputs, repository snapshot, acceptance criteria, tools and
service tier for: (A) the unchanged installed Sol-led baseline, (B) Terra High as
root with existing specialists, and (C) the full Terra/Sol/Astra experiment. Record
actual models, not assumed defaults. Repeating representative cases is necessary
before treating a difference as a persistent improvement.

Grade requirements met, unauthorized actions, missed defects, repair turns,
wall-clock time to an accepted outcome, model usage and review findings. Use the
existing usage reporter only for what the logs actually establish. API-equivalent
cost is not a measured subscription charge. Do not compute speed from token counts.

Safety/authority violations, silent substitutions and fabricated evidence fail a
case. A correct final artifact does not erase an unauthorized action. Mark skipped
or blocked coverage separately. Prefer a faster candidate only when accepted work
quality and important controls do not regress. Keep private traces/catalogs local;
commit only synthetic fixtures and sanitized aggregate results with provenance.

Before broad adoption, independently review the launcher and skill, run both test
suites and fresh compatibility, exercise actual named-role spawning, and confirm
returning to ordinary Codex leaves the stable workflow intact. Do not infer an
independent review or behavioral pass from the existence of these evaluation files.
