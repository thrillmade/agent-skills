---
name: orchestrating-agent-delegation
description: |
  Use when about to dispatch a subagent (or multiple) to execute work, when writing a prompt for another agent that will do the coding, when planning parallel work across agents, when structuring an adversarial review panel, or when a subagent reports "done" and you're about to trust its summary instead of the diff. Names the CTO-as-orchestrator model, the model-tiering table (haiku for exploration, sonnet for build + review + scoped fixes, opus for design agents and load-bearing architecture), the trust-but-verify discipline (verify every "done" against the diff, don't trust the agent's summary), refute-first adversarial reviewer prompts, the design→rule→build separation that prevents agents from silently picking architecture, and the "never delegate the 'should we?' question" rule. Cite when a prompt says "decide whether to do X" (smell — the orchestrator should decide already), when a review panel is prompted to grade rather than refute, when a single agent is asked to both design and build a non-trivial slice, or when a fix agent is dispatched per-finding instead of batched.
---

# Orchestrating agent delegation

The **general delegation mechanics** — briefs, model tiering, verification — for the orchestrator agent (the "CTO layer") that stays in the judgment layer while subagents execute.

## When to use

- Dispatching subagents to non-trivial work.
- Writing a prompt for an agent that will do the coding.
- Planning parallel work across agents.
- Structuring an adversarial review panel.
- Reviewing a draft prompt before it is sent.

## When NOT to use

- Single-shot trivial tasks (typo fix, one-line rename) — direct action beats delegation overhead.
- When you are the executing agent, not the orchestrator — this skill is the layer above.
- Solo work where no delegation is planned.

## Core principles

**1. The orchestrator owns synthesis; agents own execution.** The orchestrator reads the spec, decides architecture, rules on ambiguities, verifies results. Agents implement a spec it has already committed to: "here's what to do, execute + report."

**2. Model tier matches task complexity.** Three tiers — cheap-fast, mid, frontier — named below by their current Claude instantiations (haiku / sonnet / opus); map to your stack's equivalents.

| Task | Tier | Why |
|---|---|---|
| Broad code exploration | haiku | Reading is cheap; depth wasted |
| Adversarial reviewers (refute-first) | sonnet | Pattern recognition + tenacity, not novel reasoning — bump to opus when the correctness surface is subtle or algorithmic |
| Build agents (implementing to spec) | sonnet | Spec removes ambiguity; execution is mechanical |
| Design agents (algorithm/seam design) | opus | Design errors are the expensive ones |
| Build agents on load-bearing architecture | opus | One wrong seam ripples through the rest of the work |
| Fix agents (applying confirmed findings) | sonnet OR opus | Sonnet for scoped fixes; opus if the fix touches algorithm |
| Docs / trivial reconciliation | haiku | Throughput matters; quality is deterministic |

**3. Parallelize by file-isolation.** Agents that touch different files run concurrently; sequence when they share files. Adversarial reviewers always parallel (3+ lenses, distinct hunts). Verify the isolation yourself before dispatching.

## Prompt structure

Blocks in this order: **guard rails** first, before anything else goes wrong; **repo context** so a fresh agent lands with a coordinate system; **rulings** numbered and terse, with a rationale where a reader might argue — this is where authority is encoded; **spec** with line ranges so the agent doesn't hunt; **sub-steps** each ending in a scoped, checkable verification, never a vague "make it work"; **constraints** repeated though they opened the brief; **report format** exact, because a shapeless report can't be checked.

```
You are the <role> agent for <slice>. Do NOT commit. Do NOT create .md files.
Local branch only. Touch ONLY the files named below.

REPO: <cwd> · branch <name> · HEAD <sha> · <N> tests green.

NON-NEGOTIABLE RULINGS (implement, don't relitigate; escalate in your report to override):
1. <ruling + one-line rationale>

SPEC: <files/sections that are source of truth, with line ranges>.

TASK:
1. <sub-step> — verify with: <specific test filter / grep / check>

CONSTRAINTS (repeated): no commits · no test-weakening · no new .md files ·
match existing style · preserve the green count · if a classifier or permission
blocks something reasonable, do the independent sub-steps and note the block —
don't route around it.

REPORT (<500 words): punch list per sub-step · final <check> output tail ·
verification evidence (numeric before/after) · contradictions found · files touched.
```

