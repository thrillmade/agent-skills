---
version: "1.0.1"
digest: "15a29eec03e2"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: orchestrating-agent-delegation
description: |
  Use when about to dispatch a subagent (or multiple) to execute work, when writing a prompt for another agent that will do the coding, when planning parallel work across agents, when structuring an adversarial review panel, or when a subagent reports "done" and you're about to trust its summary instead of the diff. Names the CTO-as-orchestrator model, the model-tiering table (haiku for exploration, sonnet for build + review + scoped fixes, opus for design agents and load-bearing architecture), the trust-but-verify discipline (verify every "done" against the diff, don't trust the agent's summary), refute-first adversarial reviewer prompts, the design→rule→build separation that prevents agents from silently picking architecture, and the "never delegate the 'should we?' question" rule. Cite when a prompt says "decide whether to do X" (smell — the orchestrator should decide already), when a review panel is prompted to grade rather than refute, when a single agent is asked to both design and build a non-trivial slice, or when a fix agent is dispatched per-finding instead of batched.
---

# Orchestrating agent delegation

The **general delegation mechanics** — briefs, model tiering, verification — for the orchestrator agent (the "CTO layer") that stays in the judgment layer while subagents execute.

## When to use

- Dispatching subagents to non-trivial work, or writing the prompt for the coding agent.
- Planning parallel work across agents.
- Structuring an adversarial review panel.
- Reviewing a draft prompt before it is sent.

## When NOT to use

- Single-shot trivial tasks (typo fix, one-line rename) — direct action beats delegation overhead.
- When you are the executing agent, not the orchestrator — this skill is the layer above.
- Solo work where no delegation is planned.

## Core principles

**1. The orchestrator owns synthesis; agents own execution.** The orchestrator reads the spec, decides architecture, rules on ambiguities, verifies results. Agents implement a spec it has already committed to: "here's what to do, execute + report."

**2. Model tier matches task complexity.** Three tiers — cheap-fast, mid, frontier — named by their Claude instantiations (haiku / sonnet / opus); map to your stack's.

| Task | Tier | Why |
|---|---|---|
| Broad code exploration | haiku | Reading is cheap; depth wasted |
| Adversarial reviewers (refute-first) | sonnet | Pattern recognition + tenacity, not novel reasoning — bump to opus when the correctness surface is subtle or algorithmic |
| Build agents (implementing to spec) | sonnet | Spec removes ambiguity; execution is mechanical |
| Design agents (algorithm/seam design) | opus | Design errors are the expensive ones |
| Build agents on load-bearing architecture | opus | One wrong seam ripples through the rest of the work |
| Fix agents (applying confirmed findings) | sonnet OR opus | Sonnet for scoped fixes; opus if the fix touches algorithm |
| UI design and build | opus, **one agent per surface** | Split UI drifts: lanes take different paths and the seams show |
| Docs / trivial reconciliation | haiku | Throughput matters; quality is deterministic |

**3. Parallelize by file-isolation — and isolate verification separately.** Different files run concurrently; sequence when they share files. Reviewers always parallel (3+ lenses, distinct hunts). Verify isolation. **A UI surface is never split across lanes, even with disjoint files: one `designer` lane on opus owns it whole.**

File ownership stops overwrites, not mis-measurement: any agent in a shared checkout, read-only reviewers included, sees other lanes' half-finished work, so a whole-suite green there is not evidence, a red not attributable. Targeted tests on own files may run there; **a whole-suite claim comes from a disposable worktree at trunk HEAD with only that agent's diff**, and every number names its tree.

**4. Assign the tree in the brief, not just the files** — an agent not told assumes the main one.

## Prompt structure

Blocks in this order: **guard rails** first; **repo context** so a fresh agent lands with a coordinate system; **rulings** numbered and terse, with a rationale where a reader might argue — this is where authority is encoded; **spec** with line ranges so the agent doesn't hunt; **sub-steps** each ending in a scoped, checkable verification, never "make it work"; **constraints** repeated; **report format** exact, because a shapeless report can't be checked.

