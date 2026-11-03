---
version: "1.0.0"
digest: "14afd0862089"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: pii-and-compliance
description: Catch PRs that ship PII into logs, error messages, exception traces, analytics events, or third-party services. Flag emails, phone numbers, addresses, full names, government IDs, credit card numbers, IP addresses, and secret material that should never leave the application boundary. Apply to logging calls, telemetry events, error-handler payloads, debug statements, and external API calls.
---

# PII and compliance

This skill catches the single most common compliance leak in production code: putting personally identifiable information (PII), authentication material, or sensitive business data into places it shouldn't go — logs, error traces, analytics events, third-party SDK payloads, debugger statements.

Most teams know the rule "don't log PII." Most teams ship code that violates it anyway, because the leak happens inside an interpolated string ten frames deep from where the developer was thinking about the rule. This skill is the second line of defense.

## What counts as PII

In rough order of sensitivity:

1. **Direct identifiers**: government ID numbers (SSN, passport, driver's license), credit card numbers (full or BIN+last4), bank account numbers, full social security numbers in any partial form including last-4 if combined with name.
2. **Strong-signal indirect identifiers**: full email addresses, phone numbers, full names, full street addresses, dates of birth, biometric data, precise geolocation coordinates.
3. **Authentication material**: passwords, API keys, OAuth tokens, JWT bodies, session tokens, password-reset tokens, signed URLs, webhook secrets, private keys, recovery codes.
4. **Sensitive business data**: trade secrets, unpublished financials, M&A info, internal employee performance reviews, customer prospect lists.
5. **Reduced-signal indirect identifiers**: IP addresses, user-agent strings, device fingerprints, partial postal codes — these are PII under GDPR and CCPA when joined with other data your service holds.

## Forbidden destinations

PII or auth material should never appear in:

- **Logs** — application logs, request logs, structured log fields, debug logs, info/warn/error levels. Logs land in centralized storage where access control is coarser than your DB.
- **Exception traces / error messages** — Sentry, Rollbar, Honeybadger, native stack traces. Sentry's filters help but don't replace not logging it in the first place.
- **Analytics events** — Mixpanel, Amplitude, Segment, Google Analytics, Heap, Posthog. Marketing tools have weaker access control than your own systems.
- **CI logs** — GitHub Actions, CircleCI, GitLab CI output. Public repo CI output is world-readable.
- **Tracing spans** — OpenTelemetry attributes, Datadog span tags, X-Ray annotations.
- **URLs (path, querystring, fragment)** — URLs land in proxy logs, browser histories, referrer headers, third-party analytics.
- **Email/Slack/PagerDuty bodies** — alert payloads should reference IDs, not contents.
- **Test fixtures committed to git** — fake names and emails only. Never real customer data.

## Patterns to flag

### 1. Direct PII in log strings

```diff
- logger.info('user logged in', { email: user.email, name: user.name })
+ logger.info('user logged in', { userId: user.id })
```

The pattern to enforce: **log identifiers, not contents.** A `userId` lets an operator join back to the user record through audited access controls. The email lets anyone who can read logs read the email.

### 2. PII in error payloads

```diff
- throw new Error(`Failed to verify token ${token} for user ${email}`)
+ throw new Error('Token verification failed')   // log userId separately via structured logger
```

Exception messages travel further than logs — they end up in alerting, paging, screenshots, error-tracking SaaS. Strip the payload from the message; structure it through your logger if the operator needs it.

### 3. Auth material in URLs

```diff
- fetch(`/api/reset?token=${token}`)
+ fetch('/api/reset', { method: 'POST', body: JSON.stringify({ token }) })
```

URL components leak into browser history, proxy logs, referrer headers, and CDN logs. Put credentials in headers or POST bodies.

### 4. Console / debug statements left in production code

```diff
+ console.log({ user, password, token })   // <-- removed before merge?
```

These are almost always leftover debug statements. The signal: variable names like `password`, `token`, `apiKey`, `secret`, `credential` appearing in a `console.log` / `print()` / `puts` / `fmt.Println`. Flag every one.

### 5. Analytics events with too much detail

```diff
- analytics.track('purchase', { email, card_last4, amount, address })
+ analytics.track('purchase', { product_id, amount })
```

Marketing analytics needs aggregates, not individual identifiers. The pattern: aggregate-shaped events (counts, IDs, denormalized categories), never raw form-field values.

### 6. Test fixtures with real-looking data

```diff
+ const users = [
+   { email: 'jane.smith@gmail.com', phone: '+1-415-555-1234', ... }
+ ]
```

Use obviously-fake data: `alice@example.com`, `+1-555-000-0001`, `Jane Test`. The `.example.com` TLD is reserved for examples. The `555-01xx` range is reserved for fictional phone numbers. There's no "obviously fake" SSN — use `000-00-0000` or skip the field.

### 7. Webhook / API replay payloads committed to fixtures

A Stripe webhook fixture committed to test data contains real card BINs, real customer IDs, possibly real email metadata. Either heavily redact (`card_id: 'card_xxxxxxxxxxxxxxxx'`) or generate fixtures from a sanitized factory.

### 8. PII in feature flag payloads

```diff
- flag.evaluate('show-checkout-v2', { email: user.email })
+ flag.evaluate('show-checkout-v2', { userId: user.id, tier: user.tier })
```

LaunchDarkly / Statsig / Unleash payloads land in their SaaS. Send the minimum signal needed for targeting.

### 9. Wide-allow log filters

```diff
+ logger.add(transports.console({ level: 'debug', format: format.json() }))
```

A new `debug` transport that emits everything is a footgun — `debug` logs typically include request bodies, response payloads, and internal state. Combined with the patterns above, this can take a quiet leak and amplify it. Flag and ask whether `debug` is being enabled in prod.

### 10. Secrets in committed config files

```diff
+ const apiKey = 'sk_live_4eC39H...'   // in src/config.ts
```

Secret material in source. Even if `.gitignore` is updated in the same PR, the secret is in git history forever. Surface the leak and require rotation, not just removal.

## What this skill is NOT looking for

- **Schema-level constraints** (encryption at rest, key rotation, IAM scoping) — those are infra concerns better caught by SAST tools and architectural review, not per-PR.
- **Database column-level PII review** — also out of scope here; this skill scans the *code path* PII flows through, not the storage layer.
- **Internal sanitization helpers** — if the diff explicitly redacts (`maskEmail(email)`, `redactToken(token)`), trust the helper unless its implementation is obviously wrong.

## Finding-shape template

> [pii-and-compliance] **<class>**: `<file>:<line>`
>
> ```diff
> <the offending diff>
> ```
>
> **Why it leaks:** <which destination this lands in — logs, Sentry, analytics — and who can read that destination>
>
> **Fix:** <the structured-logging or redaction pattern that's already used elsewhere in the codebase, if known>

If the codebase has an existing redaction helper (`mask`, `redact`, `sanitize`), cite it. Authors are far more likely to adopt a fix that matches the codebase's existing pattern than to invent one.

## When this skill should be silent

- The PR doesn't touch logging, error handling, analytics, telemetry, URLs with credentials, or test fixtures.
- The PR is removing PII from those places (the opposite of what this skill catches).
- The "leak" is into a destination explicitly scoped to handle it: an encrypted-at-rest audit log, a redaction-aware logger that runs as a side effect of being called.

In any of those cases:

> [pii-and-compliance] n/a — no PII / auth-material flows in this diff.
