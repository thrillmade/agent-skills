---
version: "1.0.1"
digest: "d1f117138319"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: motion-continuity
description: |
  Use when designing, building or reviewing a transition between two states of the same thing — a card that grows into its detail view, a list that reorders, a panel or sheet that slides in and out, a column of items moving as one, an indicator that follows a moving target — or when an animation cuts, jumps when interrupted, runs ahead of what drives it, fades on its own timer, stutters on a phone, or ignores reduced motion in its script path. Framework-neutral: CSS transitions and keyframes, the Web Animations API, View Transitions, scroll-driven animations, or a per-frame loop. Cite when two objects appear mid-transition where there should be one, when a follower overtakes its driver, when related elements land on different frames, when width, height, top or left are animated, or when a requestAnimationFrame loop reads layout every frame. Not the accessibility criteria for motion (frontend-a11y) and not easing or duration token naming (token-naming-conventions).
---

# Motion continuity

Motion between two states exists to tell the reader *this is the same thing, moved*. A cut makes them find it again; a jump makes them doubt what they saw. Every rule below protects that one reading, then keeps it cheap enough to hold at frame rate on the weakest device you ship to.

## When to use

- Designing a state change of one object: open, close, expand, reorder, dismiss, switch.
- Several elements move in one gesture and must read as one.
- An animation stutters, lags its driver, overshoots, or flashes at its end.
- Choosing an implementation: CSS, Web Animations, View Transitions, or a per-frame loop.

## When NOT to use

- **Whether motion must be reducible or pausable** — the criteria (SC 2.2.2, 2.3.3) are [frontend-a11y](../frontend-a11y/SKILL.md)'s; rule 8 only says what the reduced path keeps.
- **Naming easing and duration tokens** — [token-naming-conventions](../token-naming-conventions/SKILL.md).
- **Ambient loops with no state change** — there is nothing to connect; only rules 6–8 apply.

## The rules

**1. An element becomes its next state; it is never replaced by it.** The failure is the cut: the detail view appears and the card it came from vanishes. *Recognise:* a slowed capture has a frame showing two objects where there should be one, or neither. *Fix:* carry one element's geometry from first state to last — the same node animated, or a shared-element transition (View Transitions' `view-transition-name`). Exits animate too; a state that snaps back undoes what the entrance built.

**2. Start from where it is.** An interrupted motion continues from its current rendered position; a reversal reverses from here, not from rest. *Recognise:* a teleport on the frame a second input lands. *Fix:* read the in-flight value (`getComputedStyle`, `animation.currentTime`) before building the next motion — or make interaction motions atomic: queue input, finish the motion, then recompute state from the pointer. Pick one model per system; hover state must be recomputed when any motion ends, or it stays stale.

**3. Pushed, not pulled.** Whatever is driven never gets ahead of its driver. When a column moves as one, nothing gains on what is above it; an indicator following a moving target is derived from the target's position, not animated separately to the target's destination. *Recognise:* in a slowed capture a follower overtakes, overlaps, then settles back. *Fix:* compute the follower from the driver — the same timeline plus an offset.

**4. Related motion shares one clock.** Elements of one gesture start on one timestamp, use one curve family, and land on the same frame; a stagger is an offset on that clock, never a separate timer. Independent timers drift a frame at a time and the arrivals scatter. *Fix:* one timeline — Web Animations with a shared `startTime` on `document.timeline`, or one frame driver computing every element from one `t`.

**5. A fade belongs to its motion.** Opacity is timed into the movement it accompanies: an entrance pre-fades so the element is fully present as it arrives; an exit completes its fade as it leaves, not after. *Recognise:* the last frame of a motion shows an entrance below full opacity, or an exit still visible. *Fix:* put the fade on the same animation as keyframe offsets, not on its own transition.

**6. Animate on the compositor.** Which properties may transition is [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) §9's; travel goes on `transform` (translate, scale, rotate). `filter` is composited in Chromium and WebKit only; most else lays out or paints and misses the budget (16.7 ms at 60 Hz) on the devices you did not test. A size change becomes a `scale` on the container with an inverse scale on its content — and because easing makes two-keyframe scale and counter-scale disagree mid-flight, the content warps: precompute the counter-scale as sampled keyframes (about one per frame) with the easing baked in.

