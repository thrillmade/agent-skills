← back to [docs/timeline.md](../timeline.md)

## 2026-08-15 09:08 - Bring the three design lenses to house standard, and correct a WCAG level that ships to a client

**Reasoning:** frontend-a11y, visual-polish and design-system-consistency sat at 1,665 to 1,821 body bytes against a 46-skill mean of 4,950, with none of the five required sections and an in-degree of 1. They ship to a client repository on 20 August that then leaves the org and freezes permanently, so for that consumer a thin skill is not temporary. They are now 7,998 to 8,046 bytes, carry the full house frame, and route rather than restate — which is issue #200's actual complaint. frontend-a11y previously asserted WCAG AA 4.5:1 as the contrast model while never naming apca-contrast or wcag-contrast, the two skills that own those thresholds; it now declares both REQUIRED BACKGROUND with stated reasons and defers to the system's declared primary. Written dispatched rather than standalone: reviewing-design-work routes above them and orchestrating-a-multi-agent-run carries the family axioms, so none of the three re-establishes framing something above it already supplies.

**Alternatives considered:** Drop the three from the client handoff to meet the date, which ships a design-critic that cannot cite half its territory; hand them to the consuming lane to fill, which makes another team pay for a gap in my repo under my deadline

**Implications:**
- Corrected a factual error in shipped accessibility guidance. wcag-contrast stated SC 2.4.13 Focus Appearance as Level AA in three places and web-interface-guidelines-review in one. It is Level AAA — verified against the published WCAG 2.2 Recommendation at w3.org, not against a secondary source. The AA hooks are 1.4.11 for the ring's contrast and 2.4.11 for the ring being obscured, and neither skill named 2.4.11 at all. An agent following the old text would report a AAA enhancement as an AA compliance failure, which in an accessibility audit is a claim about legal baseline
- The WCAG fix consumed 43 of web-interface-guidelines-review's 46 bytes of headroom, leaving 3. A file at 3 bytes forces the next editor to delete something, which is exactly the #213 failure. Rather than cut a rule elsewhere I rewrote my own sentence tighter, per the CEO's ruling that a file at the ceiling gets rewritten rather than trimmed. Headroom is back to 49
- All three land at 146 to 194 bytes of headroom and should be treated as at-ceiling: any future addition must displace something. 303 relative skill links across the catalog, zero broken; 112 tests pass; validator clean at 49 skills

---

## 2026-08-15 10:24 - Correct the 2.5.8 spacing exception — the paraphrase was more lenient than the spec

**Reasoning:** The panel found frontend-a11y's rendering of the SC 2.5.8 spacing exception wrong in a way that certifies real failures as passes. It said undersized targets pass when a 24px circle centred on each bounding box does not intersect another target's circle. Verified verbatim against the W3C Understanding document: undersized targets are positioned so that if a 24 CSS pixel diameter circle is centered on the bounding box of each, the circles do not intersect another target or the circle for another undersized target. Two differences, both lenient. Circles are drawn only for undersized targets, not for each target. And against an adequately sized neighbour the test is that neighbour's bounding box, not a circle — a 24px circle centred on a box of 24px or more sits strictly inside it, so comparing circle to circle can never fail there. Concretely a 20 by 20 button one pixel from a 40 by 40 button fails the criterion and passed the skill's rule. That is the dense icon toolbar case the same paragraph tells a reviewer to look at, and it ships to a client who then freezes it.

**Alternatives considered:** Leave the paraphrase and add a caveat, which keeps a rule that reports a real AA failure as a pass

**Implications:**
- Also tightened 2.4.11 from covering to hiding entirely, since the criterion requires the component not be entirely hidden and partial occlusion is 2.4.12 at AAA. Same error shape as the 2.4.13 level: an AAA obligation reported as an AA failure
- The correction pushed the body 45 bytes over the ceiling and the gate caught it — a live instance of #213, resolved the way the CEO ruled. I rewrote my own two additions tighter rather than cutting a rule elsewhere; 8,237 down to 8,128, headroom 64
- This is the second WCAG level error found in this PR's own subject matter, and both were found by an independent panel rather than by the author. The first was 2.4.13 stated as AA in two skills. Guidance that asserts conformance levels needs the primary source read at review time, not recalled

---

