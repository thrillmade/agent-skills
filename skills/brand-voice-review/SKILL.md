---
version: "1.0.2"
digest: "682367fb898d"  # is your copy current? github.com/thrillmade/thrill-skills/blob/main/docs/skill-versions.json
origin: "https://github.com/thrillmade/thrill-skills"
name: brand-voice-review
description: SUPERSEDED — split three ways, one owner per rule. Interface wording (dead phrases, "click here", "just"/"simply", filler verbs, title-case drift, verb-first calls to action) is writing-interface-copy; voice and tone (accidental shouting, ALL CAPS, we/you drift, deferring to a project's own voice guide) is defining-a-voice; buzzwords and marketing copy are writing-marketing-copy. Kept as a pointer, with its applies_to trigger, so a subscriber that loads it is routed to the successors. Load those, not this.
applies_to:
  paths:
    - "src/ui/**"
    - "src/components/**"
    - "lib/ui/**"
    - "lib/components/**"
    - "components/**"
    - "app/**"
    - "pages/**"
    - "marketing/**"
    - "docs/**"
    - "README.md"
    - "**/copy/**"
    - "**/microcopy/**"
    - "**/strings/**"
    - "**/i18n/**"
    - "**/locales/**"
  extensions: [".tsx", ".jsx", ".vue", ".svelte", ".html", ".md", ".mdx", ".pug", ".hbs", ".liquid"]
---

# Brand voice review

**Superseded.** Load the three skills below instead. Each rule that lived here moved to one owner:

| Was here | Now |
|---|---|
| §1 dead phrases, §3 empty hedging, §4 filler verbs, §5 title-case drift, §6 verb-first calls to action | [writing-interface-copy](../writing-interface-copy/SKILL.md) rules 7–10 |
| What not to flag; how to phrase a finding; staying silent when no string changed | [writing-interface-copy](../writing-interface-copy/SKILL.md), When NOT to use and Reviewing copy |
| §2 accidental shouting, §7 pronoun consistency, deferring to the project's own voice guide | [defining-a-voice](../defining-a-voice/SKILL.md) |
| §8 jargon and buzzwords | [writing-marketing-copy](../writing-marketing-copy/SKILL.md), and the avoid list a voice guide keeps ([defining-a-voice](../defining-a-voice/SKILL.md)) |

The precedence between them — the brand's guide sets tone, the clarity rules hold regardless — is stated once, in [defining-a-voice](../defining-a-voice/SKILL.md).

**Migrating a subscriber.** `npx skills update` refreshes installed skills and never adds one, so add the three successors *before* updating this one; updating first leaves a pointer to skills the repo does not have. A pinned older copy keeps working until then.
