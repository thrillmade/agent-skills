# Sources: writing-interface-copy

Why [writing-interface-copy](../SKILL.md) holds what it holds: the research trail for maintainers. The skill states each rule as the catalog's own opinion and quotes nobody; this file records which guides informed which rule, verbatim, so a rule can be re-checked against its page. All were read in November 2026. Rule numbers refer to the skill. The before/after examples in the skill are written for it; where one was adapted from a guide's own example, the guide is named below. Supplementary reading, which no rule depends on: [further-reading.md](further-reading.md).

## Where the guides disagreed, and the ruling the skill states

- **"Please" (rule 8).** Microsoft allows it "in situations where the customer is asked to do something inconvenient or the application or site is to blame"; GOV.UK's Design System avoids it "because it implies a choice", and its Service Manual says "There’s usually no need to say ‘please’ or ‘please note’"; Atlassian avoids it. Ruling: Microsoft's two cases only.
- **"We" in errors (rule 10).** Apple avoids "we"; Atlassian says "Use we instead of you"; Polaris allows it "unless Shopify caused the problem". Ruling: "we" only when the product failed; the thing is the subject, never the person.
- **Blame words (rule 10).** GOV.UK's Service Manual says "Say ‘Wrong password’"; its Design System avoids "‘valid’ and ‘invalid’"; NN/g avoids "invalid, illegal, or incorrect". Ruling: the words go; a short inline statement of the fact on its field stays.
- **"You"/"your" in labels (rule 2).** Apple: "“Favorites” conveys the same message as “Your Favorites”"; Material prefers second person. Ruling: no possessive on a noun label; actions and sentences may say "your".
- **Navigation labels (rule 9).** Apple: "When labeling buttons and links, it’s almost always best to use a verb"; Polaris: verbs like "View" or "Go" are "often unnecessary". Ruling: a data-changing control leads with its verb; a navigating one may name its destination.

