# Convention, salience and memory

The seven "laws of UX" that govern what users expect, what stands out, and what
they remember — each checked against its primary source.

## Contents

- [Evidential ranking](#evidential-ranking)
- [Jakob's Law of the Internet User Experience](#jakobs-law-of-the-internet-user-experience)
- [Aesthetic-usability effect](#aesthetic-usability-effect)
- [Von Restorff (isolation) effect](#von-restorff-isolation-effect)
- [Serial position effect (primacy and recency)](#serial-position-effect-primacy-and-recency)
- [Peak-end rule](#peak-end-rule)
- [Zeigarnik effect](#zeigarnik-effect)
- [Postel's Law (the robustness principle), applied to interfaces](#postels-law-the-robustness-principle-applied-to-interfaces)
- [Where these conflict](#where-these-conflict)
- [Sources](#sources)

## Evidential ranking

They are not peers, and listing them as peers is itself the error. Peak-end for a
bounded episode has a field replication with 287 patients. The Zeigarnik memory
effect has a 59-publication meta-analysis returning a recall ratio of 0.99.

| Principle | Cite it |
|---|---|
| Peak-end rule | Freely, for one bounded episode with a clear end |
| Jakob's Law | Freely, for interaction conventions and control placement |
| Aesthetic-usability effect | Only as a claim about perception and tolerance |
| Von Restorff | Only where recall is genuinely at stake |
| Serial position | Only where the material will be gone when recalled |
| Zeigarnik | Only in its refuted form, replaced by Ovsiankina |
| Postel's Law | As an engineering maxim adopted by analogy, never as a usability finding |

---

### Jakob's Law of the Internet User Experience

**Statement** — Users spend most of their time on sites other than yours, so they
arrive with a mental model built from those sites and expect yours to behave the
same way.

**Provenance** — Jakob Nielsen, "End of Web Design," Alertbox / Nielsen Norman
Group, 22 July 2000. Original wording: "Users spend most of their time on *other*
sites. This means that users prefer your site to work the same way as all the
other sites they already know." Restated in Nielsen, "Jakob's Law of the Internet
User Experience," UX Tigers, 2023, which cites two supporting studies. It is a
heuristic coined by a named practitioner, not a result derived from a specific
experiment — the 2000 article cites no study.

**Predicts** — On first encounter with an unfamiliar pattern, users apply the
convention rather than the design, producing errors and slower completion. The
penalty decays with repetition along a power-law learning curve (Budiu, NN/g,
2016), so it is largest for low-frequency, low-loyalty, first-visit audiences and
near-zero for daily-use tools. The strongest empirical support NN/g offers is
convention-specific: Whitenton (NN/g, 2016) — 14 fashion-retail sites, 50 users,
users 6× as likely to fail to reach the homepage in one click when the logo was
centred rather than left-aligned.

**In an interface** — Conventional control, conventional place, conventional
behaviour: logo top-left and clickable to home; primary nav horizontal below or
beside it; search top-right; cart top-right; links visually distinct and
underlined in body copy; submit at the end of the form; browser back working. On
a marketing site for an unfamiliar product, where nearly every visitor is a
first-time visitor who will never climb the learning curve, this is where the law
bites hardest. We apply it to layout and interaction, not to visual identity —
a narrowing argued in Misapplied as, and not Nielsen's own scope.

**Misapplied as** — A veto on differentiation of any kind: "Jakob's Law says look
like everyone else." We narrow it to interaction conventions and the location and
behaviour of controls, and treat it as silent on typeface, colour, motion,
illustration, copy voice and composition.

**That narrowing is ours, and Nielsen does not agree.** "End of Web Design" opens
by asking that sites "tone down their individual appearance and distinct design"
across four named layers — *visual design*; terminology and labeling; interaction
design and workflow; information architecture — and prefaces its "What Remains in
Web Design" section with "Even as websites become more similar and appearance
design becomes more simplified…". Task analysis and content design are what he
says remains, but not in contrast to visual sameness; he asks for visual sameness
too. We drop the visual half because the empirical support NN/g offers is
control-placement-specific (see Predicts), so the visual half is his opinion
carrying none of the cited evidence. Cite the narrowing as an editorial position
of this file, never as what Nielsen wrote.

Second misapplication: quoting "you can kiss about 80% of your potential customer
base goodbye" as a measured figure. That sentence is in the 2023 UX Tigers
restatement, not the 2000 Alertbox piece, and it carries no citation, footnote or
link there; no study stands behind it.

**Limits** — Formulated in 2000 for the desktop web, when conventions were young
and switching cost was a page load. It is silent on which convention to follow
when several compete (hamburger vs. visible nav; drawer vs. modal), and it is
self-referential — every convention it defends began as somebody breaking one, so
applied universally it would have prevented the patterns it now protects. The
supporting evidence is thin and convention-specific: the centred-logo study
compared 50 users across 14 *different* sites, so site quality, brand familiarity
and layout are confounded with logo position. It is not a controlled A/B test of
one variable. Deliberate deviation is licensed by Budiu's three conditions:
(1) will the new design perform *much* better once learned; (2) will users
credibly return often enough to learn it; (3) can you accelerate learning through
exposure or affordance. Nielsen's bar: "Even if a new design is hypothetically
10% better than the prevailing standard, users won't use it if it causes them 20%
worth of aggravation and learning overhead the first few times they attempt using the design." The law does not
forbid breaking convention. It prices it, and the price is paid by first-time
users only.

---

### Aesthetic-usability effect

**The popular design application — "beautiful designs are more usable, so polish
buys usability" — is not supported by the research. The founding studies measured
what users *said*, not what they *did*, and the one study that manipulated real
usability found aesthetics did not move actual performance. It never licenses
deferring usability work.**

**Statement** — Users rate visually attractive interfaces as easier to use than
less attractive ones, and that perception is only loosely coupled to how usable
those interfaces actually are.

**Provenance** — Masaaki Kurosu & Kaori Kashimura (Hitachi Design Center),
"Apparent usability vs. inherent usability: experimental analysis on the
determinants of the apparent usability," CHI '95 Conference Companion, ACM, 1995,
pp. 292–293, DOI 10.1145/223355.223680. 26 ATM interface layouts, 252
participants, who *rated* apparent ease of use and beauty — they never operated
the machines; "inherent usability" was derived analytically from
expert-identified design factors, not from observed task performance. Replicated
with a controlled manipulation by N. Tractinsky, A. S. Katz & D. Ikar, "What is
beautiful is usable," *Interacting with Computers* 13(2), 2000, 127–145: "the
degree of system's aesthetics affected the post-use perceptions of both
aesthetics and usability, whereas the degree of actual usability had no such
effect." The phrase "aesthetic-usability effect" is a later coinage in the design
literature; it does not appear in Kurosu & Kashimura, and its origin could not be
established — treat any attribution of the name as unverified.

**Predicts** — Perceived-usability ratings, satisfaction scores and SUS results
track visual appeal. In usability testing, participants under-report problems in
an attractive prototype and keep trying rather than abandoning. It does **not**
predict lower error rates, faster task completion, or higher task-success rates.

**In an interface** — Two operational uses, both defensive. (1) In evaluation:
hold visual fidelity constant across compared conditions or aesthetics confounds
the result, and never accept "no problems found" from a beautiful prototype
without behavioural measures — record task success, time on task and error
counts, not only ratings. (2) In build: polish buys goodwill for minor friction —
a slightly slow load, a small inconsistency — and buys nothing for a broken flow.
Trading a week of visual refinement against a week of fixing a blocking
interaction, the research says fix the interaction.

**Misapplied as** — "Beautiful designs *are* more usable," used to defer or skip
usability work. Also as a licence for decorative complexity: the effect concerns
perceived beauty, not ornament, and nothing in it says added visual elaboration
improves anything.

**Limits** — The direction of the effect is contested and may run the other way.
Alexandre N. Tuch, Sandra P. Roth, Kasper Hornbæk, Klaus Opwis & Javier A.
Bargas-Avila, "Is beautiful really usable? Toward understanding the relation
between usability, aesthetics, and affect in HCI," *Computers in Human Behavior*
28(5), 2012, 1596–1607 (n=80, online shop, aesthetics and usability independently
manipulated): "Results show that aesthetics does not affect perceived usability.
In contrast, usability has an effect on post-use perceived aesthetics" — what is
usable is beautiful. They note the classic finding "can be reversed under certain
conditions (here: strong usability manipulation combined with a medium to large
aesthetics manipulation)." One study does find a real performance effect —
Andreas Sonderegger & Juergen Sauer, "The influence of design aesthetics in
usability testing: Effects on user performance and perceived usability," *Applied
Ergonomics* 41(3), 2010, 403–410 (n=60 adolescents aged 14–17, simulated mobile
phone; the attractive model produced shorter task times) — but it is a single
study with a narrow sample and does not generalise to the broad claim. NN/g's own
boundary: "A pretty design can make users forgiving of minor usability problems,
but not of large ones." Kurosu & Kashimura tested one static ATM screen, all 26
variants built from identical elements, first impressions only, no interaction,
no flow.

---

### Von Restorff (isolation) effect

**The popular design application — "make the CTA orange and it will be clicked" —
is not supported by the research. This is a memory effect measured by delayed
recall of lists. Nothing in von Restorff's work or its replications addresses
click-through, gaze or persuasion.**

**Statement** — In a set of otherwise similar items, the single item that differs
is recalled better than the rest, produced by its relation to a homogeneous
context rather than by raw conspicuity.

**Provenance** — Hedwig von Restorff, "Über die Wirkung von Bereichsbildungen im
Spurenfeld," *Psychologische Forschung* 18, December 1933, pp. 299–342,
DOI 10.1007/BF02409636. Never published in English. Corrective reading of the
original: R. Reed Hunt, "The subtlety of distinctiveness: What von Restorff
really did," *Psychonomic Bulletin & Review* 2(1), March 1995, pp. 105–112 — "von
Restorff… presented evidence that perceptual salience is not necessary for the
isolation effect. She further argued that the difference between the isolated and
surrounding items is not sufficient to produce isolation effects but must be
considered in the context of similarity."

**Predicts** — When a set is homogeneous and exactly one member deviates, that
member is recalled better after the set is gone. It predicts recall — not
attention capture, not gaze, not clicks. It further predicts that the advantage
collapses as the number of deviants rises, because the mechanism requires a
homogeneous background for the isolate to stand against.

**In an interface** — One primary action per view, every other control demoted to
secondary or tertiary emphasis. One accent hue per composition rather than the
whole palette in one viewport. One highlighted tier in a pricing table. One
badged item in a nav. The discipline it imposes is on the *background*: the
isolate works only because everything else is uniform, so the effect is bought by
restraint elsewhere, not by shouting louder.

**Misapplied as** — A law of attention or conversion. Second and more common:
isolating several elements at once — three "standout" elements are not three
isolates, they are a new homogeneous set, and the effect dilutes across them and
is lost. Third: relying on colour alone to carry the isolation, which excludes
users with colour-vision deficiency. Encode the difference in at least two
channels.

**Limits** — The evidence base is list-learning with nonsense syllables and word
lists, not interfaces. Stephen R. Schmidt & Constance R. Schmidt, "Revisiting von
Restorff's early isolation effect," *Memory & Cognition* 45(2), 2017, pp.
194–207, found the effect is position-dependent — conceptually isolated items
early in a list showed *impaired* memory relative to homogeneous controls — that
it emerged only for automatic contrasts (numbers among words) and not for
conceptual category differences, and that attention during presentation is in
fact necessary, contradicting the stronger reading of Hunt. There is also a
practical ceiling specific to interfaces: an element made too visually distinct
from its surround reads as an advertisement and is ignored, so maximum isolation
is not maximum effectiveness.

---

### Serial position effect (primacy and recency)

**The popular design application — ordering a navigation bar or a menu by the
recall curve — is not supported by the research. A navigation bar is
persistently on screen. It is not a memory test, and the recall curve does not
govern it.**

**Statement** — When a series of items is presented and then recalled from
memory, items at the beginning and the end are recalled more accurately than
items in the middle.

**Provenance** — First described by Hermann Ebbinghaus, *Über das Gedächtnis*
(1885), in serial learning of nonsense syllables. The canonical free-recall
demonstration is Bennet B. Murdock Jr., "The serial position effect of free
recall," *Journal of Experimental Psychology* 64(5), 1962, pp. 482–488 — a steep
primacy effect over the first three or four items, an S-shaped recency effect
over the last eight, and a flat asymptote between. (This paper is frequently
miscited to *Journal of Verbal Learning and Verbal Behavior*; the APA record is
*Journal of Experimental Psychology*.) The two-store account and the critical
boundary come from Murray Glanzer & Anita R. Cunitz, "Two storage mechanisms in
free recall," *Journal of Verbal Learning and Verbal Behavior* 5(4), 1966, pp.
351–360.

**Predicts** — For material presented sequentially and recalled later *without it
in view*, first and last items are recalled best. Recency is fragile: Glanzer &
Cunitz showed a filled 30-second delay between presentation and recall abolishes
the recency peak entirely while leaving primacy intact. Slowing presentation
raises primacy but not recency — a double dissociation.

**In an interface** — Only where the material is transient. A spoken or video
walkthrough: state the thing that must be remembered first, and end on the single
action you want taken. A multi-step onboarding sequence the user cannot re-read.
An email or a pitch deck read once. Load the two ends and accept that the middle
will be lost.

**Misapplied as** — "Put Home first and Contact last in the nav because of the
serial position effect." What governs a visible menu is scan order and Jakob's
Law expectation. Ordering an always-visible menu by a recall curve is a category
error, and it is the most common way this effect appears in design writing. It is
also misapplied to long scrolling pages, where nothing is being recalled from
memory at all.

**Limits** — Murdock's paradigm was word lists of roughly 10–40 items at one to
two seconds each, with immediate free recall — nothing like a page. The effect
concerns recall accuracy, not preference, attention, comprehension or clicks.
Recency, the half designers most often invoke, is the half that vanishes after
roughly 30 seconds of intervening activity, which is shorter than almost any real
session. Before applying it, ask one question: will the user have to recall this
when it is no longer visible? If no, the effect does not apply.

---

### Peak-end rule

**Statement** — Retrospective evaluation of a bounded, singular experience is
dominated by the affect at its most intense moment and at its final moment, with
total duration largely neglected.

**Provenance** — Daniel Kahneman, Barbara L. Fredrickson, Charles A. Schreiber &
Donald A. Redelmeier, "When More Pain Is Preferred to Less: Adding a Better End,"
*Psychological Science* 4(6), November 1993, pp. 401–405. Thirty-two male
University of California students aged 19–39: a 60 s cold-water trial at 14 °C
versus the same 60 s plus 30 s during which the water was warmed to 15 °C. 22 of
32 (69%) chose to repeat the *longer* trial. Field replication: Donald A.
Redelmeier & Daniel Kahneman, "Patients' memories of painful medical treatments:
real-time and retrospective evaluations of two minimally invasive procedures,"
*Pain* 66(1), 1996, 3–8 — colonoscopy (n=154) and lithotripsy (n=133);
retrospective total-pain judgments correlated with peak intensity and with the
final three minutes (both p < 0.005), while procedure duration, ranging from 4 to
69 minutes, did not significantly affect retrospective judgment.

**Predicts** — Two people who underwent objectively equal amounts of friction
will rate the experience differently if one ended on a better note. Adding time
to an experience can *improve* its remembered value if the added time is less bad
than the peak. It predicts remembered and reported evaluation — not
moment-to-moment satisfaction, and not behaviour during the experience.

**In an interface** — Identify the worst moment in a bounded flow and the last
moment, and spend there first. The error state in a checkout is the peak: fix it
before polishing the hero. The confirmation screen is the end: it is the cheapest
place in the product to buy goodwill, and dumping the user onto a blank page or
an upsell squanders it. Same for a support conversation, a form submission, a
demo call, a pitch.

**Misapplied as** — Extended from a bounded episode to a whole product
relationship or a whole day, and used to argue the middle does not matter. Also
its dark-pattern use: manufacturing an artificial "peak", or holding the user at
the exit with a please-don't-go interstitial, which NN/g criticises as
prioritising "clicks and conversions over long-term customer loyalty." Watch for
number drift in secondary sources — NN/g's peak-end article (Lexie Kane, 30 Dec
2018) reports "eighty percent preferred Round 2"; the paper reports 22 of 32,
i.e. 69% (81% is the subgroup of 21 subjects who actually experienced a decrement
in discomfort).

**Limits** — The boundary is multi-episode complexity. Talya Miron-Shatz,
"Evaluating multiepisode events: Boundary conditions for the peak-end rule,"
*Emotion* 9(2), 2009, pp. 206–213 — samples of 810 (US), 820 (France) and 805
(Denmark) reporting via the Day Reconstruction Method — found that "contrary to
the predictions of the peak-end rule," the duration-weighted average of episodes
was the best predictor of retrospective evaluation of the day, and "The end
episode did not predict retrospective evaluations." So it holds for one bounded
episode with a clear terminus — a checkout, a support call, a procedure — and not
for the aggregate of many episodes: a month of using a product, a whole day, a
relationship. The founding study is n=32, all male, all students, single session,
physical pain; the field replication in *Pain* is what makes it credible, and
that too is a bounded clinical episode.

---

### Zeigarnik effect

**The popular design application — progress bars, incomplete-profile nudges and
completion meters justified on the grounds that incompleteness creates memorable
psychological tension — is not supported by the research. The memory mechanism is
precisely the part that failed to replicate.**

**Statement** — As originally claimed, interrupted or incomplete tasks are
remembered better than completed ones. As the evidence now stands, that memory
advantage does not replicate, and the robust finding in this literature is a
different one: people tend to resume interrupted tasks (the Ovsiankina effect).

**Provenance** — Bluma Zeigarnik, "Über das Behalten von erledigten und
unerledigten Handlungen," *Psychologische Forschung* 9, 1927, pp. 1–85; English
translation "On Finished and Unfinished Tasks" in W. D. Ellis (ed.), *A Source
Book of Gestalt Psychology*, 1938. The definitive modern assessment is Romain
Ghibellini & Beat Meier, "Interruption, recall and resumption: a meta-analysis of
the Zeigarnik and Ovsiankina effects," *Humanities and Social Sciences
Communications* 12, article 962, 2025, pooling 59 publications.

**Predicts** — On the meta-analytic evidence, essentially nothing about memory.
Ghibellini & Meier report, for the commonly used measure (ratio of mean
interrupted-task recall to mean completed-task recall), 0.99 both with and
without Zeigarnik's own 1927 data (N=38 and N=37 publications); interrupted tasks
accounted for 49.43% of recalled tasks with the original data and 49.16% without
(N=14 and N=13) — chance; pooled Cohen's dz = 0.15 (N=8). Their conclusion: "The
current findings do not support a memory advantage for interrupted tasks when
situational influences and individual differences are not accounted for." What
*does* hold in the same meta-analysis is the Ovsiankina effect (Maria Ovsiankina,
1928): interrupted tasks are resumed 67.00% of the time including Ovsiankina's
original data, 66.79% excluding it (N=21 and N=20).

**In an interface** — Design for resumption, which is the supported finding, and
stop citing memory. Save drafts automatically and surface them. "Continue where
you left off." Multi-step forms that persist state and can be re-entered at the
step abandoned. A visible completion state on a profile or setup checklist — it
works because an interrupted task invites resumption, not because it lodges in
memory. In a spec, "users resume interrupted tasks about two-thirds of the time
(Ghibellini & Meier 2025)" is defensible; "the Zeigarnik effect means they'll
remember it" is not.

**Misapplied as** — The whole standard design usage: progress bars,
incomplete-profile nudges, gamified completion meters and content cliffhangers
justified by memorable psychological tension. It is also routinely cited to
justify deliberately withholding completion — an engagement dark pattern wearing
a citation.

**Limits** — Even the surviving Ovsiankina effect is about resumption when
resumption is available and cheap, in laboratory tasks under an experimenter's
gaze. Ghibellini & Meier attribute the historical Zeigarnik result partly to
conditions rarer today — experimenter authority, situational demands of task
performance, task involvement — and conclude the effect "lacks universal
validity." Listing it alongside better-supported principles without this caveat
implies an evidential parity that does not exist.

---

### Postel's Law (the robustness principle), applied to interfaces

**The transposition to user interfaces has no research behind it. It is an
analogy borrowed from protocol engineering. Cite it as an engineering maxim, not
as a usability finding.**

**Statement** — In its original form, an implementation should be strict in what
it emits and tolerant of variation in what it accepts; transposed to interfaces,
accept input in whatever form the user supplies and normalise, while producing
output that is strict and predictable.

**Provenance** — Jon Postel (ed.), RFC 760, "DoD Standard Internet Protocol,"
January 1980, §3.2: "In general, an implementation should be conservative in its
sending behavior, and liberal in its receiving behavior." Restated in Postel
(ed.), RFC 793, "Transmission Control Protocol," September 1981, §2.10: "be
conservative in what you do, be liberal in what you accept from others." The
interface transposition was popularised by Jon Yablonski, *Laws of UX* (O'Reilly,
2020) and lawsofux.com, whose citation list for this entry is design blog posts
(Mark Boulton, Jeremy Keith/Adactio, A List Apart, Steven Garrity) and Wikipedia.
No study.

**Predicts** — Nothing, in the empirical sense. It is a normative engineering
maxim, not a model of behaviour, and it makes no falsifiable prediction about
users. The nearest testable claim it stands in for is well established elsewhere
and does not need Postel: forcing users to reformat data they already hold
correctly — spaces in a card number, parentheses in a phone number, a leading
zero — creates avoidable input errors.

**In an interface** — Strip and normalise whitespace, dashes and parentheses in
phone, card and account numbers before validating. Accept several date formats
and echo back the parsed date unambiguously. Accept a pasted URL with or without
scheme. Accept case-insensitive email. Make only genuinely required fields
required. Pair every act of tolerance with visible confirmation of the
interpretation — take "4111 1111 1111 1111" happily, then show what was stored.

**Misapplied as** — A licence for permissive, silent validation: guessing at
ambiguous input and proceeding without telling the user what was assumed.
"03/04/25" accepted liberally and interpreted wrongly is worse than a rejection.
Also used to justify hiding format requirements on the grounds that anything is
accepted, and to justify accepting malformed data into storage, where it becomes
somebody else's correctness problem.

**Limits** — The IETF has substantially walked this back. Martin Thomson & David
Schinazi, RFC 9413, "Maintaining Robust Protocols," June 2023, argues that
over-applying the robustness principle causes long-term ecosystem damage:
tolerated errors become entrenched, forcing bug-for-bug compatibility on every
later implementation and raising the barrier to new entrants. The interface
analogue is real — indefinite tolerance of malformed input produces dirty data
and downstream ambiguity nobody can reverse. Be liberal at the boundary, strict
in what you store, and always echo the normalisation back.

---

## Where these conflict

**Jakob's Law vs. Von Restorff.** They do not contradict once the layers are
separated. Jakob's Law governs the *location and behaviour* of controls — where
the cart icon lives, that the logo goes home, that back works. Von Restorff
governs *emphasis within a composition* — which thing on this screen is loudest.
Moving the cart icon costs real errors; making it the only accented element costs
nothing. Jakob's Law invoked against a visual decision is, on the narrowing
this file argues for, an interaction law applied to a layer its evidence never
covered — though Nielsen himself asked for visual sameness as well, so cite the
evidence gap and not his authority.

**Jakob's Law vs. peak-end.** A peak is by construction unusual, and the unusual
is what Jakob's Law prices. Resolve it with Budiu's power-law framing: put the
peak where the user is not trying to complete a familiar task — a confirmation
screen, an empty state, a completed-onboarding moment — where there is no
convention to violate and no throughput to lose. Never in the middle of a
checkout.

**Serial position vs. Von Restorff.** Serial position confers weight on two slots,
first and last. Von Restorff needs exactly one isolate. Together: position may
weight both ends, but only one of them may also carry visual emphasis.
Emphasising both produces two deviants and forfeits the isolation advantage on
each.

**Aesthetic-usability vs. Jakob's Law, as deployed in client arguments.**
Aesthetic-usability gets used to argue distinctive visual treatment pays; Jakob's
Law gets used to argue it costs. Both are misstated. Aesthetic-usability predicts
ratings, not task success, so it cannot be cashed in as usability. Jakob's Law
has measured support only for interaction deviation, not visual deviation, so it
cannot be cashed in against a typeface or a palette — Nielsen's article does ask
for visual restraint, but offers no study for that half. Correctly stated, they do not meet.

**Postel's Law vs. unambiguous feedback.** Silent tolerance and clear
communication pull opposite ways: the more formats accepted without comment, the
less the user knows what was understood. RFC 9413 makes the same argument in the
principle's home domain. Liberal acceptance obliges you to echo the normalised
interpretation back.

## Sources

- Jakob Nielsen, "End of Web Design," NN/g, 22 July 2000 — https://www.nngroup.com/articles/end-of-web-design/
- Jakob Nielsen, "Jakob's Law of the Internet User Experience," UX Tigers, 2023 — https://www.uxtigers.com/post/jakobs-law
- Kathryn Whitenton, "Centered Logos Hurt Website Navigation," NN/g, 10 July 2016 — https://www.nngroup.com/articles/centered-logos/
- Raluca Budiu, "The Power Law of Learning: Consistency vs. Innovation in User Interfaces," NN/g, 30 Oct 2016 — https://www.nngroup.com/articles/power-law-learning/
- Kathryn Whitenton, "When Is It OK to Be Inconsistent in User Interface Design?" NN/g, 19 Mar 2021 — https://www.nngroup.com/videos/inconsistent-ui-design/
- Masaaki Kurosu & Kaori Kashimura, "Apparent usability vs. inherent usability," CHI '95 Conference Companion, ACM, 1995, 292–293, DOI 10.1145/223355.223680
- N. Tractinsky, A. S. Katz & D. Ikar, "What is beautiful is usable," *Interacting with Computers* 13(2), 2000, 127–145
- Alexandre N. Tuch, Sandra P. Roth, Kasper Hornbæk, Klaus Opwis & Javier A. Bargas-Avila, "Is beautiful really usable?" *Computers in Human Behavior* 28(5), 2012, 1596–1607
- Andreas Sonderegger & Juergen Sauer, "The influence of design aesthetics in usability testing," *Applied Ergonomics* 41(3), 2010, 403–410
- Kate Moran, "The Aesthetic-Usability Effect," NN/g, 3 Feb 2024 — https://www.nngroup.com/articles/aesthetic-usability-effect/
- Hedwig von Restorff, "Über die Wirkung von Bereichsbildungen im Spurenfeld," *Psychologische Forschung* 18, 1933, 299–342
- R. Reed Hunt, "The subtlety of distinctiveness: What von Restorff really did," *Psychonomic Bulletin & Review* 2(1), 1995, 105–112
- Stephen R. Schmidt & Constance R. Schmidt, "Revisiting von Restorff's early isolation effect," *Memory & Cognition* 45(2), 2017, 194–207
- Hermann Ebbinghaus, *Über das Gedächtnis*, 1885
- Bennet B. Murdock Jr., "The serial position effect of free recall," *Journal of Experimental Psychology* 64(5), 1962, 482–488
- Murray Glanzer & Anita R. Cunitz, "Two storage mechanisms in free recall," *Journal of Verbal Learning and Verbal Behavior* 5(4), 1966, 351–360
- Daniel Kahneman, Barbara L. Fredrickson, Charles A. Schreiber & Donald A. Redelmeier, "When More Pain Is Preferred to Less: Adding a Better End," *Psychological Science* 4(6), 1993, 401–405
- Donald A. Redelmeier & Daniel Kahneman, "Patients' memories of painful medical treatments," *Pain* 66(1), 1996, 3–8
- Talya Miron-Shatz, "Evaluating multiepisode events: Boundary conditions for the peak-end rule," *Emotion* 9(2), 2009, 206–213
- Lexie Kane, "The Peak–End Rule: How Impressions Become Memories," NN/g, 30 Dec 2018 — https://www.nngroup.com/articles/peak-end-rule/
- Bluma Zeigarnik, "Über das Behalten von erledigten und unerledigten Handlungen," *Psychologische Forschung* 9, 1927, 1–85
- Romain Ghibellini & Beat Meier, "Interruption, recall and resumption: a meta-analysis of the Zeigarnik and Ovsiankina effects," *Humanities and Social Sciences Communications* 12:962, 2025 — https://www.nature.com/articles/s41599-025-05000-w
- Jon Postel (ed.), RFC 760 §3.2, January 1980 — https://www.rfc-editor.org/rfc/rfc760.txt
- Jon Postel (ed.), RFC 793 §2.10, September 1981 — https://www.rfc-editor.org/rfc/rfc793.txt
- Martin Thomson & David Schinazi, RFC 9413, "Maintaining Robust Protocols," June 2023 — https://www.rfc-editor.org/rfc/rfc9413.html
- Jon Yablonski, lawsofux.com — used only to establish how these are popularly stated and cited