**7. Precompute once per interaction, then hand it to the engine.** Measure the first and last states once, at the start (FLIP: First, Last, Invert, Play), build the keyframes, and give them to CSS or Web Animations to play. A per-frame script that reads layout and writes styles competes with input on the main thread and stalls under load. Motion that follows continuous input — drag, scroll — uses scroll-driven animations (`animation-timeline: scroll()` / `view()`; Chrome 115, Safari 26, Firefox 159 — still behind `@supports (animation-timeline: scroll())` with a frame-loop fallback) or one frame loop that writes transforms and never reads layout.

**8. Reduced motion keeps the meaning, drops the travel.** What `prefers-reduced-motion: reduce` asks for is web-interface-guidelines-review §9's; a short crossfade or an instant change is one compliant technique. The order of events and the end state stay identical; parallax and ambient loops stop. Every path honours it — CSS, Web Animations, script loops, video.

## Silent failures

- **Smooth on the build machine.** Per-frame script holds 60 fps there and scatters on a phone. Throttle the CPU in the trace before believing it.
- **End-state screenshots.** A capture taken after the motion settles cannot show a cut or a jump. Slow it and record — DevTools' animation speed control, or scaled duration tokens plus a slowed clock in any frame loop. Setting `playbackRate` on `document.getAnimations()` slows only what is already running.
- **Reduced motion in CSS only** — [frontend-a11y](../frontend-a11y/SKILL.md)'s silent failure; rule 8 makes every path reach the same end state in the same order.
- **A clip-path shape that holds, then snaps** [observed in WebKit]: a `path()` containing a zero-radius arc does not interpolate. Clamp radii to a small positive value.

## Verification

1. A slowed recording of each transition shows one object throughout, no frame with both or neither.
2. Interrupting mid-flight produces no teleport; hover state is correct after every motion ends.
3. No follower overtakes its driver; related elements land within one frame of each other.
4. A performance trace during the motion shows no per-frame layout or paint, on a throttled CPU.
5. With reduced motion on, the same end state is reached by every path, scripted ones included.

## Cross-references

- **Consumed by:** [thrill-design](../thrill-design/SKILL.md) (principle 5) and [designing-elite-ui](../designing-elite-ui/SKILL.md) (alive interaction, both worked examples); [visual-polish](../visual-polish/SKILL.md) records motion rather than judging stills.
- **Motion criteria and modes:** [frontend-a11y](../frontend-a11y/SKILL.md).
- **Code-level rule set:** [web-interface-guidelines-review](../web-interface-guidelines-review/SKILL.md) flags layout-property transitions in a diff.
- **Testing on the engine that ships:** [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md), [ios-safari-surfaces](../ios-safari-surfaces/SKILL.md).

## Sources

- Rule 1: Material's container transform "creates a visible connection between two UI elements" ([Material Components](https://github.com/material-components/material-components-android/blob/master/docs/theming/Motion.md)); [CSS View Transitions 1](https://www.w3.org/TR/css-view-transitions-1/).
- Rule 6: "Where possible, restrict animations to `opacity` and `transform`" ([web.dev](https://web.dev/articles/animations-guide)); sampled counter-scale keyframes ([Chrome](https://developer.chrome.com/blog/performant-expand-and-collapse)); the 16.7 ms budget is 1000 ms ÷ 60.
- Rule 7: [FLIP](https://aerotwist.com/blog/flip-your-animations/) (Lewis); [Scroll-driven Animations](https://www.w3.org/TR/scroll-animations-1/), support per [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/animation-timeline); shared timelines in [Web Animations 1](https://www.w3.org/TR/web-animations-1/).
- Rule 8: [Media Queries 5](https://www.w3.org/TR/mediaqueries-5/#prefers-reduced-motion).
- **House convention, not a standard:** rules 2–5. No spec says a follower may not overtake its driver; the reasoning is the failure each names.
