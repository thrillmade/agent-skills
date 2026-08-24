---
version: "1.0.0"
digest: "ea1de66ab57a"  # is your copy current? github.com/thrillmade/agent-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/agent-skills"
name: skillforge
description: |
  SUPERSEDED — skill authoring is now split three ways, and this skill duplicates all three without matching any of them: `skill-creator` (Anthropic plugin) owns measurement, since it carries the only executable eval harness in the set — trigger-rate testing on a held-out split, with-skill vs baseline runs, benchmark aggregation; `superpowers:writing-skills` owns wording form, including the match-the-form-to-the-failure model; and the studio's `skill-smith` agent owns house rules — catalog conformity, the frontmatter contract, upstream-PR discipline. Kept unchanged during the migration window; new work should load the successors. Its own conventions do not fit this catalog: the `.skills/<name>/` layout matches neither `.claude/skills/` nor `skills/`, its `.skills-registry.json` and `skdd forge` tooling are not wired here, and its "under 200 lines" is a third size rule alongside Anthropic's 500 lines and this catalog's CI-enforced byte budget. Use when you need the historical text; otherwise load a successor.

metadata:
  author: zakelfassi
  version: "2.0"
  spec: agentskills.io
---

# SkillForge

Create well-formed, spec-compliant skills from observed patterns.

## When to Forge

✅ **Forge when:**
- You've done the same sequence 2-3 times in a session
- A project convention isn't documented anywhere
- You solved a hard problem with a reusable solution
- Someone asks you to create a skill

❌ **Don't forge when:**
- It's a one-time task
- An existing skill already covers it (update instead)
- The "skill" is just a single command (use a script alias)

## Steps

### 1. Name the pattern
- What problem does this skill solve?
- What triggers it? (be specific — the `description` field is the discovery surface)
- What are the inputs and outputs?

### 2. Choose a name
- `kebab-case`, 1-64 characters
- Verb-led when possible: `deploy-preview`, `scaffold-component`, `triage-bug`
- One responsibility per skill

### 3. Create the skill directory

```bash
mkdir -p .skills/<skill-name>
```

### 4. Write SKILL.md

Use this skeleton:

```markdown
---
name: <skill-name>
description: <what it does>. Use when <triggers>.
metadata:
  forged-by: <agent-id>
  forged-from: <session-or-context>
  forged-reason: "<why this was created>"
---

# <Skill Name>

## Inputs
- ...

## Steps
1. ...
2. ...

## Conventions
- Project-specific patterns that apply

## Edge Cases
- Known gotchas or special handling
```

### 5. Add scripts (optional)
If the skill involves file generation or automation:

```
.skills/<skill-name>/
├── SKILL.md
├── scripts/
│   └── run.sh         # Executable automation
└── references/
    └── conventions.md # Detailed reference (keeps SKILL.md lean)
```

### 6. Register the skill
Update `.skills-registry.md` at the **project root** (same level as `.skills/`). Create it if it doesn't exist:

```markdown
| <skill-name> | local | <today> | 1 | <description> |
```

If the project uses the machine-readable registry (`.skills-registry.json`), update it too — `skdd forge` handles both formats automatically.

## Updating an Existing Skill

When you use a skill and encounter something it doesn't cover:

1. Add the new edge case or step to the existing SKILL.md
2. If the skill is getting too long (>200 lines), split it
3. Update `last-used` and increment `usage-count` in the registry

## Quality Checklist

Before committing a new skill:

- [ ] `name` is kebab-case, ≤64 chars
- [ ] `description` includes what it does AND when to use it
- [ ] Steps are numbered and actionable
- [ ] No hardcoded paths, secrets, or environment-specific values
- [ ] SKILL.md is under 200 lines (move details to `references/`)
- [ ] Registered in `.skills-registry.md`