- **Parallel form beyond lists (rules 11 and 3).** Microsoft and Google state parallel structure for the items of a list, Google with "if possible". Ruling: the same holds for any strings that share a role on screen (tabs, a row's second line, a tag set), and a role's tags are all states or all things. Building a role's strings in one function is the skill's own advice and sits outside the rule's test.

- **Terms of art (rule 4).** Heuristic 2's own test is "familiar to the user", so a term the domain's users already use ("Action items" in a meeting tool) is their word, not internal jargon. The skill's ruling, derived from that line.

## Rules moved here from brand-voice-review (#301)

brand-voice-review carried these as catalog opinion without a cited source. They now live in rules 7, 8, 9 and 10, checked against these pages:

- GitHub Primer, [Content](https://primer.style/foundations/content): rule 8 ("Do not say that something is “easy”, “quick”, or that the user “just” needs to do something"; "Do not use “here” or “click here” in calls to action").
- Microsoft, [Use simple words, concise sentences](https://learn.microsoft.com/en-us/style-guide/word-choice/use-simple-words-concise-sentences): rule 8's stage directions ("avoid weak or vague verbs, such as *be, have, make,* and *do*"; "Don’t use two or three words when one will do"; "Omit unnecessary adverbs", listing "quickly" and "easily").
- GOV.UK Service Manual, [Writing for user interfaces](https://www.gov.uk/service-manual/design/writing-for-user-interfaces): rule 8 ("Space is at a premium with user interfaces. So put the important words first and drop any unnecessary words").
- GOV.UK, [Technical content A to Z](https://www.gov.uk/guidance/style-guide/technical-content-a-to-z), "conditions": rule 8's hedges ("Do not use: - it may be possible to - use ‘you can’ - you may want to - use ‘you can’ - where possible you - use ‘where you can’"). The same entry keeps "‘you should’ for a recommendation" in technical content; in interface copy the skill rules it a stage direction, as brand-voice-review did.
- GitHub Primer, [Content](https://primer.style/foundations/content): rule 9's emoji ban ("Do not use emoji in UI content, or to replace words"). The screen-reader reason is the skill's own.
- Microsoft, [Top 10 tips for Microsoft style and voice](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice): rule 7's case style ("Default to sentence-style capitalization… Don't use title-style capitalization (Like This)"). The skill follows a project's consistent title case rather than overriding it, as brand-voice-review §5 did.
- Rule 10's "Please try again later": the skill's own ruling, from the GOV.UK Design System's "Describe what has happened and tell them how to fix it" (below) — a retry with no time or cause tells the user neither.

## Pages behind each rule

### GOV.UK

- Service Manual, [Writing for user interfaces](https://www.gov.uk/service-manual/design/writing-for-user-interfaces): rule 1 ("If you find yourself having to explain how the user interface works, that’s a sign something has gone wrong"); rule 10 ("Say ‘Wrong password’").
- Service Manual, [Naming your service](https://www.gov.uk/service-manual/design/naming-your-service): rule 4 ("describe a task, not a technology"); the skill's row-4 example follows its "fee remission" → "Get help with court fees" pattern.
- [A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), "Words to avoid": rule 8 ("in order to, usually not needed - do not use it").
- Design System, [Error message](https://design-system.service.gov.uk/components/error-message/): rule 8 ("'please' because it implies a choice"); rule 10 ("Describe what has happened and tell them how to fix it"; avoid "'valid' and 'invalid'").
- Design System, [File upload](https://design-system.service.gov.uk/components/file-upload/): rule 10 ("The selected file must be a …").

### Microsoft Writing Style Guide

- [Top 10 tips for Microsoft style and voice](https://learn.microsoft.com/en-us/style-guide/top-10-tips-style-voice): rule 1 ("Edit out *you can* when it isn't necessary").
- [Verbs](https://learn.microsoft.com/en-us/style-guide/grammar/verbs): rule 6 ("Keep it active whenever you can"; passive for "Avoiding condescending text or blaming the customer").
- [Use simple words, concise sentences](https://learn.microsoft.com/en-us/style-guide/word-choice/use-simple-words-concise-sentences): rule 8 ("Omit unnecessary adverbs—words that describe how, when, or where. Unless they're important to the meaning of a statement, leave them out." — hence "Renew automatically" stays; "use", not "utilize").
- [Lists](https://learn.microsoft.com/en-us/style-guide/scannable-content/lists): rule 11 ("Make all the items in a list consistent in structure. For example, each item should be a noun or a phrase that starts with a verb."). Advisory; its "In UI" section treats radio buttons and checkboxes as lists.
- [please](https://learn.microsoft.com/en-us/style-guide/a-z-word-list-term-collections/p/please): rule 8 ("in situations where the customer is asked to do something inconvenient or the application or site is to blame").

### Apple Human Interface Guidelines

- [Writing](https://developer.apple.com/design/human-interface-guidelines/writing): rule 2 ("“Favorites” conveys the same message as “Your Favorites”"); rule 5 (hint text such as "name@example.com"); rule 9 ("When labeling buttons and links, it’s almost always best to use a verb"); rule 10 (avoid "we").
- [Alerts](https://developer.apple.com/design/human-interface-guidelines/alerts): rule 9 (avoid OK "unless the alert is purely informational"; "Delete" over "OK").

### Nielsen Norman Group

- Nielsen, [10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/): rule 4 (h2, "Use words, phrases, and concepts familiar to the user, rather than internal jargon"); rule 7 (h4, "Users should not have to wonder whether different words, situations, or actions mean the same thing").
- Neusesser & Sunwall, [Error-Message Guidelines](https://www.nngroup.com/articles/error-message-guidelines/) (2023): rule 10 (avoid "invalid, illegal, or incorrect").
- Sherwin, [Placeholders in Form Fields Are Harmful](https://www.nngroup.com/articles/form-design-placeholders/) (2014): rule 5.
- Sherwin, ["Learn More" Links: You Can Do Better](https://www.nngroup.com/articles/learn-more-links/) (2015): rule 8 ("The phrase ‘Learn More’ is increasingly used as a crutch for link labels"; "The phrase is most dangerous when used alone because of its ambiguity and poor information scent" — hence a "Learn more about …" that names its destination passes).
- Nielsen, [Passive Voice Is Redeemed For Web Headings](https://www.nngroup.com/articles/passive-voice-is-redeemed-for-web/) (2007): rule 6 ("Typically, it's even harder for readers to understand passive sentences that don't explicitly state the actor"; passive to front-load keywords; the skill's row-6 payroll example is adapted from its social-security one).

### Shopify

- Polaris repository `Shopify/polaris` at [`3f7954a`](https://github.com/Shopify/polaris/tree/3f7954ae42fabf26d63cee68c23ceebfd7ef0972/polaris.shopify.com/content): `components/feedback-indicators/badge.mdx`, rule 3 ("Use a single word to describe the tone of an object. Only use two words if you need to describe a complex state"; "Always describe the tone in the past tense. For example, refunded not refund"); `components/actions/button.mdx`, rule 9 ("Verbs like “View” or “Go” or “Read” are often unnecessary"); `content/error-messages.mdx`, rule 10 ("unless Shopify caused the problem").
- Shopify app design, [Content](https://shopify.dev/docs/apps/design/content): rule 5 ("Avoid duplicating content, such as adding a page title under the page Title bar").

### Others

- Google developer documentation style guide, [Lists](https://developers.google.com/style/lists), "Parallel syntax": rule 11 ("Use the same syntax/structure for all list items in a given list, if possible."). Advisory.
- Material Design 3, [Word choice](https://m3.material.io/foundations/content-design/style-guide/word-choice): rule 2 (second-person "you" and "your").
- Mailchimp Content Style Guide, [Grammar and mechanics](https://styleguide.mailchimp.com/grammar-and-mechanics/): rule 6 (passive to "emphasize the action over the subject").
- Atlassian Design System, [Error messages](https://atlassian.design/foundations/content/designing-messages/error-messages): rule 8 (avoid "please"); rule 10 ("Use we instead of you"; "If you don’t know the reason for an error, don’t make one up").
- W3C, [WCAG 2.2](https://www.w3.org/TR/WCAG22/#label-in-name) SC 2.5.3 Label in Name (normative): "the name contains the text that is presented visually"; [Understanding 2.5.3](https://www.w3.org/WAI/WCAG22/Understanding/label-in-name.html) (advisory).
- GOV.UK [A to Z style guide](https://guidance.publishing.service.gov.uk/writing-to-gov-uk-standards/style-guides/a-to-z-style-guide/), "Active voice", and Mailchimp's grammar page: rule 6 agreement.
