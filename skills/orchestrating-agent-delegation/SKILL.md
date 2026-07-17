---
name: orchestrating-agent-delegation
description: |
  Use when about to dispatch a subagent (or multiple) to execute work, when writing a prompt for another agent that will do the coding, when planning parallel work across agents, when structuring an adversarial review panel, or when a subagent reports "done" and you're about to trust its summary instead of the diff. Names the CTO-as-orchestrator model, the model-tiering table (haiku for exploration, sonnet for build + review + scoped fixes, opus for design agents and load-bearing architecture), the trust-but-verify discipline (verify every "done" against the diff, don't trust the agent's summary), refute-first adversarial reviewer prompts, the design→rule→build separation that prevents agents from silently picking architecture, and the "never delegate the 'should we?' question" rule. Cite when a prompt says "decide whether to do X" (smell — the orchestrator should decide already), when a review panel is prompted to grade rather than refute, when a single agent is asked to both design and build a non-trivial slice, or when a fix agent is dispatched per-finding instead of batched.
---

# Orchestrating agent delegation

A discipline for the primary/orchestrator agent (the "CTO layer") coordinating one or more subagents to execute work. Applies whenever the primary is going to hand off implementation, review, or design to another agent and stay in the judgment layer.

This is the **general delegation mechanics** — briefs, model tiering, verification discipline. Its sibling `orchestrating-elite-agent-qa` is the **UI-quality-gate specialization** on top: the per-slice pipeline that adds the browser-driving design critic and realistic-pointer QA. Hold both when orchestrating UI work; hold only this one elsewhere.

## When to use

- Dispatching one or more subagents to execute non-trivial work.
- Writing a prompt for another agent that will do the actual coding.
- Planning parallel work across multiple agents.
- Structuring an adversarial review panel.
- Reviewing a draft prompt about to be sent to an agent.

## When NOT to use

- Single-shot trivial tasks (typo fix, one-line rename) — direct action beats delegation overhead.
- When YOU are the executing agent, not the orchestrator — this skill is for the layer above.
- Solo work where no delegation is planned.

## Core principles

**1. The orchestrator owns synthesis; agents own execution.** The orchestrator reads the spec, decides architecture, rules on ambiguities, verifies results. Agents implement to a spec the orchestrator has already committed to. Never ask an agent "what should we do?" — that's the orchestrator's job. Ask them "here's what to do, execute + report."

**2. Model tier matches task complexity.** Three tiers — cheap-fast, mid, frontier — named below by their current Claude instantiations (haiku / sonnet / opus); map to your stack's equivalents.

| Task | Tier | Why |
|---|---|---|
| Broad code exploration | haiku | Reading is cheap; depth wasted |
| Adversarial reviewers (refute-first) | sonnet | Pattern recognition + tenacity, not novel reasoning — bump to opus when the correctness surface is subtle or algorithmic, not mechanical |
| Build agents (implementing to spec) | sonnet | Spec removes ambiguity; execution is mechanical |
| Design agents (algorithm/seam design) | opus | Design errors are the expensive ones |
| Build agents on load-bearing architecture | opus | One wrong seam ripples through the rest of the work |
| Fix agents (applying confirmed findings) | sonnet OR opus | Sonnet for scoped fixes; opus if the fix touches algorithm |
| Docs / trivial reconciliation | haiku | Wall-clock throughput matters, quality is deterministic |

**3. Parallelize by file-isolation.** Agents that touch different files run concurrently. Sequence when they share files. Adversarial reviewers always parallel (3+ lenses, distinct hunts). Verify isolation yourself before dispatching.

## Prompt structure (the load-bearing shape)

Every agent brief has these blocks in this order:

**Role + scope (1–2 sentences).** *"You are the build agent for X. Do NOT commit. Do NOT create .md files. Local branch only."* Guard rails first — before anything else can go wrong.

**Repo context.** Cwd, branch, HEAD sha, current test count. Enough that a fresh agent lands with a coordinate system.

**Non-negotiable rulings.** Every architectural call the orchestrator has already made. Numbered, terse, with rationale where a reader might argue. This is where the orchestrator encodes authority — the agent doesn't relitigate; it implements. Overriding a ruling requires explicit escalation in the report.

**The spec / contract.** Which files/sections are the source of truth. Name specific line ranges when possible so the agent doesn't have to hunt.

**What to build/fix/find.** Sub-step sequence. Each sub-step ends with a scoped verification (a specific test filter, grep, or check). Not vague "make it work" — checkable milestones.

