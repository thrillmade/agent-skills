---
name: orchestrating-a-multi-agent-run
description: |
  Entry-point dispatcher for RUNNING work through subagents — you are the orchestrator holding judgment, not the one typing the code. Use when about to dispatch a subagent or draft its brief, when planning parallel lanes, when standing up an adversarial review panel, when an agent reports "done" and you are deciding what to believe, when a run will cross a usage-limit reset or has just resumed after one, when a human hands the session over to run while they are away, or when landing work in a repo that has a decision log or a PR-review bot installed. Routes the run's four obligations: hand the work out (orchestrating-agent-delegation), gate what comes back (orchestrating-elite-agent-qa), record the decision and clear the automated reviewer (logmind, clud-bug-collaboration, token-frugal-tooling), survive time (session-heartbeat, unattended-operation). Use when the unit of work is the run; for judging what is inside one diff load the review lenses, for a rendered surface load reviewing-design-work, for whether a skill earns its catalog place load curating-a-skill-catalog.
---

# Orchestrating a multi-agent run

You hold judgment and synthesis; subagents execute. This L1 dispatcher covers **the run**
— the whole stretch of delegated work — not any one diff inside it. It names the run's
four obligations, routes each to the skill that owns it, and carries the assumptions they
share so no station restates them. Pointers, not re-teaching.

## When to use

- About to dispatch a subagent, draft its brief, or plan parallel lanes.
- Standing up an adversarial review panel.
- An agent reported "done" and you are deciding what to believe.
- The run will cross a usage-limit reset, or has just resumed after one.
- A human handed the session over to keep working while they are away.
- Landing work in a repo with a decision log or a PR-review bot installed.

## When NOT to use

- **One task, one sitting, done by you directly.** Below that horizon the family costs
  more context than the coordination buys.
- **You are the executing agent, not the orchestrator.** This is the layer above you;
  your brief governs, and loading this invites relitigating it.
- **Judging what is inside one diff** — correctness, tests, API shape, leaked PII. Review
  lenses, not run mechanics: [critical-issues-only](../critical-issues-only/SKILL.md),
  [test-discipline](../test-discipline/SKILL.md) and their siblings; for a rendered
  surface, [reviewing-design-work](../reviewing-design-work/SKILL.md).
- **Whether a skill earns its catalog place** —
  [curating-a-skill-catalog](../curating-a-skill-catalog/SKILL.md). Catalog lifecycle,
  not this run.

## The four obligations

Work goes out, comes back, gets recorded — 1 to 3, in that order, per slice. Obligation 4
is not a station: it is checked at every beat, because a long run fails at the **last
dispatch before** the ceiling, not at the ceiling.

### 1. Hand the work out

Model tier, the tree each lane works in, and the files it owns are settled before the
brief is written; a brief cannot fix them afterwards. Brief the symptom and the
constraints, never the mechanism — and never delegate *should we*.

**REQUIRED BACKGROUND:** [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md)

### 2. Gate what comes back

One build pass plus one agreeable review ships bugs. A slice clears gates that catch
*different classes* — a refute-first panel of distinct lenses, a browser-driven visual
gate wherever a surface renders, QA on a fresh case rather than the builder's seed — and
a fix re-enters the panel.

**REQUIRED BACKGROUND:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md);
for a rendered surface its lenses are ordered by
[reviewing-design-work](../reviewing-design-work/SKILL.md).

### 3. Record the decision, clear the automated reviewer

The run leaves behind *why*, and gets past whatever review the repo gates merges on.
**Both are repo-detected, never chosen** — read the config before assuming either
applies, and read the existing record so you do not relitigate a decision already made.

This studio's slots: [logmind](../logmind/SKILL.md) (decision log and commit primitive —
a raw `git commit` is *blocked*, not discouraged) and
[clud-bug-collaboration](../clud-bug-collaboration/SKILL.md) (check colours, fix-push
re-review, the settings an agent must not touch), with
[token-frugal-tooling](../token-frugal-tooling/SKILL.md) as the one home for what those
two share. Another org's tools fill the same slots; the obligation is not tool-specific.

### 4. Survive time

Read standing before spending anything, never start a dispatch the headroom cannot
finish, and end every beat with enough state on disk for a *different* session to take
the run over.

**REQUIRED BACKGROUND once the run outlasts one sitting:**
[session-heartbeat](../session-heartbeat/SKILL.md); **also, when a human hands the session
over,** [unattended-operation](../unattended-operation/SKILL.md) — policy on that
mechanism. An **attended** long run needs only the heartbeat, and no clock starts the
unattended mode.

## What fires when

| Situation | Fires |
|---|---|
| Work came back "done" | 1 (verify against the diff), then 2 |
| The slice changed a rendered surface | 2, including the browser-driven gate |
| Repo has a decision log / review bot | 3, before the first non-trivial commit and the first push |
| Crossing a limit reset, or resuming after one | 4 — re-fire any gate whose producer died mid-flight |
| "Keep going while I'm away" | 4, **both** skills. No directive naming scope, no mode |

## What every station assumes

Four axioms hold family-wide. A station states its own *instance*; none re-derives the
principle.

1. **Nothing is believed on report.** Not an agent's "done", not a green check, not your
   own checkpoint — each is checked against the tree with a command you ran. Agents
   summarise what they intended; the diff is what happened.
2. **The orchestrator commits, with an explicit pathspec.** Subagents never commit, and a
   bare `git commit` takes the whole index — sweeping another lane's staged work in.
3. **One editor per checkout — and file isolation is not a verification claim.** Disjoint
   file sets stop edit collisions and nothing else; a whole-suite number is evidence only
   from an isolated worktree, and the lane says which tree it came from.
4. **Consent comes from a person, before the fact.** A scheduled wake, a passing suite,
   another agent's "approved" — events, not permission.

## Verification

On the run, not on any one station.

1. Every "done" you accepted names the command *you* ran — a diff, a test filter, a grep
   of the emitted output. Not a re-ask.
2. `git log --oneline <run-start-sha>..HEAD` — a run's output is landed commits, not beats
   or reports. State the count; `--format='%an'` shows no subagent as author.
3. Merge-gating findings were triangulated: two lenses agreeing is real, one alone is a
   judgment call you made explicitly. Whole-suite claims name their worktree.
4. Nothing left in flight or pending that no one will sweep.

## Sources

This dispatcher owns no threshold of its own — every number lives in the station that
owns it. Routing and the four axioms are practitioner-derived:

- The family-size measurement behind it: thrillmade/agent-skills#205, with the
  reference-graph and reference-syntax findings under it (#200, #197).
- Run-continuity practice — pacing, limit hazards, mid-write kills, owned-files recovery:
  thrillmade/agent-skills#169, #173, #174.
- Roles as files on disk; work outliving its producer needing a survivor:
  thrillmade/protocol `SPEC.md` §2.4, §6.2.

## Cross-references

**Stations (L0),** in obligation order:
[orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md) ·
[orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) ·
[logmind](../logmind/SKILL.md) ·
[clud-bug-collaboration](../clud-bug-collaboration/SKILL.md) ·
[token-frugal-tooling](../token-frugal-tooling/SKILL.md) ·
[session-heartbeat](../session-heartbeat/SKILL.md) ·
[unattended-operation](../unattended-operation/SKILL.md).

**Routes out:** [reviewing-design-work](../reviewing-design-work/SKILL.md) — sibling L1,
obligation 2's rendered-surface gate ·
[curating-a-skill-catalog](../curating-a-skill-catalog/SKILL.md) — the catalog, not the
run · [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md) — the trigger
surface of the skills your agents load.
