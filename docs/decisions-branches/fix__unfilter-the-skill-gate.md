← back to [docs/timeline.md](../timeline.md)

## 2026-08-15 07:59 - Delete the skill gate's paths filter rather than extending it, and assert it stays gone

**Reasoning:** The filter had to enumerate every input the validator reads, and the enumeration rotted. It never listed skills/skill-size-budget.json, so for the entire life of the size ratchet a pull request editing only the budget did not run the gate that budget configures — raising the limit could disable the gate without triggering it. Extending the list fixes that instance and ships the next: the planned mirror gate reads .claude/skills, the suite reads tests. The second reason is the one this repo already wrote down: GitHub treats a filter-skipped check as expected but never reported, so once a required_status_checks rule names it, a pull request touching none of the filtered paths blocks forever. check-doc-links.yml says exactly that at lines 8 to 12. agent-skills has zero required status checks today, which is why this is free to fix now and expensive later. The run is 11 to 13 seconds over 48 files.

**Alternatives considered:** Add the missing paths one at a time, which fixes the instance and leaves the class; keep the filter and accept that a budget-only edit skips its own gate

**Implications:**
- A committed test now fails if any paths or paths-ignore key is reintroduced on validate-skills.yml or test.yml, with the reason in the assertion message. Mutation-tested: adding a filter back turns two tests red, removing it returns 112 green. So the next filter has to be argued for rather than merely typed
- The test scopes to merge gates only. A scheduled refresh or a notifier has no such constraint and may filter freely; the list of unconditional gates is explicit in the test file
- PyYAML resolves the workflow key on: to the boolean True under YAML 1.1, so the test looks the key up both ways. A naive doc.get('on') finds nothing and the assertion passes by vacuity — which would be a guard that never fires, the exact defect class this repo keeps finding

---

