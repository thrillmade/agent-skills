---
name: guarding-a-regression
description: Use when you have just fixed a bug and are writing the test that stops it coming back, or when adding an assertion, lint rule, schema check, validating constructor or CI gate and claiming it protects something. Fires when a test passed on its first run and was never watched failing, when a regression shipped twice despite a test that covered it, when a guard's green looks identical whether it works or the edit never reached the running code, and when reviewing a test you cannot tell would ever go red. Not `test-discipline`, which reviews a whole test diff for suite decay (deleted assertions, over-mocking, snapshot churn, stray `.skip`); this is one guard, one regression, and whether it can be driven red — including for lint rules, schema checks and CI steps, which sit outside test paths entirely. Load both on a PR that adds a regression test.
---

# Guarding a regression

A guard you have not watched fail is not a guard — it is a line of code that runs.
Two moves make it real, both required: can you drive the system into the broken
state, and can you see that state from where you assert?

The default guard is written *after* the fix, *at the layer just edited*, *never
observed red*. All three defaults go green.

## When to use

- You fixed a bug and are about to write the test that pins it.
- You are adding a lint rule, schema check, validating constructor or CI step
  and saying it prevents something.
- You are reviewing a regression test and cannot tell what would make it fail.
- A bug you fixed came back, and a test covering it was green throughout.

## When NOT to use

- Exploratory or characterisation tests written to *learn* what code does — no
  protected behaviour exists yet, so mutating them means nothing.
- Guards a machine enforces exactly — a TypeScript type, a DB `NOT NULL`. The
  compiler is the guard; don't restate it in a test.
- Additive work with no bug behind it. Write tests — this is about guards
  claimed to hold one regression shut.
- Reviewing a *test diff* for suite decay — deleted assertions, snapshot churn,
  over-mocking. That is `test-discipline`, scoped to test paths. This is
  one guard, one regression, and whether it can go red — including on lint rules
  and CI steps, outside test paths entirely.

## Move one — mutate, then grep for the mutation

Break what the guard protects; it must go red. Then, before believing red *or*
green, confirm the mutation landed in the artifact that ran.

A green after mutation has two causes that print identically:

1. The guard is weak — it never asserted on what you broke.
2. The mutation never reached the running code — wrong file, wrong tree, stale
   build, unimported module. Each gives a truthful result about the wrong code.

Mutation tooling (Stryker, PIT) assumes (2) away and reads a *survivor* — a
mutant tests passed on — as a fact about the test. Treating (2) as (1) sends you
rewriting a guard that was fine. Grep the **running** artifact, not the file you
typed into.

(2) has a name and an incidence. *Build fuzzing* — edit a source file, rebuild,
compare what changed against what you expected — found build faults in 31
open-source projects (Licker & Rice 2019). They fuzz to find bad build rules, you
to validate a guard: same probe, opposite question.

**Where an edit silently fails to land.** npm workspace packages are symlinked
into `node_modules` at install, and one `exports` map can serve a built entry
(`"."` → gitignored `./dist/index.js`) beside **source** subpaths
(`"./theme.css"` → `./src/styles/theme.css`). The CSS edit lands as you save; the
TypeScript edit changes nothing the app imports until something rebuilds. One
package, two behaviours, identical from the editor — that asymmetry is what makes
it silent: your last edit landing teaches nothing about this one.

**Remove the state rather than remember it.** A `prebuild` step that rebuilds the
dependency every time makes a stale `dist` unrepresentable — hand-rolled
hermeticity: same inputs, same output, host-independent.

## Move two — pin at the layer the user experienced the bug

Detection needs four things in order — **reach** the fault, **infect** the state,
**propagate** it to output, **reveal** it to an assertion (the RIPR
model). A test on the helper you just fixed reaches and infects, then stops: the
helper is guarded, the wiring around it is not. That is weak- versus
strong-mutation adequacy (Howden 1982), and the gap is measured — MC/DC-adequate
suites exercised faulty code whose effect never reached the monitored oracle
variables; requiring observability revealed **up to 88% more faults** (Whalen
2013).

So name the layer from the bug report — *a URL returned 500*, *placeholder text
rendered*, *keyboard nav stopped* — and assert there.

