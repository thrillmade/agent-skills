← back to [docs/timeline.md](../timeline.md)

## 2026-11-11 17:29 - The repository is thrill-skills: every live reference to the old name is updated

**Reasoning:** The catalog repository was renamed on GitHub from agent-skills to thrill-skills, the name its npm package already carries. The old address redirects for the web, git and raw files, so nothing broke, but the files still named the old address, and one of those names is functional: the weekly census requests a token for a list of repositories by name, and a name that no longer resolves stops the whole run. The name is owned by constants in the stamper and the generators, so those changed first and the stamps, the version index and the directory skill were regenerated.

**Alternatives considered:** Leave the files as they are and rely on redirects: rejected, the census token request does not follow redirects, and published install lines should show the real address, Rename docs/integrating-with-agent-skills.md too: rejected, other repositories link to that path and GitHub does not redirect file paths

**Implications:**
- 56 skills keep their digest and version, because the digest ignores the identity lines; nine skills name the repository in their text and are bumped
- Links to the skills.sh listing point at the GitHub repository until a listing exists under the new name
- The npm trusted publisher must be registered against thrillmade/thrill-skills
- Other repositories still name the old address; redirects cover them until each is updated

---

