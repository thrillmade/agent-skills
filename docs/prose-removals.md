# Prose removals

Declared deletions of content from a `SKILL.md`. The `check-prose-retention`
gate (`.github/scripts/check_prose_retention.py`) fails any change that takes
words out of a skill and puts nothing back, unless there is a row here.

Deleting prose is allowed and ordinary — skills get trimmed, superseded and
merged. Deleting it *silently* is what this stops. Three skills lost real
content to a link-conversion sweep that needed to fit under the 8192-byte size
gate, and every check went green, because deleting content is how they went
green.

## What the gate charges you for

Reformatting is free. Rewrapping a paragraph, reordering sections, moving a
line, bolding a phrase, converting `` `spacing-system` `` to a markdown link or
back, de-linking a reference that rotted, dropping a bare URL — all score zero.

Each part of the file is scored on its own, and a gain in one never pays for a
loss in another. Padding the `description:` does not buy the deletion of a body
section, and a sentence of filler does not buy the deletion of a worked code
example. Both of those were live evasions: the size cap only measures the body,
and fenced code costs two to three times as many bytes per word as prose, so
each was a way to free real bytes while netting a whole-file word count to zero.

A code example counts as one in either of markdown's spellings — fenced, or
indented four spaces past whatever list item it sits in. Reading only the fence
left that trade open through the other spelling, at *more* bytes per word rather
than fewer.

A block quote is not a third spelling. It is a **container**, and it hid both of
them: a `>` in front of a fenced or an indented example put that example back in
the prose scope, so the same trade went green through a marker — and, the worse
direction, wrapping an existing example in `> ` without touching a word was
charged as a removal whose only printed remedy was a row here declaring words
safe to lose that were never lost. Nothing in this file is ever the right place
for that. Quote depth is now part of a block's identity, at any nesting depth
and with or without the space after the marker.

The floors are measured, not chosen — each sits at the top of its own part's
noise in this repository's history, with the smallest real removal in that part
four times higher or more. `check_prose_retention.py` carries the distribution
and the command to re-measure it.

Splitting a file into its parts is what makes all of that work, so a `SKILL.md`
whose YAML frontmatter cannot be found gets **no verdict at all** rather than
one merged part — the gate says so and fails, the way it does when it cannot
work out what to compare against. Open with a `---` line and close the block
with another.

## How to add a row

Run the gate, or read the CI failure. Either prints the exact row:

```sh
python .github/scripts/check_prose_retention.py
```

With no `--base` it compares against the merge base with `dev`, falling back to
`main` if `dev` is not reachable. Every branch here forks from and targets
`dev`, so that is usually where CI's own merge-base comparison lands too — but
CI always computes its base from the PR's actual target, so if yours is
something else, pass `--base` explicitly rather than trust the default.
Comparing against the tip of a branch instead of its merge base charges yours
for whatever landed there since you forked.

Paste the row below and replace the placeholder with the reason. That is the
whole cost — and the placeholder is rejected unfilled, because deciding the
words are safe to lose is the one part of this that cannot be automated.

The failure is written about the ledger you actually have, so it does not always
hand you a row. Paste one and leave the placeholder in, and the next run asks
you to fill that in rather than reprinting the row you just added. Where this
file already carries a row covering your cut, it says why that row is not yours
to spend instead of offering you a second one to write underneath it.

Six rules make the row a declaration rather than a standing exemption:

- **Only a row your change adds counts.** A row that was already there is
  somebody else's declaration about somebody else's deletion. Inheriting it
  would make this file the blanket exemption the size gate deliberately
  removed. Editing one does not make it yours, and which column you edit — the
  reason, the number, even the skill name, even a column added to this table
  years from now — makes no difference: between two versions of a text file an
  edit is one row removed and one row added, and nothing says which added row
  is which removed one.
- **Nothing already here may be taken back out.** That is what makes the rule
  above true rather than merely intended. Your change is credited with what
  this file gained over what it already had, so a change that removes or
  rewrites anything in it is credited with nothing at all — including its own
  honest rows — until it puts that back. Adding a throwaway row does not buy
  the difference: the row that makes this file longer and the row that covers
  your cut have to be the same row.
