## 2026-08-18 09:13 - Pass the quote marker's column through reopen() so a list column doesn't survive a container boundary the marker never reached (#226)

**Reasoning:** reopen() dropped the LEAF state unconditionally on a container boundary but kept the LIST nesting unconditionally too, correct only when the closing quote sat inside the list item's content column; * item then > at column 0 left the item's column open, so a 4-space indented example under it read as prose (threshold 6, not 4) instead of code -- weaponised in #226 against web-interface-guidelines-review's Verification rule 5, net 0, exit 0. Disclosed by the round-9 lane rather than found by a reviewer.

**Alternatives considered:** Ran the full 20,000-document / 26-construct markdown-it-py adjudication rounds 5-9 used, per the issue's own closing checklist -- rejected for this change: that's #227-scale re-derivation of the whole grammar's FLOOR bands, not a fix to one construct, and the task brief said explicitly not to do it here. Verified narrower instead: 128 generated documents crossing marker width x quote column x quote's-last-block-shape x blank-line presence against markdown-it-py 4.2.0, 0 disagreements.

**Implications:**
- The docstring's WHAT IS STILL WRONG section now says plainly that its aggregate counts (45 minimal forms, the two percentages) describe the pre-fix corpus and were not re-run, so they overstate what remains until the next round regenerates them -- a correction, not a strike, per the do-not-recite-a-number rule. This is the fifth distinct defect fixed in Container.reopen's container-boundary handling (after never-reopens, always-reopens, and indented-block-survives) -- worth flagging for #227, which argues the hand-rolled parser should be replaced with markdown-it-py as the oracle it already is in every round.

---
