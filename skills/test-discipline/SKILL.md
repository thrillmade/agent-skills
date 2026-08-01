---
name: test-discipline
description: Review test changes for the patterns that hollow out a test suite over time — overly-mocked tests, snapshot churn, asserting on the implementation, deleted tests without replacement, skipped tests left in the diff, and "fix the test to match the new behavior" without thinking about whether the old assertion was load-bearing. Apply to any PR that adds, deletes, or modifies test files.
applies_to:
  paths:
    - "test/**"
    - "tests/**"
    - "spec/**"
    - "specs/**"
    - "**/__tests__/**"
    - "**/__test__/**"
    - "e2e/**"
    - "integration/**"
  extensions: [".test.ts", ".test.tsx", ".test.js", ".test.jsx", ".test.py", ".test.go", ".test.rb", ".spec.ts", ".spec.tsx", ".spec.js", ".spec.jsx", "_test.py", "_test.go", "_spec.rb"]
---

# Test discipline

Tests don't decay because anyone wrote a bad test on purpose. They decay because a hundred small "make the test pass" edits accumulate, each one defensible in isolation, until the suite no longer catches the bugs it was written to catch.

This skill flags the categories of test edit that quietly hollow out the suite. The bar is not "this test is bad" — it's "this test edit makes the suite less useful than it was before this PR."

Apply this skill any time a diff touches `*.test.*`, `*_test.*`, `__tests__/`, `tests/`, `spec/`, `test/`, or any other test file or fixture.

## Categories to flag

### 1. Deleted assertions without replacement

```diff
  it('charges the customer card', async () => {
    const order = await placeOrder({ ... })
    expect(order.status).toBe('paid')
-   expect(charge.amount).toBe(2499)
-   expect(charge.currency).toBe('usd')
  })
```

The remaining assertion (`status === 'paid'`) doesn't catch the regression class the deleted ones were guarding (wrong amount, wrong currency). If the deleted assertions are obsolete because the behavior changed, the replacement assertions need to live somewhere — same test, different test, integration test. Flag and ask: *what's the new check that protects this code path?*

### 2. Tests deleted entirely, no replacement in diff

```diff
- describe('checkout flow', () => {
-   it('rejects expired cards', () => { ... })
-   it('handles 3DS challenge', () => { ... })
- })
```

Sometimes deletion is right — the code under test was removed, the test was a duplicate, the test was flaky and unfixable. But the PR description should say which case it is. If the description just says "remove old tests," that's the smell. Flag and ask for the reason.

### 3. Tests rewritten to match new (buggy?) behavior

```diff
- expect(parseAmount('1,234.56')).toBe(1234.56)
+ expect(parseAmount('1,234.56')).toBe(123456)
```

The assertion changed in the same PR that changed the implementation. Either the old assertion was wrong (in which case there should be a separate "bug found, here's the fix" commit and the regression is documented), or the new code is wrong and the test was edited to make it pass. Flag and ask: *was the old behavior correct, and what changed in the spec?*

### 4. Mocks that hide what the test should verify

```diff
+ jest.mock('./billing', () => ({ chargeCard: jest.fn().mockResolvedValue({ ok: true }) }))
+ it('completes checkout', async () => {
+   await completeCheckout({ ... })
+   expect(navigate).toHaveBeenCalledWith('/thank-you')
+ })
```

The test passes if checkout calls billing with literally any arguments — wrong amount, wrong customer, wrong card. The mock returns `{ ok: true }` regardless. This test now catches navigation regressions but no longer catches billing regressions. Either the mock is doing too much (replace with a stub that records args + assert on args), or the test is in the wrong layer (move to a unit test of the navigation logic alone).

### 5. Snapshot tests on rapidly-changing output

```diff
+ expect(renderInvoice(order)).toMatchSnapshot()
```

Snapshots are a smell when the output they capture has many fields and a high churn rate. Six months from now the snapshot file will have been "regenerated to match new behavior" twenty times, with no human review of what *actually* changed. Prefer assertions on the specific fields the test was written to protect. Snapshots are fine for stable, dense output (parser ASTs, deterministic serialization) — flag them on UI output, JSON payloads, log lines.

