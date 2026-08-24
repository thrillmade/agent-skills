---
version: "1.0.0"
digest: "ceee4cf10ea4"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: https://github.com/thrillmade/agent-skills
name: session-heartbeat
description: |
  Use when a session must keep working across a stretch longer than one uninterrupted sitting — an orchestrator rolling through a multi-slice plan for hours, a run that will cross a usage-limit reset, a session resumed after a limit or a compaction with someone else's work in flight, or the moment before dispatching an agent when you do not know whether the remaining window can finish it. Also use when a long run is accumulating wakeups but no landed commits, when you are polling for a result the harness would have pushed to you, or when a resumed session is re-deriving pipeline state it should have read off a checkpoint. Names the per-beat order, the largest-dispatch threshold rule, the checkpoint's required slots, and the resume-as-survivor protocol. Not for a single task inside one sitting, and not the unattended-operation policy — that is `unattended-operation`, which builds on this.
---

# Session heartbeat

A long autonomous run rarely fails at the limit. It fails at the **last dispatch before** the limit — the one nobody could finish. A heartbeat is a self-paced recurring wake that turns the ceiling from a crash into a scheduled pause: every beat reads standing before spending anything, and ends with enough state on disk for another session to take the run over.

This is the **mechanism**. `unattended-operation` is the policy layered on it for runs a human hands over; it inherits everything here and restates none of it.

## When to use

- An orchestrator is rolling through a multi-slice plan over hours.
- The run will cross a usage-limit reset — or may, and you don't know.
- Resuming after a limit, a crash, or a compaction, with work in flight.
- About to dispatch, without knowing if the window can finish that agent.
- A run is producing wakeups but no landed commits.

## When NOT to use

- One task inside one sitting. A beat costs a full context read; below the horizon where a limit or handoff is plausible it buys nothing.
- Waiting on a single result your harness will notify you about. That is a notification, not a schedule.
- The run is unattended by human handover — load `unattended-operation` too. This skill has no rules about what may not happen while nobody watches.

## Each beat, in this order

1. **Standing first.** Read remaining budget/usage before deciding anything else. Any other order commits you to a dispatch and *then* discovers it cannot land.
2. **Harvest.** Collect what finished since the last beat, and read it. A completion you noticed but did not read is not harvested.
3. **Verify the ground.** The commit the run stands on; which branches and worktrees are occupied, by whom. The checkpoint says what you expected; the tree says what happened.
4. **Dispatch at most what the headroom can finish** (below).
5. **Checkpoint** (below) — after dispatch, so it records what is in flight.
6. **Re-arm, last, always.** A beat that ends without scheduling the next one ends the run — silently, with a green tree and no error anywhere. Re-arm even on the beat that decides to pause: a pause is a longer wake, not the absence of one.

## Pacing: derive the interval from the work

The interval is set by **how often new information actually arrives** — the completion time of the shortest thing you await. A beat that wakes to an unchanged world pays a full context read for zero information. Two costs bound it:

- **Below the work's cadence is pure waste.** If dispatches take ~15 minutes, a 3-minute beat wakes five times to learn nothing.
- **Past the cache TTL, every beat re-writes the prefix.** Anthropic's prompt cache defaults to a 5-minute TTL (1 hour available at 2× the write price), is refreshed free on use, and is measured from the *start* of the request that reads it. Any cadence beyond your configured TTL pays a cache write per beat. That can be the right trade — choose it, don't discover it.

**Establish once, at entry, whether your harness pushes completion notifications into the session.** If it does, the beat is a safety net and should be long — polling for what will be pushed to you is the commonest way a heartbeat burns a night. If it does not, the beat is your only harvest and must be no longer than your shortest dispatch.

