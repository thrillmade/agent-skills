← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 12:30 - Retire the 'both models must pass' contrast gate; finish chroma-harmonization's recompose fix (#170)

**Reasoning:** APCA is UDTS's required perceptual gate; WCAG 2.2 is an optional, off-by-default cross-check, not a co-equal required model — apca-contrast and wcag-contrast still taught the pre-UDTS both-required framing after #176 fixed only oklch-color-space and chroma-harmonization's headline. apca-contrast also had no P3-meter rule at all, and chroma-harmonization was missing its two ADD items (recompose-at-shared-chroma, and the bottleneck-residual caveat).

**Alternatives considered:** Could have left 'both must pass' as a stricter-than-required safety net; rejected because it forces P3-native palettes to satisfy an sRGB-era threshold never designed for them, exactly the defect the live UDTS incident was filed against.

**Implications:**
- apca-contrast and wcag-contrast now cross-reference each other's optional/advisory framing; a future doc pass touching either must keep both in sync. chroma-harmonization's recompose step names UDTS's own harmonizeChroma as a known counterexample (verified via the issue's grep against tokenomics source) rather than a template — future contributors reading that source should not copy its clamp-without-recompose behavior.

---

