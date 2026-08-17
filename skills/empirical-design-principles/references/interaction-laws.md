# The named quantitative laws

The five laws design writing cites as if they were peers — Fitts, Hick–Hyman, Miller, Doherty,
Tesler — with what each one actually claims, checked against the primary sources.

## Contents

- [Evidentiary standing](#evidentiary-standing) — they are not peers, and ranking them as peers is the first error
- [Fitts's Law](#fittss-law) — pointing time from distance and target size
- [Hick's Law (Hick–Hyman Law)](#hicks-law-hickhyman-law) — choice time from stimulus entropy
- [Miller's Law (the magical number seven)](#millers-law-the-magical-number-seven) — absolute judgment, immediate memory, subitising
- [The Doherty Threshold](#the-doherty-threshold) — system response time and user output
- [Tesler's Law (Conservation of Complexity)](#teslers-law-conservation-of-complexity) — who absorbs the irreducible work
- [Where these laws contradict each other](#where-these-laws-contradict-each-other)
- [Sources](#sources)

---

## Evidentiary standing

The five are cited with equal authority and do not have equal backing. Ranking them as peers is
itself an error, because it lends a 1982 vendor brochure and an undated aphorism the standing of a
seventy-year-old replicated equation.

| Law | Is the finding supported? | Is the popular design application supported? |
|---|---|---|
| Fitts | Yes — equation, seventy years of replication, an ISO standard | Yes, for pointer movement to a known target. The touchscreen edge corollary is not. |
| Hick–Hyman | Yes — one of the better-replicated results in experimental psychology | **No.** Its preconditions are almost never met in an interface, and "less is better" is the opposite of what the current work concludes. |
| Miller | Yes — absolute judgment and chunking are real results | **No.** "7±2 items in a menu" appears nowhere in the paper in any form. |
| Doherty | Partly — uncontrolled 1982 field observation, sub-second, from an IBM sales document | **No.** The 400 ms figure is not in the source. |
| Tesler | No study exists — it is a named practitioner aphorism | It is a useful directive, but it is not research and is routinely inverted. |

---

### Fitts's Law

**Statement** — The time to complete a rapid aimed movement to a target of known location is a
linear function of the log ratio of movement distance to target tolerance, so the motor system's
information rate stays roughly constant across a range of amplitudes and tolerances.

**Provenance** — Fitts, P. M. (1954). "The information capacity of the human motor system in
controlling the amplitude of movement." *Journal of Experimental Psychology*, 47(6), 381–391.
Fitts's own equations are Eq. (1), Id = −log2(Ws / 2A) bits per response, and Eq. (2),
Ip = −(1/t) log2(Ws / 2A) bits per second, where Ws is the tolerance range and A the average
amplitude.

The regression form everyone quotes — MT = a + b·ID — is not in that paper, and is not Welford's
either. MacKenzie (2018, *The Wiley Handbook of Human Computer Interaction*, ch. 17) states: "The
prediction form of Fitts' law (Eq. 17.4) does not appear in Fitts' original 1954 publication," and
names no originator. Welford (1960; 1968, p. 147) is credited with something else — the index
variant ID = log2(A/W + 0.5), which fixes the negative-ID problem at low difficulty. The regression
form's usual first appearance is Fitts & Peterson (1964), "Information capacity of discrete motor
responses," *Journal of Experimental Psychology*, 67, 103–112; who first wrote it down is not
cleanly established, so do not attribute it. The Shannon variant ID = log2(A/W + 1) is MacKenzie
(1992), and is what ISO 9241-9:2000 (renumbered ISO 9241-411:2012) standardises.

**Predicts** — Movement time rises with distance and falls with target size, logarithmically, so
doubling target size buys progressively less each time. Fitts measured Ip at roughly 10–12 bits per
second across three tasks. Two targets with the same distance-to-size ratio take about the same
time regardless of absolute scale. For a mouse, screen edges and corners have effectively infinite
tolerance because the pointer pins against them, so edge targets are acquired fast at any approach
speed.

**In an interface** — Put the primary action adjacent to the last field the user touched, which
cuts D. Make the whole row or card clickable rather than the 16 px icon inside it, which raises W.
On a desktop app, hang the global menu on the top edge and put frequent-but-destructive controls in
a corner. Put two controls used in sequence next to each other, not at opposite ends of a toolbar.
When auditing, measure the actual pixel distance from the cursor's resting position — usually the
last click — to the next target, not from the viewport centre.

**Misapplied as** — Four ways.

1. **The screen-edge corollary applied to touchscreens is not supported.** NN/g (Budiu, 31 July
   2022) states edge placement "offers no advantage for touchscreens," and edge targets can take
   *longer*. Pinning requires a pointer; a finger has no cursor to pin. "Apply Fitts's law" is
   under-specified until the input device is named.
2. Justifying unbounded button growth. The relationship is logarithmic — past a point, extra size
   buys almost nothing and costs layout density.
3. Applying it to a target the user must first *find*. Fitts's law models movement to a target of
   known location and says nothing about visual search time.
4. Citing it as a general "make things easy" principle rather than a model of aimed pointer
   movement.

**Limits** — Fitts's own, verbatim: "rate of performance is approximately constant over a
considerable range of movement amplitudes and tolerance limits, but falls off outside this optimum
range." His conditions covered Id of 1 to 10 bits. Movements of 1 and 2 inches were "consistently
less efficient than movements of 4 to 8 in.", and the smallest tolerance (1/32 in.) gave low rates.
The index "is insensitive to the weight of the stylus used in the first experiment and hence to the physical work required by the task" and
"insensitive to the information required for specifying the direction of a movement, or for
specifying additional manipulatory acts such as the finger movements required to grasp and release
objects." The denominator is arbitrary by his own admission: "The specification of the possible
amplitude range is arbitrary and has been set at twice the average amplitude." And: "The absolute
level of capacity of the motor system probably varies considerably for different movements, limbs,
and muscle groups."

Documented since: the original form yields negative ID at low difficulty, fixed by Welford's
log2(A/W + 0.5) and Shannon's log2(A/W + 1). It breaks down for 2D rectangular targets, sometimes
again producing negative ID, requiring the "smaller-of" or W′ models (MacKenzie & Buxton, CHI '92,
219–226). It fails for small-target finger touch, requiring the dual-distribution FFitts model (Bi,
Li & Zhai, CHI 2013, 1363–1372). Valid comparison assumes a nominal 4% error rate and requires the
effective-width correction We = 4.133 × SDx.

Population: 16 right-handed college men (Exps. I and II) and 20 students (Exp. III). Observed error
rates were 1.2% with the 1 oz stylus and 1.3% with the 1 lb, rising to 3.6–4.1% in the hardest
condition.

---

### Hick's Law (Hick–Hyman Law)

**THE FINDING IS SUPPORTED. THE DESIGN APPLICATION IS NOT.** The law itself replicates well. What
is not supported is what design writing does with it. Liu et al. (CHI 2020) state in their
abstract that Hick's law "speaks against, not for, the popular principle that 'less is better'."
The dominant design reading — reduce the number of options — is the opposite of the law's own
conclusion. The companion reading — and nest what remains into categories — is not something Hick's
law settles either way, and the paper most often quoted against nesting concludes the reverse. Both
halves of the folk advice are misuses, for different reasons. See **Misapplied as**.

**Statement** — For a practised observer responding to an explicit stimulus under a learned
stimulus–response mapping, choice reaction time grows linearly with the entropy of the stimulus
set: T = a + b·H, where H = log2(n) for n equiprobable alternatives.

**Provenance** — Hick, W. E. (1952). "On the rate of gain of information." *Quarterly Journal of
Experimental Psychology*, 4(1), 11–26. DOI 10.1080/17470215208416600. Hick's own form, as
reproduced in Liu et al.'s Eq. (5), is "R = log(n + 1) or R = log(ne + 1)". The first is the
headline form. The second is the error-corrected case from his second experiment, where ne is the
degree of choice and equals n when no errors are made — do not present it as the headline form.
His conclusion: "the amount of information extracted R is proportional to the time taken to extract
it, on the average," at roughly 5 bits per second.

Generalised by Hyman, R. (1953). "Stimulus information as a determinant of reaction time."
*Journal of Experimental Psychology*, 45(3), 188–196, who showed RT tracks stimulus entropy
H = Σ pi·log2(1/pi) however that entropy is produced. Reviewed in Proctor, R. W., & Schneider,
D. W. (2018). "Hick's law for choice reaction time: A review." *Quarterly Journal of Experimental
Psychology*, 71(6), 1281–1299.

**Predicts** — Adding alternatives costs time logarithmically, not linearly: 2 to 4 options costs
the same increment as 4 to 8. Under high stimulus–response compatibility or heavy practice, the
slope b collapses toward zero and the number of alternatives stops mattering at all.

**In an interface** — Legitimately: modelling a practised expert hitting one of n memorised
keyboard shortcuts, or a mode switch among a small fixed set the user knows. In genuine HCI
settings the measured slope is tiny. Liu et al. reanalysed two command-selection studies and
report 32 ms/bit and 8 ms/bit (the Glass and Glass-plus-Skin conditions of Roy et al.) and 4 ms/bit
(their own), against Hick's ~200 ms/bit. Their practical conclusion is that in interface work
"reaction time RT can usually be treated as a constant" — so the honest application is to stop
budgeting for it and model visual search and decision instead.

**Misapplied as** — Three ways, and the first two are the ones that do damage in a design review.

1. **"Reduce the number of options."** Not supported. The abstract of the most direct HCI
   examination of the law says it "speaks against, not for, the popular principle that 'less is
   better'."
2. **"Nest the options into categories," justified by Hick's law.** The justification is wrong in
   both directions, so state the maths rather than a slogan. Under Hick's law taken strictly the
   two layouts are *equivalent*: because log k + log(N/k) = log N, categorised splitting is the
   exact limit case f(x) + f(y) = f(xy). In Liu et al.'s worked N = 32 illustration, one page gives
   RL = a + 5b and four exclusive categories give RL = 2a + 5b — one extra intercept per level —
   but that penalty is specific to that illustration, not a general result. The paper's own second
   design principle is "If items are categorized, then they should always be split," and because
   realistic selection-time functions grow faster than the logarithm (f(exp(·)) convex), it
   concludes that categorised splitting *reduces* response latency. The frequently quoted line
   "the optimal strategy according to Hick's law consists of displaying all the items at once on
   the same page" is scoped to Hick's law alone and is not the paper's design recommendation.
   Neither "flatten it" nor "nest it" is settled by this law.
3. **Treating any observed logarithmic time curve as evidence for Hick's law.** Any
   divide-and-conquer search is logarithmic — hierarchical menu search (Landauer & Nachbar, CHI
   '85) and alphabetical scrolling both are. Liu et al.: "in many cases, this has nothing to do
   with Hick's law."

**Limits** — The preconditions are almost never met in an interface.

1. *Population and practice.* Hick was the only participant in his first experiment and had trained
   himself over 8,000 trials beforehand; the second used the author plus one other, both well
   trained. Hyman's participants were trained across ~15,000 trials.
2. *Compatibility collapses the effect.* The better the stimulus–response mapping, the shallower
   the slope. In Leonard's vibrator-to-finger task and Mowbray's read-aloud-numerals task the slope
   approaches 0 ms/bit — there is virtually no effect of stimulus uncertainty on reaction time. Liu
   et al. argue every HCI task has extremely good compatibility by construction, so the slope is
   always near zero.
3. *Practice erases it.* Mowbray showed RT for up to 10 alternatives reduced to the two-alternative
   level after six months' practice. Knight & Dagnall report slopes dropping from 73 to 23 ms/bit
   after two months. Seibel found almost no RT difference between 31 (5 bits) and 1,023 (10 bits)
   stimuli after more than 75,000 trials.
4. *Range is task-dependent.* Linearity is often given as holding for roughly 1–4 bits with RT
   over-estimated beyond that, but Liu et al. note Pollack found the relationship extending to
   about 10 bits in a word-naming task and conclude "the actual range where the relationship holds
   is thus very dependent on the actual task." Fitts & Posner noted RT seldom exceeds 1 s whatever
   the set size.
5. *Low-probability alternatives* are responded to faster than predicted.
6. *Errors.* Beyond 0.6 bits of equivocation, the loss from mistakes exceeds the gain from speed.
7. *Paradigm mismatch.* The law models choice reaction to an explicit stimulus under a learned
   mapping. In a menu the stimulus is implicit in the user's own goal, the mapping is not learned,
   and the task is visual search plus decision. Liu et al.: "the stimulus-response paradigm is
   rarely relevant to HCI tasks."

---

### Miller's Law (the magical number seven)

**"7±2 ITEMS IN A MENU" IS NOT SUPPORTED BY THE RESEARCH.** It is the most repeated misquote in
interface design. Miller's paper is about absolute judgment and immediate memory for unrelated
items. It contains no design recommendation, no mention of menus or displayed options, and it
predates interfaces. The underlying findings — absolute-judgment limits and chunking — are real and
useful; the menu rule attached to them is invented.

**Statement** — Miller reported three numerically similar but causally unrelated limits — a span of
absolute judgment of about 2.6 bits (2^2.6 ≈ 6 categories) for unidimensional stimuli, a span of
immediate memory of about seven *chunks*, and a subitising span of about six — and explicitly
argued that they are not the same phenomenon and that the shared number is probably a coincidence.

**Provenance** — Miller, G. A. (1956). "The magical number seven, plus or minus two: Some limits on
our capacity for processing information." *Psychological Review*, 63(2), 81–97. First delivered as
an Invited Address to the Eastern Psychological Association, Philadelphia, 15 April 1955. Updated
by Cowan, N. (2001). "The magical number 4 in short-term memory: A reconsideration of mental
storage capacity." *Behavioral and Brain Sciences*, 24(1), 87–114 — that is the target article;
the often-cited 87–185 is the span including open peer commentary and the author's response.

**Predicts** — For absolute identification of a stimulus varying on *one* dimension, people can
reliably sort into roughly 4–10 categories. Miller's measured range is "1.6 bits for curvature to
3.9 bits for positions in an interval," mean 2.6 bits, SD 0.6 — note that the 1.6 endpoint is
curvature specifically, not a general floor. For immediate serial recall, roughly seven chunks —
and his actual finding is that this count is invariant to bits per chunk, so recoding into bigger
chunks raises the information recalled without changing the number of chunks. Cowan's reanalysis
puts pure capacity at three to five chunks.

**In an interface** — The legitimate use concerns what a user must carry *across a boundary*, not
what is on screen. If a confirmation code must be re-typed on the next page, chunk it (XXXX-XXXX,
not XXXXXXXX). If a user must compare a value on step 3 against one shown on step 1, put both on
screen rather than making them hold it. If a wizard requires remembering a prior selection to make
the current one, show the prior selection. Group long numbers and identifiers. That is Miller's
actual result — chunking and recoding — applied where recall is genuinely required.

**Misapplied as** — "Limit menus, navigation bars, or any list of options to 7±2 items."
Structurally this is a category error: a visible menu is a *recognition* task, and short-term
memory capacity does not constrain items that remain on screen. Nielsen ("Short-Term Memory and Web
Usability," NN/g, 6 December 2009): "It's a common misconception that limited short-term memory
implies that menus should be similarly limited to 7 items... It's fine to have longer menus (if
needed), because users don't have to memorize the full list of menu items. The entire idea of a
menu is to rely on recognition rather than recall." Even Laws of UX, the popular vector for the
folklore, gives as its first takeaway: "Don't use the magical number seven to justify unnecessary
design limitations."

A second misapplication: saying seven *items* where Miller said seven *chunks*. That distinction is
the paper's central result, not a footnote.

**Limits** — Miller's own, verbatim. The span of absolute judgment applies to unidimensional
stimuli only, and he flags it: "You may have noticed that I have been careful to say that this
magical number seven applies to one-dimensional judgments." For multidimensional stimuli capacity
rises steeply — "by adding more dimensions and requiring crude, binary, yes-no judgments on each
attribute we can extend the span of absolute judgment from seven to at least 150. Judging from our
everyday behavior, the limit is probably in the thousands, if indeed there is a limit." He warns
against fusing the three spans: "What is more natural than to think that all three of these spans
are different aspects of a single underlying process? And that is a fundamental mistake, as I shall
be at some pains to demonstrate." The two limits are in different currencies: "Absolute judgment is
limited by the amount of information. Immediate memory is limited by the number of items." And he
disowns the number: "Perhaps there is something deep and profound behind all these sevens... But I
suspect that it is only a pernicious, Pythagorean coincidence."

Cowan (2001) then corrects the memory figure: "Miller (1956) summarized evidence that people can
remember about seven chunks in short-term memory (STM) tasks. However, that number was meant more
as a rough estimate and a rhetorical device than as a real capacity limit. Others have since
suggested that there is a more precise capacity limit, but that it is only three to five chunks."
Cowan adds that even 3–5 is observable only under four boundary conditions — information overload
preventing multi-item chunks, explicit blocking of recoding, performance discontinuities, and
indirect effects — so no single number transfers to an uncontrolled real-world task.

---

### The Doherty Threshold

**THE 400 MS FIGURE HAS NO SOURCE IN THE DOCUMENT IT IS CITED TO.** The 1982 Doherty & Thadani
report was read in full and text-searched. The word "millisecond" appears zero times. There is no
threshold concept in it, and the only "400" in the document is "The number of simultaneous users
had grown to almost 400" at NIH. The probe was control-tested first on the same text: "second" 44
hits, "response time" 47, "sub-second" 12 — the search works. No primary source for 400 ms could be
established. Say "sub-second, per Doherty & Thadani 1982", or cite Miller (1968) for tiered
budgets. Do not cite 400 ms to Doherty.

**Statement** — As popularly stated: productivity rises sharply once system response time drops
below 400 ms, because the machine stops making the user wait. What the source actually argues is
*sub-second*, with 0.3 s as its fastest measured condition.

**Provenance** — Doherty, W. J., & Thadani, A. J. (1982). "The Economic Value of Rapid Response
Time." IBM technical report, November 1982. Computer History Museum catalogue no. 102751398 records
it as an IBM document, 12 pages. It is routinely miscited as an *IBM Systems Journal* paper —
lawsofux.com/doherty-threshold reads: "In 1982 Walter J. Doherty and Ahrvind J. Thadani published,
in the IBM Systems Journal, a research paper that set the requirement for computer response time to
be 400 milliseconds, not 2,000 (2 seconds)". Both the venue and the number are wrong. The venue
error appears to conflate three documents: the *Systems Journal* papers are Thadhani, A. J. (1981),
"Interactive user productivity," *IBM Systems Journal*, 20(4), 407–423 — the source of the
transaction-rate curve — and Doherty, W. J., & Kelisky, R. P. (1979), "Managing VM/CMS systems for
user effectiveness," *IBM Systems Journal*, 18(1), 143–163. The 1982 document is a standalone
report.

For perceived-responsiveness budgets the properly sourced citation is Miller, R. B. (1968),
"Response time in man-computer conversational transactions," *AFIPS Fall Joint Computer
Conference*, 33, 267–277, which gives the 0.1 s / 1 s / 10 s tiers.

The earliest traceable popular use of 400 ms is Dave Rupert's blog post of 15 June 2015, which
asserts "a sub-400 millisecond response time creates a dramatic increase in users' interactions at
all different skill levels" and credits the 1982 report.

**Predicts** — Faster system response yields more than proportional gains in user output, because
reduced wait time compounds into reduced user think time. The report's headline: at 3 s response a
programmer executes about 180 transactions per hour; at 0.3 s, 371 per hour — a 106% increase. A
2.7 s reduction in system response saves 10.3 s of the user's time. Its measured ladder is 3.0 s
(180 tx/hr), 2.0 s (208), 1.0 s (252), 0.6 s (279), 0.3 s (371).

**In an interface** — Budget perceived responsiveness as a first-class requirement, using Miller's
(1968) tiers rather than the invented 400 ms: under ~0.1 s reads as instantaneous and needs no
feedback; up to ~1 s preserves flow of thought but should show a state change; beyond ~10 s the
user disengages and you owe a progress indicator with a percentage. Practically: render an
optimistic UI state on tap rather than after the round trip; show skeleton content rather than a
spinner where the layout is known; instrument the real p95, because the mean hides exactly the
cases that break flow.

**Misapplied as** — Citing "400 ms" as an empirical threshold with a 1982 primary source behind it,
and describing sub-400 ms interfaces as "addicting" — a claim that also appears nowhere in the
report. The second misapplication is budgeting response time as though it were the same quantity as
interaction time: Doherty governs how long the *system* takes, Fitts and Hick govern how long the
*user* takes. A 100 ms server response does nothing for a target that takes 1.2 s to acquire.

**Limits** — This is a 1982 IBM vendor document arguing that customers should buy more mainframe
capacity; the conflict of interest is on the face of it. The evidence is uncontrolled field
observation from 1970s–80s VM/CMS timesharing: no control groups, no randomisation, no significance
testing reported. Sample sizes where stated are small — 75 work sessions of 15 engineers at IBM
SPD; five component forecasters for half a day. The tasks are all high-frequency repetitive expert
transaction work (programming, card wiring, parts forecasting), and the claimed mechanism depends
on that: "The traditional model of a person thinking after each system response appears to be
inaccurate. Instead, people seem to have a sequence of actions in mind, contained in a short-term
mental memory buffer." That mechanism does not obviously transfer to exploratory browsing, one-off
tasks, or content consumption, where the user has no queued action sequence to interrupt. The
economic figures ($150,000 per month at 50 concurrent users, rising to $908,000 at 300) assume a
constant $35/hr burdened rate and that saved seconds convert linearly into output. The report
states no caveats of its own.

---

### Tesler's Law (Conservation of Complexity)

**THERE IS NO STUDY BEHIND THIS.** No paper, no experiment, no dataset, no equation. It is a named
practitioner aphorism with good provenance and convergent expert opinion, which is not evidence.
Present it as a heuristic with a named author. Citing it in a list alongside Fitts's law implies
comparable empirical standing and it has none.

**Statement** — Every application has an inherent amount of irreducible complexity; that complexity
cannot be removed by design, only relocated between the user, the application developer, and the
platform developer.

**Provenance** — Larry Tesler, ca. 1984, at Apple. Primary source is Tesler's own site, nomodes.com,
"Tesler's Theorem and other adages and coinages": "Tesler's Law of Conservation of Complexity (ca.
1984). 'Every application has an inherent amount of irreducible complexity. The only question is:
Who will have to deal with it—the user, the application developer, or the platform developer?'"

Published account: Saffer, D. (2006). *Designing for Interaction: Creating Smart Applications and
Clever Devices*. New Riders (ISBN 0321432061), which carries an interview with Tesler describing
his coining it to sell the MacApp object-oriented framework to Apple management and to independent
software vendors. Do not pair that year with the subtitle *Creating Innovative Applications and
Devices* — that is the second edition (2009/2010, ISBN 9780321643391), and the interview is in the
first.

Provenance correction: design sources routinely place this at Xerox PARC. lawsofux writes that the
law's origins "can be traced back to the mid-1980s, when Larry Tesler, a computer scientist at Xerox
PARC, was helping to develop the language of interaction design" — which puts him at PARC in the
mid-1980s. He was not: Tesler was at PARC from 1973 to 1980 and at Apple from July 1980 until 1997
(per Wikipedia; note the IEEE Spectrum obituary of 20 Feb 2020 is often cited for this and does not
in fact give those years — it says only that he "spent nearly two decades at Apple"). His own dating
of ca. 1984 therefore places the formulation at Apple, in the MacApp context, not at PARC.

Unverified: Tesler's page is said to collect independent formulations by Norman (*The Design of
Future Things*, 2007, p. 112: "what is complex in digital representation and computation can only
be simplified at the expense of what is explicitly represented"), Esposito and Colborne.
nomodes.com could not be reached to confirm, and the Wikipedia article that lawsofux gives as its
own source contains no Norman quote at all. Tesler's wording and his ca. 1984 dating were confirmed
independently; the Norman page reference was not. Do not quote it as verified.

**Predicts** — Any simplification of the user's task shows up as work somewhere else: in
engineering effort, in platform capability, or in constrained flexibility. A UI that looks
effortless implies someone absorbed the cases it hides. It also predicts that a "we simplified it"
claim naming no absorber is usually a claim that complexity was hidden rather than moved, and will
resurface as edge-case failure.

**In an interface** — On an onboarding form, do not ask which of four account types the user needs;
infer it from the email domain and the invite, and let engineering own the inference and the
correction path. On a data import, do not require a pre-formatted CSV with exact headers; accept
what the user has, detect the columns, and show a mapping they can override. In both cases the
complexity is real and unchanged — the developer pays it once, and every user stops paying it every
time. When reviewing a spec, ask of each simplification: who absorbed it, and is that written down?
If the answer is nobody, the complexity was hidden, not moved.

**Misapplied as** — An excuse: "complexity is conserved, so this confusing interface is
unavoidable." That inverts the point. The law is a directive about *who* absorbs the work, and the
answer is nearly always the developer, because engineering hours are paid once and user confusion
is paid every session by every user. The second misapplication is presenting it as research.

**Limits** — "Irreducible complexity" is not operationally defined and not measurable, so the law
is unfalsifiable as stated: you cannot compute a system's complexity budget or verify that a design
hit the floor. It claims complexity is conserved, not that it is bounded — bad design routinely
*adds* complexity beyond the irreducible minimum, so the law never licenses the inference "this is
complex, therefore it is inherent." Complexity and difficulty are not the same quantity. And the
trade is not zero-sum in cost even where it is in complexity: moving work to the platform means it
is paid once and amortised across every user, which is precisely why the trade is usually worth
making. The Norman formulation, if the citation holds, is narrower than the popular one — it
applies specifically to what is explicitly represented in a digital system, not to complexity in
general.

---

## Where these laws contradict each other

Cite two of these in one breath and you are often citing a contradiction. The four that matter:

**Hick versus the 7±2 folklore.** They give opposite advice about menu length and are habitually
quoted together to justify the same decision — hiding options. Applied honestly, Hick's law does
not favour truncation at all; the 7±2 folklore says truncate to seven, and rests on nothing. An
agent citing both to support "show fewer" is citing a contradiction on top of a misquote.

**Hick versus Fitts on flat-versus-nested.** Hick's law, correctly applied, is indifferent between
a flat list and a categorised split — the maths makes them the limit case of each other. Fitts's
law penalises the flat layout, because a longer list means greater average pointer distance and, if
density rises to compensate, smaller targets. Neither law settles the trade. The resolution comes
from visual search cost, which neither of them models.

**Doherty versus Fitts and Hick on "performance".** They budget different quantities that get
conflated in one conversation. Doherty governs system response time; Fitts and Hick govern
user-side interaction time. A team that optimises only the first ships an app that feels fast and
is slow to use.

**Fitts against itself across input devices.** On a mouse, edges and corners are the fastest targets
on screen. On a touchscreen, NN/g (2022) reports edge placement offers no advantage and edge targets
can take longer. Name the pointer before applying the law.

---

## Sources

Primary sources, read directly unless marked.

- Fitts, P. M. (1954). The information capacity of the human motor system in controlling the amplitude of movement. *Journal of Experimental Psychology*, 47(6), 381–391. [read in full]
- Fitts, P. M., & Peterson, J. R. (1964). Information capacity of discrete motor responses. *Journal of Experimental Psychology*, 67, 103–112.
- MacKenzie, I. S. (1992). Fitts' law as a research and design tool in human-computer interaction. *Human–Computer Interaction*, 7(1), 91–139.
- MacKenzie, I. S. (2018). Fitts' Law. In *The Wiley Handbook of Human Computer Interaction*, ch. 17.
- MacKenzie, I. S., & Buxton, W. (1992). Extending Fitts' law to two-dimensional tasks. *Proc. CHI '92*, 219–226.
- Bi, X., Li, Y., & Zhai, S. (2013). FFitts law: Modeling finger touch with Fitts' law. *Proc. CHI 2013*, 1363–1372.
- ISO 9241-9:2000, renumbered ISO 9241-411:2012 — standard method for Fitts-based input device evaluation.
- Hick, W. E. (1952). On the rate of gain of information. *Quarterly Journal of Experimental Psychology*, 4(1), 11–26.
- Hyman, R. (1953). Stimulus information as a determinant of reaction time. *Journal of Experimental Psychology*, 45(3), 188–196.
- Proctor, R. W., & Schneider, D. W. (2018). Hick's law for choice reaction time: A review. *Quarterly Journal of Experimental Psychology*, 71(6), 1281–1299.
- Liu, W., Gori, J., Rioul, O., Beaudouin-Lafon, M., & Guiard, Y. (2020). How relevant is Hick's law for HCI? *Proc. CHI 2020*. DOI 10.1145/3313831.3376878. [read in full]
- Landauer, T. K., & Nachbar, D. W. (1985). Selection from alphabetic and numeric menu trees using a touch screen: Breadth, depth, and width. *Proc. CHI '85*, 73–78.
- Seow, S. C. (2005). Information theoretic models of HCI: A comparison of the Hick-Hyman law and Fitts' law. *Human–Computer Interaction*, 20(3), 315–352.
- Miller, G. A. (1956). The magical number seven, plus or minus two. *Psychological Review*, 63(2), 81–97. [read in full]
- Cowan, N. (2001). The magical number 4 in short-term memory. *Behavioral and Brain Sciences*, 24(1), 87–114.
- Miller, R. B. (1968). Response time in man-computer conversational transactions. *AFIPS Fall Joint Computer Conference*, 33, 267–277.
- Doherty, W. J., & Thadani, A. J. (1982, November). The Economic Value of Rapid Response Time. IBM technical report, CHM cat. 102751398. [read in full and text-searched]
- Thadhani, A. J. (1981). Interactive user productivity. *IBM Systems Journal*, 20(4), 407–423.
- Doherty, W. J., & Kelisky, R. P. (1979). Managing VM/CMS systems for user effectiveness. *IBM Systems Journal*, 18(1), 143–163.
- Tesler, L. Tesler's Theorem and other adages and coinages. nomodes.com. [not reachable at time of check; wording confirmed independently]
- Saffer, D. (2006). *Designing for Interaction: Creating Smart Applications and Clever Devices*. New Riders.
- Nielsen, J. (2009, 6 December). Short-Term Memory and Web Usability. Nielsen Norman Group.
- Budiu, R. (2022, 31 July). Fitts's Law and Its Applications in UX. Nielsen Norman Group.
- Rupert, D. (2015, 15 June). The Economic Value of Rapid Response Time. daverupert.com. [cited as the origin of the 400 ms folklore, not as authority]
- Laws of UX, lawsofux.com. [cited as the popular vector, not as authority — its Doherty page miscites the venue and the number; its Miller page correctly warns against the 7±2 misuse]
