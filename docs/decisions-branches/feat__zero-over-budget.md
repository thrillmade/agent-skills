← back to [docs/timeline.md](../timeline.md)

## 2026-08-14 20:49 - Zero over budget: pay the 8,543-byte debt, then delete the exception mechanism entirely

**Reasoning:** The ratchet #203 shipped stopped regression but nothing drove the debt down, so a grandfathered entry could sit at its recorded size forever and the policy quietly became over-budget-is-fine-if-you-got-there-first. Ruled zero over budget. The four entries were paid off by editorial trimming — narration, duplication, and content a neighbour already owns replaced with links — and each trim enumerated the file's normative rules before cutting and checked the list survived. Then the mechanism itself was removed rather than merely emptied: skill-size-budget.json is deleted and SIZE_LIMIT is a constant in the workflow. Emptying the list while leaving limitBytes in a data file would have moved the escape to a worse lever, because a grandfather row exempts one skill visibly and in review while the limit exempts all 46 at once and silently. Removing the data file closes both: there is no list to add to and no number to raise.

**Alternatives considered:** Keep a reviewed exception path for a skill that genuinely cannot fit; empty the grandfather list but leave limitBytes in a data file

**Implications:**
- There is deliberately no escape hatch left. The budget is not a style rule — an oversized skill is already broken for its consumer whether or not it is blessed, because truncation is silent and lossy at the point of use and the author sees a complete file and a green build. So there is nothing for an exception to be an exception to. When a skill genuinely cannot fit after honest trimming the honest answers are that it is two topics and should be split, that it is tool-reference documentation rather than a knowledge skill, or that the consumer's ceiling is wrong and belongs upstream at clud-bug#301
- The back-inside-the-budget branch becomes dead code and is kept only as a safety net if an entry is ever added deliberately during a future migration. It stops being load-bearing
- An adversarial review verified the trims independently rather than accepting the author's rule count: every normative token present in the before-state was traced to a surviving reformulation or a verified deduplication. It found one silent improvement nobody claimed — logmind's numbered list ran 1,2,3,5 and was corrected to 1,2,3,4 — and orchestrating-agent-delegation's brief skeleton gained guard rails the base carried only in prose
- Margins are now thin and worth watching: test-discipline sits at 8191 with one byte of headroom, clud-bug-collaboration at 8186 with six. The next edit to either fails the gate, which is the intended behaviour and not a defect

---

## 2026-08-14 20:50 - Correct the debt figure in this branch's own decision entry: 7,935 over budget, 8,543 removed

**Reasoning:** The previous entry's summary calls 8,543 the debt. It is not. The debt — bytes over the 8192 ceiling — was 7,935: logmind 3,190 plus clud-bug-collaboration 2,785 plus orchestrating-agent-delegation 1,958 plus web-interface-guidelines-review 2. The 8,543 figure is the reduction actually made across those four skills, which exceeds the debt because the trims went below the line rather than stopping at it. Two different quantities, and conflating them tells a reader the catalog was 608 bytes further over budget than it was. The same discrepancy exists in the PR body, which cites 7,935 as the reduction; net across all five changed skills is -8,440, since component-sizing-principles gained 103 bytes.

**Alternatives considered:** Amend the earlier entry, which would need a force-push on a pushed branch; leave it, since the conclusion is unaffected

**Implications:**
- Both numbers are worth keeping and they answer different questions: 7,935 is how much debt existed, 8,543 is how much editorial work was done, and the gap between them is the headroom the trims bought. Margins are now thin — test-discipline at 8,191 has one byte, clud-bug-collaboration at 8,186 has six
- Found by the local review pass on my own commit, which is the third time this session a number I wrote was wrong in a way only measurement caught. Recite nothing; compute it

---