**A named authority appears to disagree.** Fowler's *TestPyramid* says to
replicate a bug with a **unit** test first. Both are right; the rule surviving
both is **assert where the fault is observable** — a fault inside a unit is
observable at its output, one in the wiring *between* units is not.

**Worked example — a guard that cannot fail.** Four assertions grepped a component's
*source text* for `/ArrowRight/`, `/PageDown/`, `/Home/`, `/End/` to prove keyboard
support. Delete the `addEventListener("keydown", …)` line (it then greps `0`) and
all four still pass — the strings sit in an `event.key` comparison and survive any
breakage around them. Keyboard navigation dead, guard green, and no parser
catches it: the test-smell
vacuity names (*Unknown Test*, *Empty Test*, *Redundant Assertion*) are
syntactic, and these assertions were real and non-tautological.

The right shape asserts on the bytes a viewer receives — scaffolding text that
reaches them is observable on the response, not on a component:

```js
assert.equal(response.status, 200);
assert.doesNotMatch(html, /react-loading-skeleton|taking shape/i);
```

## Guards that are not tests

Lint rules, schema validators, validating constructors and CI steps are guards
too, and the literature above is about executable tests. Their commonest failure
is different: **nothing routes through them**.

**Worked example.** A constructor clamping line-height —
`leading: exempt ? leading : Math.max(1.2, leading)` — correct, with a docstring
calling it load-bearing. Grep its exported names across `.ts .tsx .js .mjs .css`:
every hit is inside its own file, nothing imports it. The live values are
hand-authored elsewhere as absolute rem, not a unitless ratio, so a breach is
invisible until you divide size by leading.

A guard nothing routes through can never go red. One mutation on day one — set a
leading to 0.9, watch nothing happen — shows it.

## Verification

Claim a guard holds only when you can show all four:

- [ ] The command that broke the protected thing, and the guard's **red** output.
- [ ] The grep proving the mutation was in the artifact that ran — built `dist`,
      staged assets, the resolved `node_modules` path — not the file you edited.
- [ ] The tree it ran in (`git worktree list`), matching the one you mutated.
- [ ] The assertion at the layer named in the bug report, quoted. If they all sit
      a level below it, the regression is not pinned.

For a lint rule, schema or constructor, add a grep showing a real caller routes
through it.

## Cross-references

- **REQUIRED BACKGROUND:** `superpowers:test-driven-development` — what "red"
  must mean to count.
- [proving-an-absence](../proving-an-absence/SKILL.md) — move one's primitive.
  "The mutation never reached the code" is an absence claim; the grep proving it
  landed is its control test.
- [test-discipline](../test-discipline/SKILL.md) — a suite's decay across a
  diff; this, one guard.
- [orchestrating-elite-agent-qa](../orchestrating-elite-agent-qa/SKILL.md) — the
  build→panel→QA gate this is step three of; the panel checks these boxes.
- [orchestrating-agent-delegation](../orchestrating-agent-delegation/SKILL.md) — a
  brief naming the tree makes a wrong-tree mutation detectable.
- `superpowers:systematic-debugging` finds the layer the bug was hit at;
  `superpowers:verification-before-completion` is the general form.

## Sources

- RIPR — Ammann & Offutt, *Introduction to Software Testing* 2e (2016); verbatim
  in Papadakis et al., *Advances in Computers* 112 (2019) p.15,
  doi:10.1016/bs.adcom.2018.03.015.
- Howden 1982, weak vs. strong mutation, doi:10.1109/TSE.1982.235571 · Whalen et al.,
  "Observable MC/DC", ICSE 2013, doi:10.1109/ICSE.2013.6606556 — the 88%, on
  avionics models, hence "up to" · Licker & Rice, "Detecting Incorrect Build Rules",
  ICSE 2019, doi:10.1109/ICSE.2019.00125.
- Definitions — Bazel *Hermeticity*; npm *workspaces* and Node *Packages*
  (conditional/subpath exports); test smells, testsmells.org; Fowler,
  martinfowler.com/bliki/TestPyramid.html; killed vs. survived,
  stryker-mutator.io/docs; move two,
  testing-library.com/docs/guiding-principles/
