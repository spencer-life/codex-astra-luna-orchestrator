# Delegation contracts

## Route and sequence

| Example assignment | Route | Evidence to hand back |
| --- | --- | --- |
| Trace a request through validation to its database write | explorer | File and symbol map with the mutation boundary |
| Verify a framework option in the installed version | researcher | Primary-source citation and version |
| Reconcile immediate revocation with cached authorization | architect | Decision, invariants, and failure behavior |
| Implement an accepted validation rule | worker | Focused patch and checks for the accepted behavior |
| Repair duplicate writes under retries | engineer | Reproduction, root cause, fix, and verification |
| Correct a clipped mobile header | ui_specialist | Change and rendered desktop and mobile checks |
| Reproduce a reported regression and run its targeted suite | tester | Command, result, and gaps |
| Inspect a completed change for race conditions | reviewer | Independent findings with concrete evidence |

When discovery is needed, pass the explorer's map to the implementer. When an
external compatibility fact determines a design, establish that fact before planning.
For a backend bug visible in a browser, split UI reproduction and backend repair
into separate assignments.

## Assign and coordinate

Give each owner the outcome, acceptance criteria, workspace and paths, write scope,
dependencies, available capabilities, and expected evidence. Supply the relevant
artifacts and context. For UI work, specify inspection or implementation mode,
URL, browser session, viewports, and who owns cleanup.

Group related work by milestone. A release can give a backend owner and a UI owner
separate surfaces while the root tracks shared acceptance criteria. Queue work that
depends on an unfinished result. When a thread name already exists, check its owner
and follow up if the assignment fits. After a failed spawn, use the tool result to
choose the next action. Report unavailable capabilities and continue unblocked work.

The parent coordinates shared files and reviews scope changes. Specialists return
new dependencies or decisions to the parent. When retiring threads is supported,
keep suitable owners available for foreseeable follow-ups on their current work.

## Review and recheck

For an initial independent review, give a fresh Sol 6.1 High reviewer the original
requirements, actual artifacts, surrounding context, and raw evidence. Let the
reviewer inspect those before sharing the author's verdict if it could bias the
review. Keep authoring, execution evidence, and independent judgment distinct.

Have the owner fix confirmed defects. Send the changed artifact and affected
evidence to the existing independent reviewer for a focused recheck. Keep applicable
test results and rerun the affected checks and required release gates. If independent
review is required and unavailable, report the gate as blocked and preserve completed
work. For release verification, bind approval and artifact checks to the packaged
version or digest when the workflow requires it.

## Escalate and hand off

A worker returns an unknown cause or coupled problem to the root for engineer
routing. An engineer returns an unresolved contract, schema, or permission decision
for the root or architect to settle. Give escalations a narrower question, new
evidence, or a materially different approach. If the needed capability remains
unavailable, report it. Verify any session model selection through actual settings.

Return modified paths, the checked snapshot, commands and results, assumptions,
remaining risks, and decisions. Record real spawn and role evidence for delegated
work. For a handoff, include the user's intent, constraints, completed work, artifact
locations, branch and commit, and the next action. Let the receiving agent verify
live state.
