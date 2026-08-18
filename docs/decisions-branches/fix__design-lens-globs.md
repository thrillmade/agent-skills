← back to [docs/timeline.md](../timeline.md)

## 2026-08-18 04:53 - Converge designing-elite-ui's applies_to globs with the other three design lenses

**Reasoning:** designing-elite-ui was the last of four design lenses still on the old narrow glob set (site/**, app/**, **/components/**, **/ui/**; tsx/jsx/css/scss/vue/svelte), missing the nested-app and content-file coverage the other three (frontend-a11y, design-system-consistency, visual-polish) already converged on, so it silently missed a monorepo's nested app/** and astro/html files

**Alternatives considered:** leave designing-elite-ui on its own narrower pattern — rejected, it's an unexplained fifth dialect among four lenses meant to fire together on the same rendered surface

**Implications:**
- designing-elite-ui now matches the shared pattern: paths site/**, app/**, **/site/**, **/app/**, **/components/**, **/ui/**, **/styles/**; extensions tsx/jsx/vue/svelte/astro/html/css/scss — no test currently guards cross-lens glob convergence, so a future edit to one lens can drift again silently

---

