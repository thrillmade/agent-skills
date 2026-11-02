---
version: "1.0.0"
digest: "a57bad98b860"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: ios-safari-surfaces
description: |
  Use when a web page ships to Safari on iPhone and the browser's own surfaces misbehave — the address or tab bar shows the wrong colour, flips colour on scroll, or takes on a fixed header's or toast's colour; theme-color does nothing; a scroll lock, sheet, modal or scroll-to-top works on desktop but not on the phone, or the page reports scrollY 0 while the screen shows it scrolled; a full-bleed first screen is the wrong height or jumps as the bars move (svh, lvh, dvh, 100vh) — and when planning how to test any iPhone-Safari bug, since Responsive Design Mode and headless WebKit do not reproduce these. Covers iOS 26 and later, the WebKit bar-tint sampling rule, the screen-versus-page scroll desync, viewport units for a first screen, and the iOS Simulator as the test harness (xcrun simctl). Not for native iOS apps, not for Android Chrome's theme-color, and not for general responsive layout (composing-a-screen).
---

# iOS Safari surfaces

Safari on iPhone does two things no desktop engine or emulator reproduces: it paints its own bars from your page, and it scrolls the screen in a different process from the one your script runs in. Both fail silently — the build is green, the desktop render is right, and the phone shows the wrong colour or a page that will not move.

Each claim is labelled: **[source]** read in WebKit source at the commit in Sources; **[secondary]** reported by others; **[observed]** reproduced in the iOS Simulator and on a device, mechanism not traced in source.

## When to use

- A full-bleed first screen, cover, fixed header or fixed footer ships to iPhone.
- The bars show the wrong colour, or change colour as you scroll.
- Scroll lock, a sheet, a modal or scroll-to-top works on desktop and not on the phone.
- Choosing `svh`, `lvh` or `dvh`; planning how to test an iPhone-Safari bug.

## When NOT to use

- **Native iOS apps** — the bars are yours to set; none of this applies.
- **Android Chrome** — it has its own tinting model; this one is WebKit's.
- **Responsive layout in general** — [composing-a-screen](../composing-a-screen/SKILL.md); targets and motion modes — [frontend-a11y](../frontend-a11y/SKILL.md).

## Bar tinting (iOS 26+)

**The model.** `<meta name="theme-color">` is ignored [secondary]. Both bars take the page's background colour unless a viewport-constrained box owns an edge [secondary, consistent with source]. Each edge is decided separately: WebKit hit-tests a point 4 px in from the midpoint of that edge and walks up to the first `position: fixed` or `sticky` ancestor that qualifies [source]:

- its length along the edge is at least **0.9** of the viewport's (short along it but full-length on the adjacent side is a *sidebar*: it still owns the edge, its colour kept or sampled);
- it is not hidden or nearly transparent; a `backdrop-filter` in its lineage yields no single colour.

Thickness decides how the colour is read, not ownership. Over **10 px** both ways, the box's declared background is used; at **10 px or less**, the bar is pixel-sampled from a 2 px band 4–6 px in — a ~6 px strip still tints it, a 1–4 px strip misses the sample.

The owning box's background colour is read live, so changing it recolours the bar. Once a box has owned an edge, ownership stays with it [observed]: swapping in a different box mid-page may not take.

**What breaks.** A full-width fixed header paints the top bar its colour whether you meant it or not. A full-width toast recolours the bottom bar while shown. A first screen whose ground differs from the root's background gets bars in the root's colour, not its own.

**The fix.** Decide per edge what colour the bar should be, then make one thing true: either the root background is that colour, or a qualifying box owns that edge — e.g. a full-width fixed strip 12 px tall in that colour, so its declared background is used rather than sampled. Ship it in critical CSS, present from first paint; scope it to touch input (`@media (hover: none) and (pointer: coarse)`) so desktop is untouched; when the ground changes, change the strip's colour, not the strip.

## Screen versus page scroll [observed]

The screen scrolls in Safari's own process; a scroll from script is a request to it. Two requests never land:

- **A scroll asked of a root in the frame it is locked** (`overflow: hidden`) is dropped.
- **A scroll to where the page already believes it is** is never sent. After a desync the page reports `scrollY` 0 while the screen shows it scrolled, so `scrollTo(0, 0)` does nothing.

