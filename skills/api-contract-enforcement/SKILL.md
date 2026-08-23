---
version: "1dd295d6a4e8"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
name: api-contract-enforcement
description: Flag PRs that change the shape, semantics, or error behavior of a public API without versioning, deprecation, or migration notes. Catches removed fields, renamed parameters, changed status codes, broken pagination, and silent enum drift. Apply when reviewing HTTP routes, gRPC services, GraphQL schemas, SDK exports, CLI flags, or any other interface a downstream consumer depends on.
applies_to:
  paths:
    - "api/**"
    - "src/api/**"
    - "lib/api/**"
    - "internal/api/**"
    - "**/routes/**"
    - "**/handlers/**"
    - "**/controllers/**"
    - "**/endpoints/**"
    - "**/resolvers/**"
    - "src/index.ts"
    - "src/index.js"
    - "src/__init__.py"
    - "openapi/**"
    - "schema/**"
    - "schemas/**"
  extensions: [".proto", ".graphql", ".graphqls", ".gql", ".thrift"]
---

# API contract enforcement

A public API is a promise. This skill reviews PRs for unannounced changes to that promise — the kind of edit that ships green CI in your repo but breaks every consumer the moment it lands.

## What counts as "public API" for this skill

In rough order of consequence:

1. **HTTP routes and request/response shapes** — REST endpoints, JSON-RPC methods, OpenAPI schemas.
2. **gRPC services and message definitions** — protobuf field numbers, deprecated tags, oneof variants.
3. **GraphQL schemas** — types, fields, arguments, directives, enum values.
4. **SDK exports** — anything a package's `index.ts` / `__init__.py` / package's main entry re-exports. Types AND runtime values.
5. **CLI flags, subcommands, and exit codes** — anything documented in `--help` or relied on by scripts.
6. **Database column names, view definitions, materialized views** — when the schema is consumed by readers outside the PR's own service.
7. **Event payload shapes** — Kafka topics, webhook bodies, queue messages.
8. **Configuration file schemas** — when a config file is read by code outside the PR's service.

What this skill is **not** for: internal helper functions, private classes, package-internal modules. Convention says those can change.

## Breaking-change patterns to flag

For each, the finding shape is: quote the diff, explain why it breaks consumers, propose the migration path (deprecate-then-remove, versioned endpoint, additive change, etc.).

### 1. Removed or renamed fields

```diff
- response.user_id
+ response.userId
```

This is a breaking change in two ways: removing `user_id` and adding `userId`. Old consumers reading `user_id` now get `undefined`. The fix is either an additive change (ship `userId` *alongside* `user_id`, deprecate the old field in docs, remove later) or a versioned endpoint (`/v2/users/...`).

### 2. Tightened input validation

```diff
- email: z.string()
+ email: z.string().email().max(254)
```

This rejects requests that previously succeeded. Even if the previously-accepted inputs were "wrong," consumers may be sending them today. Flag and ask whether existing data has been audited — if not, this needs a deprecation window with logged warnings.

### 3. Changed status codes or error shapes

```diff
- res.status(404).json({ error: 'Not found' })
+ res.status(410).json({ code: 'GONE', message: 'Not found' })
```

Three breakages: status code 404 → 410 (clients that switch on status), key `error` → `message` (clients that read it), new key `code` (clients with strict-shape validation may reject extra fields).

### 4. Reordered required fields or positional arguments

```diff
- function createUser(name: string, email: string, role: Role)
+ function createUser(email: string, name: string, role: Role)
```

Every caller now passes arguments in the wrong slots. Tests within the PR's own repo are updated; downstream consumers aren't.

### 5. Silently dropped enum values

```diff
  type Status = 'active' | 'paused' | 'archived'
- type Status = 'active' | 'paused' | 'archived'
+ type Status = 'active' | 'archived'
```

A consumer that holds a 'paused' value loses it on the next round-trip. Surface the migration: what happens to existing 'paused' records?

### 6. Changed pagination contract

```diff
- res.json({ items, total, page, pageSize })
+ res.json({ items, nextCursor })
```

Two paradigms — offset/limit vs cursor — can't coexist transparently for consumers. Either keep both response shapes during a transition window, or version the endpoint.

### 7. Stricter rate limits or auth scopes

A previously-permissive endpoint suddenly returning `429` or `403` to existing tokens is a breaking change even though the response *shape* is identical. Flag a missing changelog entry or migration warning.

### 8. Changed default behavior of optional parameters

```diff
- function get(opts = { includeDeleted: false })
+ function get(opts = { includeDeleted: true })
```

Existing callers who omit `opts.includeDeleted` now get different data. Make the change opt-in or feature-flag it.

### 9. Removed CLI flags or shortened forms

```diff
- program.option('-v, --verbose')
+ program.option('--verbose')
```

Scripts using `-v` break silently. Either leave the short form, or version the CLI.

### 10. Database column rename without view + dual-write

```diff
- CREATE TABLE users (id, user_name TEXT)
+ ALTER TABLE users RENAME COLUMN user_name TO name
```

Any reader still issuing `SELECT user_name FROM users` breaks at the moment of deploy. Migration pattern: add the new column, dual-write, deprecate readers of the old column, then drop.

## When this skill should be silent

- The PR doesn't touch any public API surface — pure internal refactor, test changes, build config.
- The change is purely additive — adding a new optional field, new endpoint, new CLI flag — with no removal or behavior change to existing surface.
- The breaking change is explicitly versioned (new endpoint path, new SDK major version, new gRPC service version) AND a migration path / deprecation window is documented in the PR.
- The change is in a clearly marked unstable / experimental / internal surface (`@experimental`, `@internal`, `/v0/`, `__private__`, etc.).

In any of those cases, post a single line and stop:

> [api-contract-enforcement] n/a — no public-API changes in this diff. *(or: change is additive / explicitly versioned)*

## Finding-shape template

> [api-contract-enforcement] **Breaking change without deprecation:** `<file>:<line>`
>
> ```diff
> <the offending diff>
> ```
>
> **Who breaks:** <which consumer pattern this breaks — e.g. "any client that reads `response.user_id`">
>
> **Migration path:**
> 1. <step 1 — usually: keep the old form too>
> 2. <step 2 — usually: deprecate the old form in docs>
> 3. <step 3 — usually: remove in a versioned/major release>

Specific > general. Quote the diff. Name the consumer pattern. Don't say "this might break clients" — name the broken access path.

## Checking your work

Before posting a finding, search the codebase (or the PR's commit history) for evidence the migration was already considered:

- Look for a CHANGELOG entry, migration guide, or `BREAKING:` prefix in the commit message.
- Look for a deprecated alias or fallback alongside the rename.
- Look for a version-bump commit (major SemVer, new endpoint path, new schema version).

If you find one, downgrade the finding to "verify migration plan is sufficient" rather than flagging it as missed. The author may have already done the work.
