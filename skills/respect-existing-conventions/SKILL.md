---
name: respect-existing-conventions
description: Don't suggest changes that fight the codebase's established patterns. Match what's already there.
---

# Respect existing conventions

A code review is not a redesign. The PR author is working within a codebase that has its own conventions, abstractions, and trade-offs that long predate this PR.

## Before suggesting any change, check

- **Is this pattern already used elsewhere in the repo?** If yes, the author is following convention. Don't push them off it.
- **Did the team explicitly choose this approach?** Look at neighboring files, git log on related code, or comments. If the surrounding code already does it this way, that's a signal.
- **Would adopting your suggestion require changing 50 other files?** If yes, your suggestion belongs in a separate refactor PR or RFC, not this review.

## Things that often *look* like problems but usually aren't

- Manual loops where a `.map()` would also work — both are fine.
- Repeated three-line patterns that "could be a helper" — three is below the threshold to justify abstraction.
- Type annotations the language can infer — explicitness is a valid choice.
- Defensive null checks at module boundaries — context-dependent.

## When convention itself is the bug

If the existing pattern *is* the source of the bug, say so explicitly: "the convention used here propagates [specific bug]; this PR should break from it because [reason]." Don't quietly suggest a different approach without naming the trade-off.

The bar for "you should do it differently than the rest of the codebase" is high. Clear it before suggesting.
