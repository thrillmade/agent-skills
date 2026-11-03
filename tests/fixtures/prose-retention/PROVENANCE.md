# Where these fixtures came from

Real files from the real defect, not hand-written approximations. `before.md`
and `after.md` in each directory are byte-for-byte the two sides of the #197
link-conversion sweep:

| side | commit | what it is |
|---|---|---|
| `before.md` | `8b4e1c8` | last commit before the sweep (on `main`) |
| `after.md` | `42f881c` | the sweep itself |

Re-derive any of them with:

```sh
git show 8b4e1c8:skills/<name>/SKILL.md   # before
git show 42f881c:skills/<name>/SKILL.md   # after
```

They are vendored rather than read from git at test time on purpose. `42f881c`
lives on a topic branch; once that branch is deleted the commit becomes
unreachable and the tests would break permanently, taking the only evidence the
gate works with them. Vendoring also keeps the suite hermetic — no
`fetch-depth: 0` requirement on the test job.

## The five skills

Three lost prose to buy size-gate headroom. They are the cases the gate exists
for, and the suite asserts it fires on each:

- **web-interface-guidelines-review** — lost Verification rule 5, which
  required a review's findings to cite the skills they rest on. The sharpest
  case: a conversion whose purpose was strengthening cross-skill routing
  deleted a cross-skill routing statement to fit.
- **clud-bug-collaboration** — lost its entire `CLUD_BUG_QUIET=1` agent
  invocation section.
- **session-heartbeat** — lost the two lines establishing that it is the
  *mechanism* and unattended-operation the *policy* layered on it.

Two are controls. They took the same conversion, heavily — 50 and 52 changed
lines — and lost nothing. The suite asserts the gate stays silent on both:

- **reviewing-design-work**
- **designing-a-design-system**

Without the controls, a detector that simply flagged every touched file would
pass the three positive tests. They are what makes those three mean something.

## The sixth: `designing-elite-ui`, the churn founding case

Not from #197. `before.md`/`after.md` here are `602bb6c`/`8896dcc` --
designing-elite-ui's #257 restructure (issue #258): it cut the author-addressed
`## Deploying This Skill` section (55 words) in the same change that added the
house's five standard sections. Net-per-scope scored a GAIN, not a loss --
`over` cannot see it by construction -- and the gate exited 0 on a real,
undisclosed cut. Both commits are ordinary history on `dev`/`main`, not a topic
branch, but vendored on the same terms as the other five: hermetic, and
immune to a future rebase moving what these two hashes mean.

```sh
git show 602bb6c:skills/designing-elite-ui/SKILL.md   # before
git show 8896dcc:skills/designing-elite-ui/SKILL.md   # after
```