- **A line the gate cannot read still takes up a line.** Every line of this
  file occupies a slot: a row by what it declares, and anything else — prose, a
  code block in either of markdown's spellings, a commented-out draft, a row
  that is missing a cell or whose count is not a number — by its own text. So a
  row parked somewhere unreadable and made readable by a later change declares
  nothing in that change: the line it vacated is a removal, and a removal
  credits you with nothing. Without this the rule above was an invariant over
  what *parses* rather than over this file, and every way of writing an
  unreadable row was somewhere to stage one.
- **The count must cover the cut.** It cannot be written blind, and it puts the
  size of the cut in the diff where a reviewer reads it. It is a floor, not an
  exact match: if a later commit in the same PR adds words back, the row you
  already wrote still stands. Understating still fails.
- **The reason must be filled in.** A row pasted straight from the failure,
  placeholder intact, declares nothing and does not count.
- **A second removal needs a second row**, even from the same skill at the same
  size. Rows are counted, not deduplicated.

Rows go in the table at the bottom of this file — the **first** such table in
it, and only that one, so an example elsewhere in the document declares nothing
and does not shadow the real table either. Code counts as an example in either
of markdown's spellings, fenced or indented four spaces, and so does a
commented-out draft. Reading the fence alone was not enough: an indented
example renders identically, its header was the first `| skill | words | why |`
in the document, and the table a reader would actually write into went dead
under it. The record is the point.

Putting an example inside a block quote changes nothing here, and that is
measured rather than assumed: a quoted line begins with `>` and never with a
pipe, so it was never a row or a header either way. The container reading moved
no slot in this file, and moved none in 40,000 generated ledgers built from
quoted rows, quoted fences and quoted indented rows — while the same 40,000 move
21,043 lines in and out of the code scope, which is what says the check looked.

Paste the row anywhere inside that table. A blank line before it is fine; the
table ends at the first line that is neither blank nor a table row, so prose
below it stays prose.

**Rows stay after they merge.** This is a record, not a queue, and the gate
fails on its own if a change takes a merged row back out — with no SKILL.md
involved and nothing else wrong. Correcting a row means adding a new one and
leaving the old one standing.

The gate is characterized against the three real deletions, vendored with their
provenance in
[tests/fixtures/prose-retention/PROVENANCE.md](../tests/fixtures/prose-retention/PROVENANCE.md).

