---
version: "1.0.2"
digest: "4b0e5b2d3736"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: orchestrating-elite-agent-qa
description: Use when orchestrating multi-agent feature work (build/review/merge with subagents or workflows) and the quality bar is high — shipping UI, interactive editors, or anything where a single build pass plus a polite review would let real bugs through.
---

# Orchestrating Elite Agent QA

## When to use

- Multi-agent build/review/merge work where the quality bar is high.
- Shipping UI, interactive editors, or any surface where one build pass plus a polite review lets bugs through.
- Gating a merge on more than a build agent's "done".
- A slice needs a browser-driven visual gate, not just a code read.

## When NOT to use

- Single-agent, low-stakes changes — overhead isn't worth it; [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md) alone covers the brief and tiering.
- Pure backend/logic changes with no rendered surface — the design-critic gate has nothing to check.
- You are the executing agent, not the orchestrator running the pipeline.

## Overview

One build pass plus one agreeable review ships bugs. Quality comes from three independent forces stacked on every slice:

1. **Adversarial diversity** — several skeptical reviewers, each a *different lens*, prompted to refute.
2. **An independent visual gate** — an agent that *drives the browser* (not just reads code).
3. **Realistic QA** — a *fresh, simple* case exercised with *real-mouse-like* events, not the dense seed clicked by exact handle.

Gate the merge on all three; each catches a class the others miss.

(The delegation mechanics beneath this pipeline — briefs, model tiering, trust-but-verify — live in [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md); this skill is the UI-quality-gate specialization.)

## The Per-Slice Pipeline (run in order)

1. **Scope ONE slice → branch** off main. Small, independently mergeable.
2. **Design first (complex slices)** — a planning agent reads the *real code* and designs the algorithm + exact file/function seams before any build. Skip for trivial slices.
3. **Build** — one agent implements on the branch. It must NOT commit. **For UI that one agent is a single `designer` lane on opus owning the whole surface (every state, both themes); never split a surface across builders — the seams show.** Reviewers and the critic stay separate: they check, not shape.
4. **Review — N parallel adversarial reviewers**, each a distinct LENS (e.g. correctness · invariants · regression · headline behavior). Prompt them **refute-first**: "try to break it; report ONLY real, high-confidence issues with a concrete fix; empty if clean." Not a rubber stamp.
5. **Fix** — one agent applies the confirmed high/med findings (defer/note the lows).
6. **Design-critic visual gate** — a dedicated agent drives the browser (cache-bust the JS, screenshot in light AND dark, open menus/states) and challenges the render against the elite bar. Its high/med findings GATE the merge.
7. **QA on a FRESH + REALISTIC setup** — verify on a *fresh simple* case (2–3 named items), not only the complex seed, with realistic pointer sequences (pointer-capture, `pointermove` with `buttons:1`, dispatch at the *location*, not the exact `data-*` handle).
8. **Merge** only when build + review + critic + QA all pass. Update the SPEC/docs and plan **in the same PR**. QA issues get FIXED, never shipped.
9. **Interaction slices: get the human's real-mouse confirmation** — synthetic events can't exercise pointer-capture, hover, or thin hit-targets.

## Orchestration Discipline

- **Sequence slices that touch the same core files.** Parallelize only *truly independent* work.
- **A branch is not an isolated working tree.** Parallel agents in the SAME checkout share one working directory: each needs a **worktree**.
- **A green suite from a shared checkout is not evidence, and a red one is not attributable**: other lanes' half-finished work is in it, even for read-only reviewers. Whole-suite claims come from a disposable worktree at trunk HEAD with only that agent's diff; every number names its tree.
- **"Completed" ≠ done.** A workflow can stop cleanly with the build finished but the *review unrun*. Verify the artifact (gate-check + a functional probe) before trusting any "done."
- **Be resilient to flaky infra.** If a workflow's parallel phase dies (overload, stall), don't just retry — take over with **direct background agents** (individual spawns survive when a fan-out panel doesn't) or finish inline. A workflow that produced its build can be *resumed from cache*; the dead review reruns live.
- **Cache is the silent liar.** Cache-bust the JS (fetch-reload + page reload) and confirm the new symbol loaded before believing a browser-QA result.

## Common Mistakes

| Mistake | Reality |
|---|---|
| Trust the "✓ completed" status | Inspect the diff + run a functional probe; the review may have died. |
| Synthetic exact-handle QA (grab the `data-*` el) | Masks real-mouse bugs (thin targets, missing pointer capture). Use location-based events + a human pass. |
| Skip the design-critic "it's just logic" | UI slices have visual bugs (clipping, off-center, contrast) invisible to code review. |
| Reviewers that summarize, not attack | Refute-first + multi-lens, or they rubber-stamp. |
| Parallelize slices on shared files | Sequence them; only independent work runs in parallel. |
| Forget the SPEC/plan | Stale docs rot fast. Update them in the same PR, every slice. |

## Copyable Prompt (hand to an orchestrator agent)

> For each slice: branch off main. (If non-trivial, first run a **design** agent that reads the real code and specifies the algorithm + exact file/function seams.) Run a **build** agent (no commit). Then **3 parallel adversarial reviewers**, each a distinct lens (correctness · invariants/regression · the headline behavior), *refute-first* — only real, high-confidence issues with a concrete fix, empty if clean. A **fix** agent on the confirmed high/med findings. Then a **design-critic** agent that *drives the browser* (cache-bust the JS, screenshot light + dark, exercise the states) and gates the merge. Then **QA it yourself on a fresh, simple setup** with realistic pointer events (not the dense seed, not exact-handle clicks). Merge only when all gates pass; update spec + plan in the same PR; fix QA issues, never ship them. **Sequence slices that share files; verify "done" before trusting it; cache-bust before believing a browser result; for interaction slices, get a human real-mouse confirmation.**

## Verification

1. Build, the N parallel refute-first reviewers, the design-critic pass, and fresh-case QA are each independently confirmed to have run — never inferred from a "completed" status alone.
2. The design-critic's screenshots come from cache-busted JS, in both light and dark.
3. QA ran against a fresh, simple case with realistic pointer events — not only the dense seed clicked by exact handle.
4. For interaction slices, a human gave real-mouse confirmation before merge.

## Cross-references

- **For the two claims a panel most often accepts unchecked:** [guarding-a-regression](../guarding-a-regression/SKILL.md) — a fix's regression test is evidence only once watched going red, and the panel is where that gets asked; and [proving-an-absence](../proving-an-absence/SKILL.md) — "no test covers this", "I could not reproduce it" and any bare count are absence claims, and an uncontrolled probe is how a false one survives review.
- **For a run that outlives one sitting:** [session-heartbeat](../session-heartbeat/SKILL.md) — this skill says which gates a slice must clear, not how a pipeline continues across a usage-limit reset or resumed session; pacing, the checkpoint, and re-firing a gate whose producer was killed live there.

## Sources

- Practitioner-derived from the same #136 skill-unification build [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md) cites — this skill is that run's panel / design-critic / QA gate sequence.

## Deploying This Skill (per writing-skills)

This draft has NOT been pressure-tested. Per `superpowers:writing-skills`, before relying on it broadly: run a baseline scenario without the skill, capture the rationalizations an agent uses to skip the gates, then tighten the wording (especially "verify done" and "don't ship synthetic-only QA") until an agent complies under time pressure.