## Roles are files, not prose

A dispatch names a **role** on disk at `.claude/agents/<name>.md` (SPEC §2.4), carrying its instructions, `tools`, `model` and `effort`. Discovery is reading that directory — no registry, no network call. So a brief says which role and what this job is, not what the role is for; framing you paste into every dispatch belongs in the role file.

**`model` and `effort` are separate knobs.** A strong model thinking briefly and a cheap one thinking hard are different trades. Raise `effort` where being wrong is expensive *and hard to notice* — an audit, a security pass, a claim that something is safe. Leave it alone for mechanical work. **Silent failure:** a role that omits `model` inherits the dispatching session's, with nothing to report it — pin `model` on any role where the tier matters.

**A review pass is a dispatched role too** (SPEC §4) — an agent from the same roster, so a repo can give its security pass a stronger model than its prose pass in one file.

## Rules the orchestrator holds

**Trust but verify — always.** Every "done" gets an independent check: run the test suite yourself, grep the emitted output for the specific claims, spot-check a load-bearing case. Agents summarize what they intended; the diff is what happened.

**Refute-first for reviewers.** Adversarial panels get an explicit "empty report if genuinely clean." Bad reviewers rubber-stamp; the prompt must license silence and reward findings with grounded evidence (quoted line / reproduction / named invariant).

**Overlap 2–3 concerns across reviewers.** Word the briefs to hit certain claims from different angles, then triangulate (see Verification).

**Design agent → orchestrator rules → build agent.** Never design + build in the same agent: the design agent flags decisions, the orchestrator rules on them, the build agent implements a spec already ruled on. Removes a class of "agent silently picked" bugs.

**Budget context, not just time.** A fix agent burning 200 tool uses on failing classifier calls is worse than a scoped rebrief. If an agent stalls, take the partial work, verify what's usable, and dispatch a tighter continuation with the tricky parts pre-decided.

**One fix agent for the batch, not one per finding.** After a panel, consolidate findings, pick fix shapes in the orchestrator layer, and hand ONE brief covering everything — cheaper, coherent, one round of golden regen / fixture update.

**Never delegate the "should we?" question.** A brief that says "decide whether to do X" is a smell — the orchestrator should have decided already. Agents ask the wrong questions the wrong way, or default to the safe/wrong answer.

## Failure modes

- Agent reports "clean" without having run the specific check → independent verification catches it.
- Agent goes off-brief because a subtask blocked → the brief must say "continue with the independent sub-steps if blocked; report the block."
- Model wrong for the task (sonnet on a design decision) → the tiering table above prevents this.
- Fix agent picks the wrong fix shape when it was left ambiguous → state the fix shape per finding, or name the options.
- Cross-repo cwd trips permission classifiers (a Claude Code behavior; other harnesses vary) → never dispatch a subagent cross-repo from a session bound to a different cwd; start a fresh session in the target repo.

## Verification

1. Every "done" verified by a direct diff / test / grep — never by re-asking the agent.
2. Adversarial findings triangulated: 2+ reviewers flagging the same thing = real; 1 reviewer alone = judgment call.
3. The landed commit is authored by the orchestrator (or consensus-reviewed subagent output) — not blind-passed from a report.

## Cross-references

- **REQUIRED COMPANION for UI work:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) — *which gates a slice must clear* (adversarial panels, the browser-driving design-critic gate, fresh-case QA), where this skill covers *how to brief and verify*. Hold only this one elsewhere.
- Authoring the skills your agents load: [skillforge](../skillforge/SKILL.md). Their trigger surface: [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md).

## Sources

- Practitioner-derived from multi-agent slices run at the CTO layer, including the agent-skills skill-unification build (PR #136: 23-agent build/verify workflow run on this skill's model).
