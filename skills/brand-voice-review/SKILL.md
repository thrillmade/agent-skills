---
name: brand-voice-review
description: Review user-facing strings for brand-voice consistency. Catch dead phrases ("click here", "you should"), accidental shouting (exclamation marks, ALL CAPS), and jargon that leaks past the design team. Apply to button labels, error messages, marketing copy, headings — not to internal code identifiers or logs.
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

This skill applies to **user-facing strings**: button labels, headings, body copy, error messages, empty states, toast notifications, marketing copy, email subject lines. It does **not** apply to internal identifiers (variable names, class names, log messages, API field names, debug strings).

Your job is to catch microcopy that escaped the design team's review — the kinds of phrasings that read fine in isolation but, in aggregate, make the product sound like every other SaaS dashboard. Most projects don't have an explicit brand-voice guide; this skill is the default backstop until they do.

If the repository ships a brand-voice guide (e.g. `BRAND.md`, `docs/voice.md`, a `.brandvoice` config), defer to it. The rules below are the fallback when there's no project-specific guidance.

## What to scan for

### 1. Dead phrases (replace with what they actually mean)

**Bad:** "Click here to learn more."
**Good:** "Read the migration guide."

**Bad:** "You should configure your API key."
**Good:** "Set your API key in Settings → Secrets."

**Bad:** "Please try again later."
**Good:** "Retry in a minute." (or, if the cause is known: "Connection lost — reconnecting…")

"Click here" is dead because the link could be a button, a tap target, or a keyboard activation — the verb describes the user's hardware, not the user's intent. "You should" is dead because if it weren't required, the message wouldn't exist. "Please try again later" is dead because it tells the user nothing actionable. Replace with the specific verb and the specific next step.

### 2. Accidental shouting

Exclamation marks in product copy almost always read as forced enthusiasm. Reserve them for genuinely positive moments (a completed onboarding, a celebratory milestone) — never for errors, warnings, or routine confirmations.

**Bad:** "Saved!"
**Good:** "Saved."

**Bad:** "Oops! Something went wrong!"
**Good:** "Couldn't save your changes — check your connection and retry."

ALL CAPS in body copy reads as yelling. Use it only for established UI primitives (`USD`, `API`, `JSON`) and acronyms.

### 3. Empty hedging

**Bad:** "We're just doing a quick sync."
**Good:** "Syncing your library."

**Bad:** "Simply enter your email."
**Good:** "Enter your email."

The words **just**, **simply**, **easy**, **quick** add nothing and quietly insult readers who don't find the task quick or easy. Strip them.

### 4. Filler verbs

**Bad:** "Make sure to save your work."
**Good:** "Save your work."

**Bad:** "Go ahead and click Continue."
**Good:** "Click Continue." (or, per rule 1: "Continue.")

"Make sure", "go ahead", "feel free", "be sure to" are stage directions, not instructions. Cut them.

### 5. Title-case button labels

Most modern interfaces use sentence case for buttons and form labels. Title case (`Submit Your Changes`) reads as legalese; sentence case (`Submit your changes`) reads as a conversation.

If the project's existing buttons use sentence case, flag any new buttons that drift to title case. If the project's existing buttons use title case consistently, leave them alone — match the project's pattern.

**Bad** (drifts from a sentence-case project): "Edit Your Profile Settings"
**Good:** "Edit your profile settings"

### 6. Verb-first calls to action

Buttons and links should start with the verb that names the user's intent.

**Bad:** "Profile" (on a button that opens the profile editor)
**Good:** "Edit profile"

**Bad:** "Settings"
**Good:** "Open settings"

**Bad:** "Submit"
**Good:** "Send invitation" / "Save changes" / "Publish post" — name the *thing* the user is doing, not the form mechanic.

### 7. Pronoun consistency

Pick **we** (the product team speaking) or **you** (the user being addressed) and stay with it within a screen, dialog, or email. Drifting between the two within a single message is jarring.

**Bad** (drifts mid-sentence): "We need you to confirm before you can continue, and then we'll send you a code."
**Good:** "Confirm your phone number. You'll get a code by SMS."

### 8. Jargon and feature-team in-talk

Words that mean nothing outside the team's slack channels: *leverage, synergize, frictionless, seamless, robust, world-class, best-in-class, cutting-edge, enterprise-grade.* If you can replace the word with what it actually means and the sentence gets *more specific*, that's the brand-voice fix.

**Bad:** "Leverage our enterprise-grade authentication for frictionless onboarding."
**Good:** "Sign in with Google or GitHub — no password to manage."

## What NOT to flag

- **Internal identifiers**: variable names, class names, function names, API field names, log lines, debug output. Brand voice is for the user; engineers can name things whatever the code style guide says.
- **Tone of voice in technical docs**: documentation has its own register (precise, dense, evidence-anchored). Don't flag a technical doc for not being conversational.
- **Quoted user input**: if the code is rendering content the user wrote (commit messages, comment bodies, profile fields), brand voice doesn't apply — it's their text.
- **A/B test variants**: if you see a `experiment_copy_v2.tsx` file or a feature-flagged string, leave it alone — that's marketing intentionally testing voice variants.

## How to phrase findings

One concrete issue per comment. Quote the exact string. Suggest a specific replacement. Cite the file + line.

**Good finding shape:**

> [brand-voice-review] Dead phrase + accidental shouting in `app/onboarding/page.tsx:142`:
>
> ```
> Welcome aboard! Simply click here to get started!
> ```
>
> Suggested: `Start your tour.` (single verb-first imperative, no exclamation, no "simply", no "click here").

**Bad finding shape:**

> "This copy could be more on-brand."

Without a quoted string and a concrete replacement, the author has no way to act on the feedback.

## When this skill should be silent

If the diff doesn't touch any user-facing strings (the change is purely code-internal, infra, build config, dependency bumps, etc.), post a single line:

> [brand-voice-review] n/a — no user-facing strings in this diff.

Don't invent findings on irrelevant changes.
