← back to [docs/timeline.md](../timeline.md)

## 2026-11-12 17:14 - Skill content tranche: public skills stop citing the private spec; UDTS specifics in three colour primitives become marked examples; decision-artifact anti-patterns name their cost (#311); interface-copy rule 11, siblings of one role take one shape (#305)

**Reasoning:** A public reader cannot open the private spec, so each rule it backed is now stated as the skill's own and sourced as from practice. The colour primitives promise universal rules, so one system's choices are marked as examples instead of stated as the rule. #311 and #305 were agreed and waiting on byte room; each is paid for with cuts of text another skill already owns.

**Alternatives considered:** Publishing the spec (not this change's call, and the skills state the rules anyway). Moving the UDTS content into the udts-* stubs (they say they are not guidance yet). A separate skill for parallel form (one rule in the existing skill is enough).

**Implications:**
- Thirteen skills restamped with patch bumps and eleven ledger rows added. The descriptions of apca-contrast and chroma-harmonization changed and no trigger evaluation was run. The colour family's gating stance (APCA required, WCAG optional) is unchanged here and waits on the owner. This supersedes the UDTS counterexample recorded in fix__color-srgb-default. Not done here: the apcach round-trip claim in oklch-color-space, and unmarked product mentions in three sibling primitives.

---

## 2026-11-12 17:42 - Review fixes to the content tranche: colour claims checked against the libraries and recomputed, one more private-spec citation removed, apca-contrast says one thing

**Reasoning:** Three reviewers read the first commit. They found a fourth skill (conventions-template) still citing the private spec; apca-contrast made conditional in its description but absolute in its body; two claims about the apcach library that its README and source do not support (an accuracy guarantee, and a forced sRGB hex round-trip for the background); a chroma-limiter claim that a computation contradicts (the narrowest hue below L 0.7 is near 200, cyan to azure, in sRGB and Display P3 alike, not blue); and WCAG's large-text thresholds given in px where the standard says points.

**Alternatives considered:** Finishing the gating-stance change inside this PR (it is the owner's pending decision, so the skill is restored to dev's stance wording instead). Leaving the pre-existing colour errors for a later pass (they sat in sentences this change rewrote).

**Implications:**
- Fourteen skills changed in total. The apcach round-trip correction listed as not done in the first entry is now done. culori's displayable() is named as an sRGB check, with inGamut('p3') for Display P3. Still unsupported and left as they were: the px and weight pairings in the Lc table, and the drift of about 5 Lc across hues. No trigger evaluation was run on the three changed descriptions.

---

