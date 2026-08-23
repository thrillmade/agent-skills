← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 12:38 - frontend-a11y: name SC 2.5.8's missing Inline exception, fix box-vs-target wording

**Reasoning:** The lens named only the Spacing exception with the definite article, so inline links in body copy -- undersized by construction and exempt under WCAG 2.2's Inline exception -- were reported as SC 2.5.8 AA failures on every rendered page reviewed. Line 66 also tested the 24px circle against 'another target's box', stricter than the normative text ('another target'), which fails a target whose real region clears a rounded-corner neighbour but whose bounding box does not. Verified both directly against the W3C WCAG 2.2 source (curl'd https://www.w3.org/TR/WCAG22/, not a paraphrase): five exceptions -- Spacing, Equivalent, Inline, User Agent Control, Essential -- and the Spacing text intersects 'another target', using the bounding box only to center the circle.

**Alternatives considered:** Move the exception list to a references/ subdirectory instead: rejected, clud-bug#305 is still pending so that consumer reads only SKILL.md and the move would delete the content from what a reviewer actually sees. Wait for #201's progressive-disclosure mechanism: rejected, this skill ships to a client on 20 Aug and #201 is not built. Name only Inline and skip Equivalent/User Agent Control/Essential: rejected, the issue's own probe measures presence of all four names, and naming them costs little once Inline's explanation is already in the sentence.

**Implications:**
- Body was 8129/8192 bytes (63 headroom) before this change; the fix needed roughly 160 bytes so ~135 bytes were trimmed elsewhere (a duplicate MDN/native-semantics citation, a duplicate 'mode not captured' recap, and a Verification bullet rewrap) to land at 8168/8192 (24 headroom) rather than deferring to #201. Net prose word count did not drop, so no docs/prose-removals.md row was needed -- confirmed by running check_prose_retention.py against origin/dev, which reported no undeclared loss. The cosmetic 24px 'diameter' wording from the same issue was left unfixed for lack of bytes; #201 remains the real fix for headroom, not this stopgap.

---

