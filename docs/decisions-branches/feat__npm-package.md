← back to [docs/timeline.md](../timeline.md)

## 2026-08-24 14:53 - Publish agent-skills as the npm package thrill-skills, content-only

**Reasoning:** The vercel-labs skills CLI already bridges node_modules -> agent directories via experimental_sync (confirmed against a real published package's layout, dotenv, and end-to-end against our own tarball); shipping skills/ as an npm package turns a catalog update into a normal Dependabot version-bump PR for any repo with a package.json, with zero new infra and no duplicated tooling

**Alternatives considered:** A postinstall script that copies skills/ itself, Wait for the skdd steward's org-wide fan-out

**Implications:**
- Package version (0.1.0, independent, monotonic) is a separate number from each SKILL.md's own version/digest/origin frontmatter; it only advances when a maintainer bumps package.json and pushes a vX.Y.Z tag -- nothing here yet auto-tags a skills/ merge, so a real publish still needs a human to remember to cut one

---

