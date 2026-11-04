# Delegation contracts and trigger examples

## Select one owner for the next output

Use the routing gate in SKILL.md before substantive work. Do not spawn all roles to
satisfy a quota. A missing required tool/model is a blocker to report, not permission
to use Astra or silently choose an unrelated agent. Roles are differentiated by
output and source of uncertainty, not by model name.

| Example assignment | Route | Do not substitute |
| --- | --- | --- |
| Trace who validates a request and where the database write happens | explorer | researcher; this is internal code evidence |
| Verify whether the installed framework supports this configuration option | researcher | explorer; this is external/version evidence |
| Decide how immediate token revocation can coexist with cached validation | architect | engineer coding an undecided policy |
| Implement the accepted validation rule in the specified handler | worker | engineer merely because several lines change |
| Diagnose duplicate writes under retries and repair the coupled state transition | engineer | worker repeatedly guessing a one-line fix |
| Correct a clipped mobile header and verify rendered desktop/mobile behavior | ui_specialist, implementation | engineer/worker as the visual owner |
| Reproduce this reported regression and run the targeted suite, without production edits | tester | reviewer treating commands as design signoff |
| Independently inspect the completed change for race conditions and missing tests | reviewer | architect inventing a new plan or author reviewing itself |

If discovery is needed first, ask explorer for a map, then give that evidence to the
implementing role; do not send both agents to independently rediscover the same map.
If external compatibility determines a plan, ask researcher for that fact before the
architect chooses. If a bug is in backend state but appears in a browser, give UI
reproduction to ui_specialist and backend repair to engineer with disjoint ownership.

## Coordinate by milestone

Group related work into a coherent milestone and start with one owner, adding a
second independent lane when it can make progress without duplicating discovery or
editing the same files. Use the four-thread limit for genuinely separate deliverables
or checks. It is a ceiling, not a target. For a release, for example, a backend owner
and a UI owner can work in parallel on separate surfaces while the root tracks
acceptance criteria and dependencies.

Before starting another thread, check whether the work already has an active owner or
finished evidence that still applies. If the same deliverable needs more work, follow
up with its existing owner. Use a fresh reviewer for the initial review of material
work, then reuse that reviewer for focused rechecks while independence and scope remain
valid. Keep valid test results and rerun only coverage affected by a change, along
with required release checks.

Keep working on unblocked root-owned tasks while agents run. Wait when another result
is required to continue or integrate. Otherwise, act on incoming updates or check
again when there is reason to expect progress. Repeated waits that return no new
information add coordination without advancing the work. If a thread name is already
in use, check that existing owner and follow up if the deliverable matches. Do not
retry an unchanged spawn. If capacity is full and distinct work has no owner, queue it
until a slot opens. Retire agents when ownership ends if the runtime supports closing
their threads, and report an actual availability blocker when no route remains.

## Assignment

Give outcome/acceptance criteria, non-goals, exact worktree and relevant paths,
minimal raw context, exclusive writable paths or no-edit mode, dependencies,
available tools/permissions, and expected evidence. For UI specify inspection or
implementation mode and browser URL/session/viewports. Never imply missing tools
exist. Do not pass the entire transcript or prescribe private reasoning steps.

For release-like work, state the user-critical acceptance criteria in the initial
assignment and test plan. Check behavior against those criteria before packaging.
After packaging, record the actual artifact's version or digest for downstream
review, then run any required exact-artifact, privacy, deployment or approval gates.
If edits change the candidate, rerun affected behavioral checks and gates against the
new artifact.

The parent owns shared files, coordination and acceptance. Workers do not recursively
spawn. Resolve expanded scope with the parent before editing, not after a collision.
Serialize dependent work and keep parallel assignments on distinct paths.

## Result and routing accountability

Return outcome, actual modified paths/artifacts, checked snapshot, commands/results,
environment assumptions, unresolved risks and decisions. Distinguish static reads,
execution, visual inspection and independent review. No self-assigned approval.
The parent briefly records the actual role used, assignment and result. For skipped
substantive delegation, name the concrete exception and unverified coverage. A model
saying it delegated is not evidence: retain actual spawn/role metadata locally.

## Independent Sol review

Use a fresh Sol 6.1 High reviewer. Give original requirements, real artifacts/diff,
relevant surrounding code and raw evidence, initially without the author's verdict
when that could bias the result. The architect/engineer instance that authored work
cannot approve it independently. Same underlying model, separate context.

A tester supplies test evidence and Terra supplies visual observations; neither
replaces requested independent review. Resolve findings against artifacts, have the
owner repair confirmed defects and rerun affected checks. Continue focused follow-up
in the independent reviewer thread rather than paying for redundant full reviews.
No automatic Max/XHigh, no Astra, no downgrade of a required gate into a self-check.
If Sol review is unavailable, report the gate blocked and keep completed safe work.

## Escalation

Worker returns to parent/engineer when the solution is no longer known, a speculative
approach fails or coupled reasoning appears. Engineer returns new contract/schema/
permission decisions to parent/architect before expanding scope. The parent may ask
a reviewer to challenge a consequential existing plan; that is distinct from writing
it. Escalation is a different bounded question, not repetition of the same task at
higher effort. Any model/effort change requires real supported configuration evidence.

Stop retries with an unchanged blocker. Gather a discriminating observation, take
an authorized materially different approach, or report the exact missing capability.
If coordination exceeds the Terra root's scope, propose a new Sol-led session with a
compact checkpoint rather than claiming an in-place switch. Never propose Astra.

## Handoff

Preserve intent, decisions, constraints, unresolved questions, completed work,
artifact/evidence locations, branch/commit and next action. Let receiving Codex
inspect live state and implementation details. Plans are not completed work.
