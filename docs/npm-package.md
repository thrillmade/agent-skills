# Consuming agent-skills as an npm dependency

Every posture in [integrating-with-agent-skills.md](integrating-with-agent-skills.md) — Subscribed, Published, Local — needs something to *notice* a catalog change: a weekly cron, the steward's future watcher, or a human running `npx skills update` by hand. `thrill-skills` on npm gives a fourth option that needs none of that built: **Dependabot**, which every `package.json`-carrying repo already has wired to open a PR on a version bump, gated by whatever review your reporulez ruleset already requires.

## What it ships

`thrill-skills` carries exactly `skills/` — the same `skills/<slug>/SKILL.md` tree this repo publishes — plus `LICENSE` and `README.md`. No `bin`, no build step, no dependency of its own; measured with `npm pack --dry-run`. It exists so the [`skills` CLI's](https://github.com/vercel-labs/skills) `experimental_sync` command, which already scans `node_modules/*/skills/*/SKILL.md` (confirmed against a real published package — `dotenv` ships the identical shape), has something to find.

## Consume it

```bash
npm install --save-dev thrill-skills
npx skills experimental_sync
```

`experimental_sync` walks `node_modules`, finds every `skills/<slug>/SKILL.md` it can reach (`thrill-skills`' and any other package shaped the same way), and installs each into the agent directories it detects. Re-run it whenever `thrill-skills` bumps — after `npm install` in CI, or by hand — the same way you'd re-run any other generated-artifact step after a dependency update.

## What the version number means

[SKILL.md frontmatter already carries per-skill semver](integrating-with-agent-skills.md) (`version:`, `digest:`, `origin:`) — that stays the source of truth for "is this one skill current." The npm package version is a separate, independent number: it tracks *publishes of the tarball*, not any single skill's content, and it is monotonic — it only goes up. It moves by hand, the same way [clud-bug's own package version](https://github.com/thrillmade/clud-bug/blob/main/package.json) does: a maintainer bumps `package.json`, tags `vX.Y.Z`, and [`.github/workflows/npm-publish.yml`](../.github/workflows/npm-publish.yml) publishes that tag. A minor bump is the routine case (skills added or edited since the last release); a major bump means the shipped shape changed in a way a consumer would notice on install — a skill removed from the tarball, or the `files:` list scoped differently. Nothing here is a code API, so "breaking" means "the tarball's contents changed," not a function signature.

## What's deliberately not in the tarball

Not [`docs/skill-versions.json`](skill-versions.json): that index answers "is my copy of this file, obtained some other way, stale" — a question that doesn't apply to a copy that arrived by `npm install` plus a Dependabot bump, since by construction that copy is whatever the package published. Its own `_readme` field talks about `main`-branch CI recomputing `current` on every pull request, a claim about *this* git repo that has no meaning divorced from it. Not [`docs/placement-map.json`](placement-map.json), not `.github/`, not `tests/` — none of it is content an agent runtime loads.
