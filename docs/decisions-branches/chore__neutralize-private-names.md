← back to [docs/timeline.md](../timeline.md)

## 2026-11-03 23:01 - Neutralize private repo names in the public tree and drop departed private subscribers from placement-map.json

**Reasoning:** The repo is public; private repo names (two private consumer repos and a private studio repo) appeared in scripts, tests, docs and decision logs, and placement-map.json declared departed private repos as subscribers the census cannot see. Owner ruling 2026-11-04: neutralize and eliminate. CEO wording killed in the same pass (owner ruling: kill if lightweight).

**Alternatives considered:** Leave decision-log archives untouched and only fix live docs: rejected — the archives are public bytes too, and the facts survive with the names neutralized. Rewrite git history to purge the names entirely: not attempted — a public-repo force-push is heavyweight and the owner has not ruled on it; flagged instead.

**Implications:**
- One deliberate leftover: feat__house-structure-gate.md:20 keeps 'CEO' inside a quotation that records a fabricated citation — editing the quote interior would falsify the record of what was invented. docs/timeline.md still carries two CEO titles; it is derived and main-only, so regen-on-main clears them after promotion. Git history still contains the private names; purging it is a separate owner decision.

---

