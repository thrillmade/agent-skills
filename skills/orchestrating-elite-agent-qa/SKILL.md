---
version: "1.0.0"
digest: "7eebf3cfc4dd"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: https://github.com/thrillmade/agent-skills
name: orchestrating-elite-agent-qa
description: Use when orchestrating multi-agent feature work (build/review/merge with subagents or workflows) and the quality bar is high — shipping UI, interactive editors, or anything where a single build pass plus a polite review would let real bugs through.
---

# Orchestrating Elite Agent QA

## Overview

One build pass plus one agreeable review ships bugs. Quality comes from three independent forces stacked on every slice:

1. **Adversarial diversity** — several skeptical reviewers, each a *different lens*, prompted to refute.
2. **An independent visual gate** — an agent that *drives the browser* (not just reads code).
3. **Realistic QA** — a *fresh, simple* case exercised with *real-mouse-like* events, not the dense seed clicked by exact handle.

Gate the merge on all three. Each catches a class the others miss.

(The general delegation mechanics beneath this pipeline — brief structure, model tiering, trust-but-verify — live in [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md); this skill is the UI-quality-gate specialization.)

## The Per-Slice Pipeline (run in order)

1. **Scope ONE slice → branch** off main. Small, self-contained, independently mergeable.
2. **Design first (complex slices)** — a planning agent reads the *real code* and designs the algorithm + the exact file/function seams before any build. Skip for trivial slices.
3. **Build** — one agent implements on the branch. It must NOT commit.
4. **Review — N parallel adversarial reviewers**, each a distinct LENS (e.g. correctness · invariants · regression · the headline behavior). Prompt them **refute-first**: "try to break it; report ONLY real, high-confidence issues with a concrete fix; empty if clean." Not a rubber stamp.
5. **Fix** — one agent applies the confirmed high/med findings (defer/note the lows).
6. **Design-critic visual gate** — a dedicated agent drives the browser (cache-bust the JS, screenshot in light AND dark, open menus/states) and challenges the render against the elite bar. Its high/med findings GATE the merge.
7. **QA on a FRESH + REALISTIC setup** — verify on a *fresh simple* case (2–3 named items), not only the complex seed, with realistic pointer sequences (pointer-capture, `pointermove` with `buttons:1`, dispatch at the *location*, not the exact `data-*` handle).
8. **Merge** only when build + review + critic + QA all pass. Update the SPEC/docs and the plan **in the same PR**. QA issues get FIXED, never shipped.
9. **Interaction slices: get the human's real-mouse confirmation** — synthetic events can't exercise pointer-capture, hover, or thin hit-targets.

## Orchestration Discipline

- **Sequence slices that touch the same core files.** Parallelize only *truly independent* work — conflicting parallel edits are merge hell.
- **"Completed" ≠ done.** A workflow can stop cleanly at a phase boundary with the build finished but the *review unrun*. Verify the artifact (gate-check + a functional probe) before trusting any "done."
- **Be resilient to flaky infra.** If a workflow's parallel phase dies (API overload, stall), don't just retry it — take it over with **direct background agents** (individual spawns survive when a fan-out panel doesn't) or finish it inline. A workflow that already produced its build can be *resumed from cache*; the dead review reruns live.
- **Cache is the silent liar.** Always cache-bust the JS (fetch-reload + page reload) and confirm the new symbol actually loaded before believing a browser-QA result.

## Common Mistakes

| Mistake | Reality |
|---|---|
| Trust the "✓ completed" status | Inspect the diff + run a functional probe; the review may have died after the build. |
| Synthetic exact-handle QA (grab the `data-*` el) | Masks real-mouse bugs (thin targets, missing pointer capture). Use location-based realistic events + a human pass. |
| Skip the design-critic "it's just logic" | UI slices have visual bugs (clipping, off-center, contrast) invisible to code review. Drive the browser. |
| Reviewers that summarize, not attack | Refute-first + multi-lens, or they rubber-stamp. |
| Parallelize slices on shared files | Sequence them; only independent work runs in parallel. |
| Forget the SPEC/plan | Stale docs rot fast. Update them in the same PR, every slice. |

## Copyable Prompt (hand to an orchestrator agent)

> For each slice: branch off main. (If non-trivial, first run a **design** agent that reads the real code and specifies the algorithm + exact file/function seams.) Run a **build** agent (no commit). Then run **3 parallel adversarial reviewers**, each a distinct lens (correctness · invariants/regression · the headline behavior), prompted *refute-first* — report only real, high-confidence issues with a concrete fix, empty if clean. Run a **fix** agent on the confirmed high/med findings. Then a **design-critic** agent that *drives the browser* (cache-bust the JS, screenshot light + dark, exercise the states) and gates the merge on its findings. Then **QA it yourself on a fresh, simple setup** with realistic pointer events (not the dense seed, not exact-handle clicks). Merge only when all gates pass; update the spec + plan in the same PR; fix QA issues, never ship them. **Sequence slices that share files; verify "done" before trusting it; cache-bust before believing a browser result; for interaction slices, get a human real-mouse confirmation.**

## Cross-references

- **For the two claims a panel most often accepts unchecked:** [guarding-a-regression](../guarding-a-regression/SKILL.md) — a fix's regression test is evidence only once someone has watched it go red, and the panel is where that gets asked; and [proving-an-absence](../proving-an-absence/SKILL.md) — "no test covers this", "I could not reproduce it" and any bare count are absence claims, and an uncontrolled probe is how a false one survives a review.
- **For a run that outlives one sitting:** [session-heartbeat](../session-heartbeat/SKILL.md) — this skill says which gates a slice must clear, but nothing about a pipeline continuing across a usage-limit reset or a resumed session. That is where pacing, the checkpoint, and re-firing a gate whose producer was killed mid-flight live.

## Deploying This Skill (per writing-skills)

This draft has NOT been pressure-tested. Per `superpowers:writing-skills` (TDD for skills), before relying on it broadly: run a baseline scenario without the skill, capture the rationalizations an agent uses to skip the gates, then tighten the wording (especially the "verify done" and "don't ship synthetic-only QA" rules) until an agent complies under time pressure.