| skill | words | why |
|---|---|---|
| empirical-design-principles | 6 | Its disclaimer said Norman's two gulfs "are in neither skill and are covered nowhere yet". `composing-a-screen` now covers them (#225), so the sentence had become false about its own catalog. Corrected rather than cut — the words went because the claim did, not to make room. |
| finding-a-catalog-skill | 12 | Generated, not authored. The directory publishes a "not here" section listing gaps the catalog does not cover, and its entry for the two gulfs was removed by `gen_skill_directory.py` because #225 filled that gap — the generator refuses to publish a "not here" claim that has become false. The removal is derived from `NOT_HERE_PROBES`; editing this file by hand is what the byte-identity gate forbids. |
| component-sizing-principles | 19 | Consumer audit #252 finding 4: this skill's own "WCAG 2.5.8 target-size floor" section fully restated the floor's value and reasoning that `spacing-system` already owns and cites — two skills asserting the same number is how one of them goes stale. Cut to a pointer at `spacing-system` in the body, `Verification` and `Sources`; the application-specific rung-placement guidance (which rung is reserved, where interactive rungs start) stays, since that half is this skill's own. |
| spacing-system | 55 | Consumer audit #252 finding 5: the border-radius ladder's formula table (`radius-sm = minor`, `radius-xl = 1.5 × major`, `radius-2xl = 2 × major`, ...) had no citation and prescribed a specific ratio as if it were universal, when radius personality — how many rungs, how fast they grow — is a design system's own call, not this skill's to dictate. Replaced with the two endpoints that are genuinely universal regardless of personality (`radius-pill`, `radius-circle`) and a pointer to `udts-spacing-defaults` for one system's worked ladder. |
| designing-elite-ui | 55 | The `## Deploying This Skill` section, addressed to the skill's AUTHOR rather than its reader ("test by retrieval + application… tighten any principle an agent reads but doesn't apply") and paid for on every load. Cut in the #252 restructure. **The gate did not demand this row** — it scores net words across three coarse scopes per file, so the five house sections added in the same change offset the deletion inside the same prose bucket. Logged anyway, because the same PR declared two other cuts and a policy applied only when a gate forces it is not a policy. |
| design-system-consistency | 26 | #256: buying room for rule 6's "filed once" dedup fix on the tightest file in the catalog (3 bytes headroom). The `Sources` section's own "House convention, not a standard" bullet was a compressed restatement of three things already stated in full in the body — `When NOT to use`'s "no system on disk, file one finding" bullet, `Establish the reference before judging` item 2's "filed once — not one finding per hue", and `Every mode needs a token path`'s "is there a path" test — under a heading it explicitly disclaimed belonging in ("not a standard"). Cut as genuine duplication, not trimmed to fit; nothing it said is now unstated elsewhere in the file. |
| token-frugal-tooling | 6 | #202: renaming `## Where to look for detail` to the house's `## Cross-references` (this file's genuine cross-reference list, just under a bespoke name) drops 4 words from the heading itself, and converting `` **`logmind` skill** `` / `` **`clud-bug-collaboration` skill** `` into real relative links (`[logmind](../logmind/SKILL.md)`) drops the now-redundant noun "skill" from each, once the link text already names the skill. No fact or instruction is lost — the two entries still say exactly what each sibling skill covers. |
| clud-bug-collaboration | 61 | House-structure gate: this file had 6 bytes of headroom under the 8192-byte cap and needed 4 new sections (`When to use`, `When NOT to use`, `Verification`, `Sources`), so every existing section was edited for redundancy before anything was added. What actually left rather than merely moved: the "Generic prose ('be careful with database code') gets ignored" framing sentence and its `lib/db/queries.ts` example path (the bad/good snippet right after it still carries the rule); the exact GitHub error string `"Workflow validation failed"` alongside the 401 it's paired with; the per-scope byte-budget preamble ("per run on diff / prior-comment / skill-content") and the `(above any realistic PR diff, below OOM)` aside; "not interactively" in the quiet-mode note; and, in the cost-control fast-paths bullet, the pinned model ID `claude-haiku-4-5-20251001`, the `classify emits model=$MODEL then exit 0` / `is_workflow_only` gating detail, and the quoted Anthropic rationale for Sonnet over Opus. No procedure, threshold or number a reader acts on was cut — the two check-status and check-secret sections were reorganised (one became `Verification`, near-zero net) rather than shortened. |
| orchestrating-agent-delegation | 34 | Local-sync merge of the CEO's October additions (UI is one `designer` lane on opus; verification isolated from file ownership; assign the tree in the brief; repo-global git commands banned), which arrived on a body with 51 bytes of headroom under the 8192-byte cap — so the existing prose was tightened to carry them. What actually left: two Failure-modes bullets that restated rules held elsewhere in the file ("agent reports clean without running the check" — Verification rule 1 and "Trust but verify"; "model wrong for the task" — the tiering table is the rule), the "no registry, no network call" gloss on role discovery, and clause-level trims in the effort/review-pass, stalled-agent, fix-agent and cross-repo-cwd passages. The brief skeleton's "if a classifier or permission blocks something" clause became "if blocked", which the Failure-modes bullet on off-brief agents still states in full. Review caught one rule the first pass dropped silently -- "check you touched the file before attributing a failure" -- restored in compressed form and paid for by cutting the redundant "Split UI drifts:" table-cell prefix (rule 3 states the split rule) and two clause tightenings. No rule is withdrawn in the final state. |
| orchestrating-elite-agent-qa | 60 | Local-sync merge of the CEO's October additions (one `designer` lane builds a UI surface; a branch is not an isolated working tree; a shared-checkout green is not evidence), which arrived on a body with 279 bytes of headroom under the 8192-byte cap, so existing prose was tightened to carry them. What left is clause-level only: "conflicting parallel edits are merge hell", the "visual-polish lens" aside in When NOT to use, "Drive the browser" in a Common Mistakes cell, the "(TDD for skills)" gloss and a clause naming the "verify done" rules in the deploy note, and wording in the Cross-references (`session-heartbeat` entry) and Copyable Prompt. Every gate, rule and cross-reference survives. |
| designing-elite-ui | 14 | Minor 1.1.0 (feat/design-skills-nov), checked word by word against origin/dev. Four principles (9–12), a content-led worked example, modes past light/dark and the panel's corrections arrived on a body with 151 bytes of headroom, so existing prose was tightened. What actually left: the "One hand draws the surface" section shrank to an intro clause (`orchestrating-elite-agent-qa` step 3 owns the rule) — gone are "on opus", "design and build", "each agent takes its own path", "mixed spacing, two accent logics, three button shapes"; the intro's "Encode it explicitly (a tokens file + a short design-system doc)… one source of truth" (the Encode section states it); principle 1's "Give each role a band", "it reads deliberate, not random" and its parenthetical example (worked example A states it); principle 2's "(a dark draw ramp, derived dark reds)" and "never reuse the light values on a dark surface" (the dark-mode gotcha keeps it); principle 3's "not a rainbow" and "solid"; "Retire decoration that doesn't carry meaning" (principle 9 restates it with a test); "Consistency over variety" (principle 10); principle 5's "one icon language" (principle 10) and, as a system's call rather than a universal, "Infinite/dotted background beats a white card on a page"; principle 6's "Cursor affordances (… on handles … on pan)" and "smooth transitions" (now `motion-continuity`); principle 7's "Light and dark are BOTH primary… neither is an afterthought" (replaced by every theme and mode is primary); principle 8's "Optical, not metric"; gotchas' "recompute after layout settles" and "washed/low-contrast"; Encode the Bar's "The bar only bites if it's written down where agents read it", "(a SPEC section / memory)", "in light + dark"; worked example A's "fully specified", "tokens and component primitives (button, input, table row, toolbar, panel) already on disk; nothing here is hand-rolled", the band hue paths (blue→purple→pink, green→orange), "neutral states near-grey", "(red must stay unambiguous)", the delete/error/failed list, "Reduced-color", "APCA-gate every metric label + status chip", "`text-box-trim` centering", "row density + px-per-unit on chart axes locked", "collapsible", "Lucide icons, per-section accent", "never splits it", "column-resize … header handles", "drag-reorder", "soft warning halos on cells needing attention, not hard error tiles" (kept compressed); Verification's "After building or critiquing a surface against this bar", "not one screenshot in one theme", "distinct from its neighbors" (kept as "distinct"); Cross-references' "applies this bar as a craft lens", "the stance it judges color drift against"; Sources' "so the two skills never disagree on what backs the claim". Every principle, gotcha and verification check that existed survives in substance. |
| orchestrating-elite-agent-qa | 105 | Minor 1.1.0 (feat/design-skills-nov), checked against origin/dev. Two rules (verify on the shipping engine and device; control-run every check both ways) and a Verification item arrived on a body with 14 bytes of headroom. What left: the `## Deploying This Skill (per writing-skills)` section, addressed to the skill's author rather than its reader — the same cut `designing-elite-ui` made in #252; three Common Mistakes rows restating rules stated in full in the same file ("Trust the ✓ completed status" = "Completed ≠ done"; "Parallelize slices on shared files" = "Sequence slices"; "Forget the SPEC/plan… stale docs rot fast" = pipeline step 8); and in the Copyable Prompt, "(not the dense seed, not exact-handle clicks)" (pipeline step 7 states it), "For each slice" → "Per slice", the four "Then"s, "(If non-trivial, first run…)" → "Non-trivial → first", "each a distinct lens" → "distinct lenses", "(cache-bust the JS, screenshot light + dark, exercise the states)" → "(cache-busted JS, light + dark, states exercised)". No gate, rule or cross-reference is withdrawn. |
| frontend-a11y | 8 | Back-link to `motion-continuity` (feat/design-skills-nov) on a body with 25 bytes of headroom, checked against origin/dev. "and screenshots are static so this lens never sees it" → "and static screenshots never show it"; dropped ", not what the ladder should have been" from the threshold bullet, whose "Cite them, never re-derive them" already carries the rule. |
| reviewing-design-work | 9 | Back-links for `thrill-design` and `motion-continuity`, the stale "4 dedicated design lenses" count corrected to 5, and lens 3's summary of `designing-elite-ui` updated (feat/design-skills-nov), on 56 bytes of headroom; checked against origin/dev. Left: the old summary "(…APCA-gated contrast, floating stable chrome, dark verified)" → "(…gated contrast, subtraction, on-grid sizes, every mode)"; "— this dispatcher adds nothing" after "Pure logic / backend review with no design surface"; "(the QA gate that drives the browser-driven rendered pass)" → "(rendered-pass gate)" (the lens order and What-fires-when sections state the browser-driven pass in full); "L1 sibling dispatchers" → "L1 siblings". |
| visual-polish | 7 | Back-link to `motion-continuity` from "Motion judged from stills" (feat/design-skills-nov), on 40 bytes of headroom; checked against origin/dev. Dropped "This lens applies a bar; it does not set one." — the same bullet's lead ("Deciding what the bar *is*" → designing-elite-ui) and the REQUIRED BACKGROUND entry both state it. |
| ios-safari-surfaces | 25 | PR #289 review fixes (feat/design-skills-nov), on a body at the 8192-byte cap. "`vh` is the UA's choice of one of the three; Safari resolves it to the large viewport [secondary]" was superseded spec text — CSS Values 4 §6.1.2.1 now defines the default units against the large viewport — so it became "`vh` is `lvh` by spec (§6.1.2.1)", and Sources' "the UA-defined `vh`" went with it. To make room for the theme-color hedge, Cross-references dropped "— an emulator is evidence about modules, not the product", which `orchestrating-elite-agent-qa` states as its own rule and this file's Testing section already applies. |
| motion-continuity | 14 | PR #289 review fixes (feat/design-skills-nov), on a body at the 8192-byte cap. Cut the intro's "Rules 1, 6, 7 and 8 rest on published sources; 2–5 are house convention (see Sources), each with the failure it prevents" — Sources' "House convention, not a standard: rules 2–5" line owns that split. Rule 6 and rule 8 now defer the property list and the reduced-motion prescription to `web-interface-guidelines-review` §9 instead of restating them ("for motion that travels it means … and `opacity`"; "replace movement with"); the Silent-failures "What rule 8 adds:" restatement was compressed into a pointer at rule 8. |
| reviewing-design-work | 15 | PR #289 review fixes and the owner's L2 ruling (feat/design-skills-nov). The **Rationale** paragraph restated the intro's own ordering reason (objective before subjective, cheap code read before browser-driving passes), which the intro still states; the clud-bug parenthetical lost "orthogonal" and "the elite-bar-last placement is this dispatcher's guidance", which stopped being true once the house stance became lens 4; System-specific layers' "the UDTS-specific rules a reviewer checks *on top of* this dispatcher" became "an L2 stance composes on top", covering both stances. |
| thrill-design | 14 | PR #289 review finding 7, one owner per fact (feat/design-skills-nov). Principle 5's *Holds when* restated `motion-continuity` Verification 1 ("a slowed capture shows one object throughout") and now points at it; principle 6's "Optical nudges live inside the footprint" and "footprint edges align to the margin" restated `designing-elite-ui` principle 8 and now point at it; the "Ink on the margin" silent failure keeps only its recognition cue (it shows only beside a neighbour); "Scale the check to the change" now names `designing-elite-ui` Verification as the rule's owner and keeps only the house lean. |
| orchestrating-elite-agent-qa | 4 | Follow-up to the #289 row above, which did not name this cut (#290). The delegation cross-reference lost its parenthetical "— briefs, model tiering, trust-but-verify —", a gloss on what the linked skill covers; the link itself and the sentence stating that this skill is the UI-quality-gate specialization survive, and the linked skill's own description owns the list. |
| visual-polish | 7 | Making room for the inline link in Verification 3 (#290) on a body at the 8192-byte cap. When NOT to use dropped ", and never gets filed as one" after "A polish nit never outranks a measured success-criterion failure" (Verification 4 states the ranking rule), and the Cross-references entry for the browser-pass skill now reads "producing this lens's states" in place of "producing the states and themes this lens needs" (the QA gate's step 6 owns which modes). |
| logmind | 156 | #267 shipped-release conformance: the skill taught behaviour that logmind v1.2.0, the latest tag, does not have. Each of these was probed against the v1.2.0 source and the installed v1.2.0 binary, with a control, and is absent: the `warp`, `show`, `search`, `context` and `headline` commands; `doctor --fix`; `LOGMIND_QUIET` and `--quiet` agent mode; `context.spec_file`; `LOGMIND_ALLOW_GIT_COMMIT`, `git.enforce_commits` and the PreToolUse hook; the main-only derived-docs rule with its `Derived docs were edited on this branch` gate; `docs/timeline-archive.md`; the "pulse" advisories; push after commit. Also removed: the "50 most recent" cap (default `max_recent` is 20 and nothing in `timeline` reads it) and the "since v0.2.7" version claim, neither verifiable. Rewritten to what v1.2.0 does: `log` commits without pushing, the `commit-msg` hook only warns, derived docs are regenerated with `logmind timeline --write` / `logmind file-structure --write` (the PR gate and merge conflicts both resolve that way), and the pre-commit `check-decisions` hook is named. The `doctor` installed-vs-latest/clud-bug claim and the "all local except push" claim were replaced with what v1.2.0 does. Nothing true of v1.2.0 was cut. |
| token-frugal-tooling | 101 | #267 shipped-release conformance, same pass as the logmind skill: logmind v1.2.0 (latest tag) has no `LOGMIND_QUIET` or `--quiet` (`logmind --quiet` errors `unknown flag`, control: `logmind timeline --help` works), no `--no-push` on `log`, and no `show` or `search` command (`unknown command`). Removed: the `LOGMIND_QUIET=1` table row and its example, the whole `Show + search` section, and the logmind half of the "agent mode" wording in the description and cross-reference. The `file-structure` and `timeline` rows verify in v1.2.0 and stay; every clud-bug claim is untouched. The Verification bullet's installed-vs-latest and clud-bug-probe claim is replaced: `doctor` in v1.2.0 has no clud-bug probe and its version line is unreliable. |
| designing-elite-ui | 201 | Batch-level flag raised by the dev→main promotion (#294), not by any single PR: #287 merged the owner's October rewrite of this skill (take-local) and #289 amended it, and in each PR more words arrived in the same part than left, so the per-PR gate correctly never fired; against main's August tip the batch nets a 201-word loss. Scattered tightening across the rewrite — the gate names no single passage. The bar's load-bearing rules survive restated on dev: APCA gating (4 mentions), the stable-canvas rule (3), optical alignment, both themes verified. Nothing main teaches is absent; it is said shorter. |
| orchestrating-elite-agent-qa | 111 | Same promotion-batch flag (#294), same cause: the October sync (#287) and the #289 amendment restated the pipeline tighter, with 353 words arriving in the same part per the gate. Refute-first reviewer prompting (4 mentions), the design-critic browser gate (6) and the merge-only-when-every-gate-passes rule survive in the rewritten text. The 4-word #290 row above covers a different, earlier cut; this row covers the batch net vs main. |
| spacing-system | 110 | Promotion-batch flag (#294): across #255/#257/#277 the radius-ramp example block was compacted (55 of the 110 are code words from that block) and the curated-sizes and scope prose tightened, masked per-PR by 105 arriving words. The curated icon-friendly set, the radius ramp and the component-sizing cross-reference survive on dev (radius 4 mentions, curated 4). |
| line-height-grid | 30 | Promotion-batch flag (#294): #255/#257/#277 tightened the 1.20/1.50 rationale bullets and the cross-reference list. Both ratios survive with their reasoning (7 mentions each) and the skill still routes to type-scale and spacing-system. |
| visual-polish | 14 | Promotion-batch flag (#294): #289 dropped the Sources entry for CSS Inline Layout 3 / MDN `text-box` while keeping what it supported — `text-box-trim` is still taught (2 mentions) and the Sources section keeps 6 live links. The 7-word #290 row above is a different cut; this covers the batch net vs main. |