### 6. `.skip` / `.only` / `xit` left in the diff

```diff
+ it.skip('handles the refund case', () => { ... })
+ describe.only('checkout', () => { ... })
```

`.skip` is a TODO marker that won't run. `.only` makes CI silently skip every other test. Both ship green CI and break the suite's coverage. Flag every occurrence — the question is "is this intentional, and is there a tracking issue?" Acceptable answers: yes + linked issue. Unacceptable: "oops, debug leftover."

### 7. `if (process.env.CI)` skip gates

```diff
+ it('integration test', async () => {
+   if (!process.env.RUN_INTEGRATION) return
+   ...
```

Tests that skip themselves based on env var run in some environments but not others, and the silent-skip path means CI looks green when the test never executed. Either the test runs everywhere, or it lives in a separate suite that's explicitly named (`integration.test.ts`). Flag the in-test skip.

### 8. Tests for code paths that don't exist yet

```diff
+ it('handles WebAssembly modules', () => {
+   // TODO: implement when wasm support lands
+   expect(true).toBe(true)
+ })
```

A green test that asserts nothing is worse than no test — it gives false confidence. Either delete it or implement the assertion.

### 9. Time-dependent assertions without freezing time

```diff
+ expect(createTimestamp()).toBe(new Date().toISOString())
```

This passes on the local machine in the same millisecond and fails in CI. The fix: freeze time with `jest.useFakeTimers()` / `sinon.useFakeTimers()` / equivalent, then assert on the frozen value. Flagged for the flakiness it creates.

### 10. Asserting on internal state, not observable behavior

```diff
+ expect(component.state.isOpen).toBe(true)
+ expect(internalCache.size).toBe(3)
```

These assertions break when you refactor the component to use a different state shape — even though the externally-visible behavior is unchanged. Either move the assertion to the public surface (what does the user *see* when `isOpen` is true?), or accept the coupling and document it. Flag with a question: *can we assert on the rendered output / API response instead?*

## Categories that are NOT smells

To stay calibrated, here's what *looks* like a problem but usually isn't:

- **A test rewriting itself to use a new API as the production code's API changed** — that's correct. Production API change + test rewrite move together. The smell is the test rewriting to a different *assertion* than the old one.
- **A test moved to a different file** — fine if the assertion is preserved. Smell if the assertion is silently lost in the move.
- **A small number of `expect`s per test (1-3)** — that's good; tightly scoped tests are easier to diagnose than mega-tests.
- **Tests for newly-added code paths landing alongside the code** — that's what TDD looks like, regardless of whether the test was written before or after.

## Finding-shape template

> [test-discipline] **<category>**: `<file>:<line>`
>
> ```diff
> <the offending diff>
> ```
>
> **Regression class this no longer catches:** <what specific bug could now slip through>
>
> **Suggested fix:** <one of: keep the old assertion, move it to a different layer, replace the mock with a stub-with-asserts, link a tracking issue for the `.skip`>

The most useful framing is *what bug could slip through now*. That gives the author a concrete reason to push back ("we have an integration test that catches this case") or a concrete fix ("you're right, I'll keep the amount assertion").

## When this skill should be silent

- The PR doesn't touch any test files or fixtures.
- The test changes are purely mechanical (rename, import path update, formatting) with no assertion changes, no skips, no mocks added.
- The PR is removing tests AND removing the production code those tests covered (clean removal of a feature; the test is correctly going with it).

In any of those cases:

> [test-discipline] n/a — no behavioral test changes in this diff.

## Working with the existing suite

Before flagging, scan the rest of the suite for context:

- If the codebase already has integration tests covering the path your skill is worried about, downgrade unit-level deletions ("integration test at `<path>` still covers this regression class").
- If the codebase uses snapshot tests pervasively (it's the established convention), don't flag every snapshot — only flag snapshots on rapidly-changing output that's likely to churn.
- If the codebase has a documented testing strategy (`TESTING.md`, `docs/testing.md`), defer to it. The skill is the fallback when there's no project-specific guidance.
