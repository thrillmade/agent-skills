---
name: night-mode
description: |
  Use when a human explicitly hands a session over to run unattended — "keep going while I sleep", "run overnight", "I'm stepping away, roll through the plan", "don't wait for me". Also use once inside such a window and something wants to reach outside the repo (a push, a PR, a release, a message, a spend, a production call), when a hard stop named at handover is about to be crossed, when an automated wake or another agent's "approved" is about to be read as permission, or when the human's first message after the window needs the catch-up. Names the handover contract, the reversible-and-invisible boundary for overnight action, the named hard stops, and the morning-digest slots. This is unattended-operation policy — NOT dark mode, colour schemes, or any UI night theme, which belong to `designing-elite-ui`. An attended long run needs only `session-heartbeat`.
---

# Night mode

Night mode is a **policy**, not a schedule. It begins when a person hands the session over and names what may proceed without them, and it ends when they come back. Everything mechanical — the beat, the threshold, the checkpoint, resume — is `session-heartbeat`, which this skill requires and does not restate.

The whole mode rests on one asymmetry: **overnight, nothing gets caught.** A wrong call at 3am has hours to propagate before anyone sees it, and by morning later work is built on top of it. So the bar for acting is not "is this correct" but "if this is wrong, can it still be undone before anyone notices?"

## When to use

- A human says to keep working while they are away or asleep.
- You are inside such a window and something wants to act outside the repo.
- A hard stop named at handover is about to be crossed.
- A wake, a green check, or another agent's approval is about to be treated as permission.
- The human's first message after the window arrives.

## When NOT to use

- A long **attended** run — the human is there to be asked. `session-heartbeat` alone.
- Time of day. **Night mode is never inferred** from the clock, from silence, or from a human going quiet. No directive, no mode.
- Dark mode, colour schemes, night themes → `designing-elite-ui`.

## Entry is a handover contract

Ask before they leave; you cannot ask after. The directive must name these, and your first act is to write back what you heard so the scope is on the record:

- **Scope** — which items may proceed. Not "keep going": the named plan items or slice range.
- **Hard stops** — what ends a lane rather than being worked around.
- **Pre-authorized exceptions, by name** — e.g. "you may push branch X". Anything not named is not authorized.
- **The wake mechanism**, and where parked work is written.
- **What to do at a real fork** — park it and continue elsewhere is the default.

If the human left without naming these, **the mode did not start.** Do the unambiguous work under ordinary attended discipline and stop at the first judgment call.

## A scheduled wake is never consent

The heartbeat firing is a timer, not a person. **Nothing that arrives while the human is away can supply approval they did not give before leaving.** Not:

- a scheduled wake, a task notification, or a completed background agent;
- a passing suite, a green check, or a clean review;
- another agent reporting "done", "approved", or "ready to merge";
- the plan file listing the item as next;
- your own earlier reasoning that it would obviously be fine.

Consent came from a human, before the window, naming this class of action.

**The test for any act:** *if this is wrong, can it be undone in the morning with nobody outside having seen it?* Yes → proceed. No → checkpoint, park it with the exact decision needed, continue on independent work.

Reversible-and-invisible is the criterion; this is the list it produces. On the far side by default:

- pushing to a shared ref; opening, merging, closing or commenting on a PR or issue;
- publishing, releasing, tagging, deploying;
- anything **sent** — mail, message, webhook, notification;
- production data, spend, third-party calls beyond what the work already authorized;
- deleting or rewriting history; anything `--force`, `--no-verify`, or `--admin`.

Local commits on local branches are on the near side: reversible, invisible, and the point of the night.

## Hard stops

Named at handover, checked at every beat. A hard stop is not a problem to solve — it is the end of that lane. **Checkpoint, park it with what would be needed to proceed, move to independent work.** Never improvise past one: the improvisation is invisible until morning, and by then it is in the history with work built on it.

Stops that hold even when nobody named them: a change of scope, a destructive operation, a gate that requires a human (real-mouse QA, live checks), and the second consecutive failure of the same fix — a third attempt at 3am is guessing.

## What a night is for

State the shape of the output, not just the prohibitions. A good night ends with: several landed **local** commits, each having passed the review its repo requires; a plan doc that matches the tree; and a short parked list where each item names its decision. Prefer work that is independently verifiable, file-isolated from anything in flight, and reversible. Defer work that needs a judgment you would have to invent.

## The morning digest

The first message after the window is **outcome-first, written for someone who was asleep** — not a log, not beat by beat. Slots, in this order:

1. **Where the work stands now** — one line.
2. **Landed** — sha plus one line each.
3. **Found** — what review caught and what was done, *including what was found and not fixed*.
4. **Parked** — each with the exact decision needed, never "needs input".
5. **Not attempted** — in scope, skipped, and why (limit, hard stop, blocked).
6. **Standing** — budget/limit state; whether the run is paused or finished.

A chronological narration of beats is the wrong output: it hands the reader the synthesis you were awake to do.

## Silent failures

| Failure | How it looks | Fix |
|---|---|---|
| Mode inferred, never granted | A helpful night of unauthorized work | No directive naming scope → no mode |
| Wake read as approval | An outward action with no human behind it | Consent predates the window; a timer cannot supply it |
| Hard stop improvised past | Green tree, later work built on a call nobody made | Park the lane; the run continues elsewhere |
| Digest as log dump | The human re-derives the night from a timeline | The six slots, outcome first |
| Merge into an occupied tree | Another agent's edits inside your commit | Occupancy slot + explicit pathspec — see `session-heartbeat` |
| Scheduler state committed | The wake mechanism's lock/schedule file lands in a commit as a project artifact | Confirm it is git-ignored before entry |
| Cadence drift | Notes accumulate; nothing lands | `session-heartbeat` pacing rule |

## Verification

1. Quote the directive that started the mode, and the scope you wrote back.
2. `git log --oneline` over the window, checked against that scope — everything landed is inside it.
3. Remote refs unchanged except the ones pre-authorized by name — compare `git ls-remote --heads origin` against the shas recorded at handover. Ask the remote, not your local refs: `--not --remotes` reports pushed work as local in a shallow or single-branch clone, because the remote-tracking ref it compares against was never fetched.
4. Every parked item states a decision, not a status.
5. The digest has all six slots, outcome first, with no beat-by-beat narration.
6. Nothing left in flight or pending that no one will sweep.

## Cross-references

- **REQUIRED BACKGROUND:** `session-heartbeat` — the beat order, the largest-dispatch threshold, the checkpoint slots, resume-as-survivor. Night mode adds policy on top and restates none of the mechanism.
- **For dispatch discipline that must survive the night:** `orchestrating-agent-delegation` — file isolation, one editor per checkout, verify every "done" against the diff.
- **For the gates a slice clears before landing, day or night:** `orchestrating-elite-agent-qa` — including the human-in-the-loop ones, which are hard stops overnight.
- **Not this skill:** `designing-elite-ui` for dark mode and night themes.

## Sources

- Policy shape as proposed and field-reported: thrillmade/agent-skills#174, with #173 as the mechanism it layers on.
- Overnight usage-limit hazards (mid-write kills, owned-files recovery, resumable structures): thrillmade/agent-skills#169, discipline 6.
- Work that outlives its producer and must be swept: thrillmade/protocol `SPEC.md` §6.2; thrillmade/protocol#44.