*Fix:* hold the root scrollable for two animation frames, scroll to 1 px off the target, then to the target, and only then lock. One helper, used by every scroll lock and every scroll-to-top.

## Viewport units for a first screen

[CSS Values 4](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths) defines three viewports: small (`svh`, bars expanded), large (`lvh`, bars retracted) and dynamic (`dvh`, follows the bars).

- **A first screen that must fit and never jump:** `100svh`. It is never hidden behind the bars and never resizes as they move.
- **A backdrop that must cover what the bars uncover:** `lvh`.
- **`dvh` only where resizing during scroll is the intent** — it relayouts as the bars move.
- **`vh` is the UA's choice** of one of the three; Safari resolves it to the large viewport [secondary], so `100vh` content sits under expanded bars.

## Testing: the Simulator is the test

- **Responsive Design Mode is not a test** [observed]: it misreports `svh` (first screens at half height, scroll stopping) and runs neither bar tinting nor the separate scroll process. A narrow desktop window is evidence about layout only.
- **The iOS Simulator** (Xcode): `xcrun simctl boot "<device>"`, `xcrun simctl openurl booted <url>`, `xcrun simctl io booted screenshot out.png`, `xcrun simctl io booted recordVideo out.mov` — recordings show the bars, which in-page screenshots cannot.
- **No touch input from simctl.** Drive the interaction with a test-only script injected into the served page behind a query parameter, never shipped.
- **Log same-origin.** Fetches and beacons from Simulator Safari to another localhost port did not arrive [observed]; serve the page and a log endpoint from one origin.
- **Control first.** Reproduce the bug in the harness on the old build before trusting a "fixed" capture; a harness that cannot show the bug proves nothing ([proving-an-absence](../proving-an-absence/SKILL.md)).

A real device remains the last word on feel; the Simulator is where you reproduce and measure.

## Silent failures

- **The bar matches a header added for another reason** — a full-width fixed or sticky box reaching past 4 px from the edge owns it even when thin; one of 4 px or less is never hit.
- **A strip mounted after hydration** — the first paint has the wrong bar, then it flips.
- **A dropped scroll-to-top** after closing a sheet: the page thinks it is already at 0.

## Verification

1. A Simulator recording, not a screenshot, shows each edge's bar colour at the top of the page, mid-scroll, and with every fixed overlay open.
2. Every edge's intended colour is written down, and the box or root background that produces it is named.
3. Lock, unlock and scroll-to-top were exercised in the Simulator after a scroll, and landed.
4. The first screen fits at `svh` with bars expanded and does not resize as they retract.
5. The harness reproduced the original bug on the old build before it was trusted on the new one.

## Cross-references

- **Real engine, real device:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) — an emulator is evidence about modules, not the product.
- **Consumed by:** [thrill-design](../thrill-design/SKILL.md) (principle 7).
- **Motion on the phone:** [motion-continuity](../motion-continuity/SKILL.md).

## Sources

- [source] WebKit `LocalFrameView::fixedContainerEdges` at [d291551](https://github.com/WebKit/WebKit/blob/d2915517219320e0fdfbfc4a59c168337d982292/Source/WebCore/page/LocalFrameView.cpp): `minimumRatio = 0.9` against the viewport length on that side and `isFixedPositioned() || isStickilyPositioned()` in `containerEdgeCandidateResult` (sidebars returned as owners); `thinBorderWidth = 10` checked only in `primaryBackgroundColorForRenderer`, falling back to `PageColorSampler::predominantColor`; `fixedContainerSampleRectMargin = 4` and `sampleRectThickness = 2` (`PageColorSampler`); backdrop filter → multiple colours.
- [secondary] [WebKit bug 301756](https://bugs.webkit.org/show_bug.cgi?id=301756) — tint from the page background, theme-color unused. [Ben Frain](https://benfrain.com/ios26-safari-theme-color-tab-tinting-with-fixed-position-elements/) on fixed elements recolouring the bars.
- [CSS Values 4](https://www.w3.org/TR/css-values-4/#viewport-relative-lengths) for the three viewports and the UA-defined `vh`.
- `xcrun simctl help` for the Simulator commands.
- [observed] the scroll desync, the Responsive Design Mode misreport and the cross-port logging loss: reproduced in the Simulator and on device; not traced in source.
