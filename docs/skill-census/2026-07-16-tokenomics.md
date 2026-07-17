# Skill census — thrillmade/tokenomics — 2026-07-16

## §1 Inventory

| Skill | Description (frontmatter) | Posture | Provenance | Manifest | Locally modified? |
|---|---|---|---|---|---|
| `brand-voice-review` | Review user-facing strings for brand-voice consistency; catch dead phrases, shouting, jargon | Subscribed (`.agents/skills/`, symlinked into `.claude/skills/`) | agent-skills | `skills-lock.json` (hash-pinned) | Not verifiable offline (hash pin present; no local edits this session) |
| `logmind` | MUST load for logmind projects; log decisions before writing >20 lines | Subscribed (same symlink pattern) | agent-skills | `skills-lock.json` (hash-pinned) | Not verifiable offline; no local edits this session |
| `clud-bug-collaboration` | Working in a clud-bug-installed repo — fix-push flow, strict-mode mechanics | Subscribed (baseline) | clud-bug v0.7.0-rc.20 | `.clud-bug.json` | No (baselines overwritten on `clud-bug update`; none made) |
| `critical-issues-only` | PR review discipline — correctness/security/perf only, skip nits | Subscribed (baseline) | clud-bug | `.clud-bug.json` | No |
| `evidence-based-review` | Every review claim must quote the code criticized | Subscribed (baseline) | clud-bug | `.clud-bug.json` | No |
| `respect-existing-conventions` | Don't fight the codebase's established patterns | Subscribed (baseline) | clud-bug | `.clud-bug.json` | No |
| `orchestrating-elite-agent-qa` | Multi-agent build/review/merge orchestration at a high quality bar | Published-upstream (nomination in flight per census intro) | **authored-here** | **NONE — UNTRACKED** (in neither manifest) | n/a (this repo is the source) |

## §2 Writer classification

- `orchestrating-elite-agent-qa` — **promotion-candidate** (already being promoted): distills the build → 3-lens adversarial review → fix → design-critic browser-gate → fresh-QA pipeline that has gated ~30 slices here. One caveat its own frontmatter admits: **never pressure-tested per `writing-skills` TDD** — the editor should demand a baseline-scenario test before catalog acceptance.
- No other authored-here skills exist yet. The `udts-*` L2 series (udts-token-model, udts-state-recipes, udts-linter-rules, udts-naming-convention, udts-dtcg-extensions, udts-review) is **planned but deliberately unwritten** — see §5, they'd be stale on arrival.

## §3 Usage evidence

- **clud-bug baselines (all 4)**: fire on EVERY commit via the PostToolUse hook — 10+ local reviews in the current session alone; findings led to real fixes (parseFloat hue truncation, selected-chip dark-mode contrast, seed-gate regression). Alive and load-bearing.
- **orchestrating-elite-agent-qa**: applied continuously — the G8 three-reviewer panel, every build-agent → verify → commit cycle this month followed its pipeline.
- **clud-bug-collaboration**: consulted for strict-mode/hook semantics; moderate use.
- **logmind**: skill loads, but the logmind CLI is **in repairs** (CDO-approved raw-git interim since ~2026-07-14) — workflow suspended, decision entries currently ride in long-form commit messages. Not the skill's fault; keep.
- **brand-voice-review**: **never fired** in this session's window. Plausibly fires during docs-prose slices; keep but low-signal.

## §4 Gaps

1. **`udts-review` (planned as K2f)** — clud-bug lens for UDTS rules: R7 band-floor, R8 state-delta, R9 coverage, R10 craft-guardrails, dogfood discipline. The G8 panel and G21 audit **manually re-derived** these checks from docs each time.
2. **Dogfood-discipline skill** — "zero raw hex/rgba/oklch in preview source outside documented exceptions (checkerboard, rainbow gradient, relative-color shadows)" has been re-derived at least 3× (G6, G21, G8-R3), whitelist included. Portable to any UDTS-consuming repo.
3. **Playground/live-rebuild architecture knowledge** — stable-alias mechanism (G12), split-CSS Sheet A/B, cross-frame palette cache: every new build agent gets this re-explained in prompts. A repo-local skill would cut prompt size.
4. **Classifier-outage operating mode** — commands via user `!` with SHORT lines (line-wrap once split an `--out` arg into a phantom command); prep-with-Write-then-handoff. Tribal, bit us twice.

## §5 Conflicts + constraints

- **Phase R (tier-model rewrite) in flight** on `feat/udts-color-polarity` (PR #92 stays open; keep-rolling locked). It rewrites `docs/foundations/color.md`, the registry SSOT, and the naming convention (`<palette-slug>-<role>`, spec 2.0 clean break). **Any `udts-*` skill drafted now encodes the OLD model — hold K2 incubation ~1-2 weeks until R lands.**
- **Deprecated slug refs found**: `design-token-naming` in `docs/integrations/claude-design.md`, `docs/implementation/07-config-format.md`, `docs/skills/inventory.md`; `component-sizing` in the latter two. Also both appear in `docs/decisions-branches/*` — those are historical logs, don't rewrite; the three living docs should re-point after the split ships.
- `docs/skills/` (inventory.md, creation-process.md) is prose ABOUT skills, not skills — will need a refresh pass post-reorg.
- Strict mode is ON (`.clud-bug.json`); refresh PRs touching baseline skills take effect from base ref only.

## §6 Sync readiness

- **Yes to weekly refresh PRs** — the repo already runs this exact rhythm (`clud-bug-self-update.yml`, `logmind-self-update.yml` Monday crons); `skills-lock.json` hash-pinning is live.
- **Breakage watch**: `.claude/skills/{brand-voice-review,logmind}` are **symlinks** into `.agents/skills/` — a refresh that materializes files over symlinks (or vice versa) would double-install; refresh tooling should preserve link topology. Baseline skills are overwritten by `clud-bug update` by design — never locally edit them.
- **Would subscribe** (don't today): the 4 design-critic skills (`designing-elite-ui`, `design-system-consistency`, `frontend-a11y`, `visual-polish` — K4 `--with-design` is a queued task here), `orchestrating-elite-agent-qa` (flip from authored-here to subscribed once accepted, and **add it to a manifest either way** — currently untracked), and L0 `oklch-color-space` + `apca-contrast` for build-agent grounding.