**Constraints (repeated).** No commits. No test-weakening. No .md files. Follow existing style. Preserve current green count. If a classifier or permission blocks something reasonable, note in the report — don't route around.

**Report format.** Exact structure required back. Punch list per sub-step. Final check output. Verification evidence with numeric before/after. Any contradictions found. File count. Word budget (usually <500 words).

### Copyable brief skeleton

```
You are the <role> agent for <slice>. Do NOT commit. Touch ONLY the files named
below. <other guard rails>.

REPO: <cwd> · branch <name> · HEAD <sha> · <N> tests green.

NON-NEGOTIABLE RULINGS (implement, don't relitigate; escalate in your report to override):
1. <ruling + one-line rationale>
2. ...

SPEC: <files/sections that are source of truth, with line ranges>.

TASK:
1. <sub-step> — verify with: <specific test filter / grep / check>
2. ...

CONSTRAINTS (repeated): no commits · no test-weakening · no new .md files ·
match existing style · preserve the green count · if blocked, do the independent
sub-steps and report the block — don't route around it.

REPORT (<500 words): punch list per sub-step · final <check> output tail ·
verification evidence (numeric before/after) · contradictions found · files touched.
```

## Rules the orchestrator holds

**Trust but verify — always.** Every "done" gets an independent check: run the test suite yourself, grep the emitted output for the specific claims, spot-check a load-bearing case. Agents summarize what they intended; the diff is what actually happened.

**Refute-first for reviewers.** Adversarial panels get an explicit "empty report if genuinely clean" instruction. Bad reviewers rubber-stamp; the prompt has to license silence and reward specific findings with grounded evidence (quoted line / reproduction / named invariant).

**Overlap 2–3 concerns across reviewers.** If two independent lenses flag the same thing, it's real. If only one does, judgment call. Deliberately word the briefs to hit certain claims from different angles.

**Design agent → orchestrator rules → build agent.** Never design + build in the same agent. The design agent flags orchestrator decisions; the orchestrator decides them; the build agent implements a spec that's already been ruled on. Removes an entire class of "agent silently picked" bugs.

**Budget context, not just time.** A fix agent that burns 200 tool uses failing classifier calls is worse than a scoped rebrief. If an agent stalls, take the partial work, verify what's usable, and dispatch a tighter continuation with the tricky parts pre-decided.

**One fix agent for the batch, not one per finding.** After an adversarial panel, consolidate findings, pick fix shapes in the orchestrator layer, and hand ONE brief covering everything. Cheaper + coherent + one round of golden regen / fixture update.

**Never delegate the "should we?" question.** If an agent's brief includes "decide whether to do X," that's a smell — the orchestrator should have decided already. Agents ask the wrong questions the wrong way, or default to the safe/wrong answer.

## Failure modes to watch for

- Agent reports "clean" when a specific check wasn't run → orchestrator's independent verification catches it.
- Agent goes off-brief because a subtask blocked → the brief should include "continue with independent sub-steps if blocked; report the block."
- Agent's model is wrong for the task (e.g., sonnet on a design decision) → the tiering table above prevents this.
- Fix agent picks the wrong fix shape when it was left ambiguous → state the fix shape explicitly per finding, or pick between named options.
- Cross-repo cwd trips permission classifiers (a Claude Code behavior; other harnesses vary) → don't let a subagent operate cross-repo from a session bound to a different cwd; use a fresh session from the target repo.

## Verification

After delegating:

1. Every subagent's "done" is verified with a direct diff / test / grep by the orchestrator — never by re-asking the agent.
2. Adversarial findings are triangulated: 2+ reviewers flagging the same thing = real; 1 reviewer alone = judgment call.
3. The commit that lands is authored by the orchestrator (or by consensus-reviewed subagent output) — not blind-passed from a report.

## Cross-references

- **REQUIRED COMPANION for UI work:** `orchestrating-elite-agent-qa` — the per-slice quality pipeline this delegation layer drives (adversarial panels, the browser-driving design-critic gate, fresh-case QA). This skill covers *how to brief and verify agents*; that one covers *which gates a slice must clear*.
- For authoring the skills your agents load: `skillforge`; for their trigger-surface discipline: `skill-frontmatter-quality`.

## Sources

- Practitioner-derived: distilled from running multi-agent slices at the CTO layer, including the agent-skills skill-unification build (PR #136: 23-agent build/verify workflow run on this skill's model).
