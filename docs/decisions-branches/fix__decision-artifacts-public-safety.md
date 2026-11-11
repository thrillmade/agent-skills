← back to [docs/timeline.md](../timeline.md)

## 2026-11-11 14:30 - making-decision-artifacts carries the method, not the case: private pointers and verbatim quotes removed, review findings fixed

**Reasoning:** The skill reached dev with pointers into private material: a private repository's name, links to private issue comments, internal paths, dated incidents with counts, and verbatim quotations. A public skill carries the method, never the case, so the body and its sources file now name the kind of source behind each rule (a house ruling, an incident described in general terms, or a public specification) and nothing that identifies where it came from. An independent five-lens review also confirmed defects that are fixed in the same pass: an undefined term, a checklist box that could not be true before publishing, a conflict with thrill-design's principle 9, and one limit stated two ways.

**Alternatives considered:** Move the skill to a private catalog: rejected, the method is generic once the case is removed, Scrub only the body and leave the sources file: rejected, the sources file is published with the skill

**Implications:**
- references/sources.md names the kind of source behind each rule, not the source itself
- The earlier text remains in git history; removing it needs a history rewrite, which is a separate decision
- The frontmatter description still describes the moves page as rows printed by one grammar; it should be brought in line with the body in a later change

---