```
You are the <role> agent for <slice>. Do NOT commit. Do NOT create .md files.
Local branch only. Touch ONLY the files named below.

REPO: <cwd> · branch <name> · HEAD <sha> · <N> tests green.
WORK IN: <main checkout | worktree path>. Other lanes there: <lane → files>; their
files and reds are not yours. Whole-suite claims: worktree at <sha>, only your diff.

NON-NEGOTIABLE RULINGS (implement, don't relitigate; escalate in your report to override):
1. <ruling + one-line rationale>

SPEC: <files/sections that are source of truth, with line ranges>.

TASK:
1. <sub-step> — verify with: <specific test filter / grep / check>

CONSTRAINTS (repeated): no commits · no test-weakening · no new .md files ·
match existing style · preserve the green count · never `git stash` / `reset --hard` /
`checkout -- .` / `restore` / `clean` (they eat other lanes' work) · never
`git add -A` · if blocked, do the independent sub-steps and report the block.

REPORT (<500 words): punch list per sub-step · final <check> output tail ·
verification evidence (numeric before/after) · contradictions found · files touched.
```

## Roles are files, not prose

A dispatch names a **role** on disk at `.claude/agents/<name>.md` (SPEC §2.4), carrying its instructions, `tools`, `model` and `effort`; discovery is reading that directory. A brief says which role and what this job is, not what the role is for — framing pasted into every dispatch belongs in the role file. A review pass is a dispatched role too (SPEC §4).

**`model` and `effort` are separate knobs:** a strong model thinking briefly and a cheap one thinking hard are different trades. Raise `effort` where being wrong is expensive *and hard to notice* (an audit, a safety claim); not for mechanical work. **Silent failure:** a role that omits `model` inherits the dispatching session's, with nothing to report it — pin `model` where the tier matters.

## Rules the orchestrator holds

**Trust but verify — always.** Every "done" gets an independent check: run the suite yourself, grep the output for the specific claims, spot-check a load-bearing case. Agents summarize what they intended; the diff is what happened.

**Refute-first for reviewers.** Panels get an explicit "empty report if genuinely clean." Bad reviewers rubber-stamp; license silence and reward findings with grounded evidence (quoted line / reproduction / named invariant).

**Overlap 2–3 concerns across reviewers** from different angles, then triangulate.

**Design agent → orchestrator rules → build agent.** Never design + build in one agent (UI surfaces are the exception, above): the design agent flags decisions, the orchestrator rules, the build agent implements what was ruled. Removes a class of "agent silently picked" bugs.

**Budget context, not just time.** A fix agent burning 200 tool uses on failing classifier calls is worse than a scoped rebrief: verify a stalled agent's partial work and dispatch a tighter continuation.

**One fix agent for the batch, not one per finding.** After a panel, consolidate findings, pick fix shapes yourself, and hand ONE brief covering everything — cheaper, coherent.

**Never delegate the "should we?" question.** A brief saying "decide whether to do X" is a smell — the orchestrator should have decided. Agents default to the safe/wrong answer.

## Failure modes

- Agent goes off-brief when a subtask blocks → the brief says "continue with the independent sub-steps; report the block."
- Fix shape left ambiguous → agent picks wrong: state it per finding, or name the options.
- Cross-repo cwd trips permission classifiers (a Claude Code behavior; others vary) → never dispatch cross-repo from a session bound to another cwd; start a fresh session there.

## Verification

1. Every "done" verified by a direct diff / test / grep — never by re-asking the agent.
2. Adversarial findings triangulated: 2+ reviewers flagging the same thing = real; 1 reviewer alone = judgment call.
3. The landed commit is the orchestrator's (or consensus-reviewed output), not blind-passed from a report.

## Cross-references

- **REQUIRED COMPANION for UI work:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) — *which gates a slice must clear* (adversarial panels, the browser-driving design-critic gate, fresh-case QA), where this skill covers *how to brief and verify*. Hold only this one elsewhere.
- Authoring the skills your agents load: [skillforge](../skillforge/SKILL.md). Their trigger surface: [skill-frontmatter-quality](../skill-frontmatter-quality/SKILL.md).

## Sources

- Practitioner-derived from multi-agent slices run at the CTO layer, including the agent-skills skill-unification build (PR #136: 23-agent build/verify workflow run on this skill's model).