*(One instantiation: agent-skills#173 reports ~20-minute beats — one operator's number for one shape of work, not a default.)*

## The threshold is your largest dispatch, not a round number

Stopping at "90% used" only works if nothing you would start costs more than the remaining 10%. Derive it instead:

> **threshold = the ceiling, minus the cost of the largest dispatch you would still start.**

That makes it enforceable per dispatch: **if this agent cannot finish inside the remaining headroom, do not start it** — shrink the slice or park it. The orchestrator-side complement to a review killed mid-flight: stop *starting* work you cannot finish.

At the threshold:

- **Stop dispatching. Do not kill what is running.** An agent told to stop may still be writing; resetting its files races those writes and leaves a tree neither party owns. Confirm it stopped, *then* reclaim by its owned-files list.
- **Checkpoint.**
- **Schedule the wake for the reset, not a short retry.** A retry beat spends a full context read to learn the limit is still there.

## The checkpoint

Write it to a durable file the project already reads — the plan doc. Not session memory, not a scratch file, never only the conversation. Required slots:

- **The sha the run stands on.** The sha, not a branch name; a name resolves to whatever moved under it.
- **In flight** — each agent: role, model, branch or worktree, files owned.
- **Occupancy** — which trees are not free to merge into.
- **Next dispatch, already decided.** The resumer executes it; it does not re-derive it.
- **Blocked, on what** · **Parked, awaiting whom.**
- **Next wake time, and why** — normal cadence or limit reset. This is what lets a fresh session tell *paused* from *died*.

## Resume: you are the survivor

A check MUST NOT be left pending, and a producer that dies cannot honour that — the rule needs a survivor that does not depend on the producer being alive (protocol SPEC §6.2). The resumed session is that survivor.

1. Read the checkpoint before anything else.
2. **Verify it against the tree; do not trust it.** It was written before the last writes landed.
3. Per in-flight agent: confirm it stopped, then reclaim its files — or let it finish.
4. Re-fire whatever is recorded pending: reviews and gates that died with their producer.
5. Continue from the pre-decided next dispatch.

## Silent failures

Each of these leaves a green tree and reports nothing.

| Failure | How it looks | Fix |
|---|---|---|
| Beat never re-armed | The run just stops; no error | Re-arm last, every beat; checkpoint the next wake so absence is detectable |
| Dispatch that could not finish | A partial diff that reads like work | Per-dispatch headroom check, not a global % |
| Reset raced a dying agent | Files from two owners; tests pass | Confirm stopped before reclaiming |
| Merged into an occupied tree | Another agent's edits ride into your commit (whole-tree staging) | Occupancy slot in the checkpoint; commit with an explicit pathspec |
| Checkpoint written, never read | Resume re-dispatches work already landed | Resume opens by reading it and diffing it against the tree |
| Cadence drift | Beats accumulate notes; nothing lands | Count consecutive beats with no landed commit; three means the beat outpaces the work — lengthen or stop |

## Verification

1. `git log --oneline <run-start-sha>..HEAD` — the run's value is commits, not beats. State the count.
2. Every checkpoint names a sha that `git cat-file -e` resolves.
3. Each beat closed with the next wake already scheduled — check before it ends, not after.
4. No agent's files were reclaimed without evidence it stopped.
5. Nothing left pending that no one will sweep.

## Cross-references

- **REQUIRED BACKGROUND:** `orchestrating-agent-delegation` — brief shape, model tiering, verify-every-"done"-against-the-diff, and the file-isolation rules the occupancy slot records. This skill paces dispatches; that one is how to write and verify one.
- **For unattended runs:** `unattended-operation` — the policy layer (scope, hard stops, what a wake does *not* authorize, the handback digest). Load both when a human hands the session over.
- **For the gates a resumed slice must re-fire:** `orchestrating-elite-agent-qa`.

## Sources

- Cache lifetime/refresh: Anthropic prompt-caching docs — 5-minute default TTL, 1-hour option at 2× write price, refreshed free on use, measured from request start.
- Pending-work survivor rule: thrillmade/protocol `SPEC.md` §6.2 — "A check MUST NOT be left pending… the rule needs a survivor."
- Cadence and threshold practice as reported: thrillmade/agent-skills#173. Mid-write kill hazards, owned-files recovery: #169 (discipline 6). The review lifecycle a resume re-fires: thrillmade/protocol#44, thrillmade/clud-bug#239.
