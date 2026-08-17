# Gestalt grouping and figure–ground

What each grouping principle actually claims, who established it, what it predicts in an interface, and the conditions under which it stops holding.

Palmer, who introduced common region, disclaims the word "law" in a footnote to the paper that did it:

> "I hereafter refer to the 'laws' of grouping more modestly as 'principles' or 'factors' of grouping because they lack the quantitative structure of standard scientific 'laws'."
> — Palmer 1992, p. 438, n. 1

Every principle below is a *ceteris paribus* rule: a claim about what happens when nothing else varies. Wertheimer's 1923 paper contains no participants, no measurements and no statistics — it asks the reader to look at dot patterns and agree. Where a principle has since been measured, the measurement is given.

## Contents

- [Who established what](#who-established-what)
- [Principles](#principles)
  - [Proximity](#proximity)
  - [Similarity](#similarity)
  - [Common fate](#common-fate)
  - [Good continuation](#good-continuation)
  - [Closure](#closure)
  - [Prägnanz (good Gestalt)](#prägnanz-good-gestalt)
  - [Symmetry and parallelism](#symmetry-and-parallelism)
  - [Figure/ground](#figureground)
  - [Common region](#common-region)
  - [Uniform connectedness](#uniform-connectedness)
  - [Element connectedness](#element-connectedness)
  - [Synchrony](#synchrony)
  - [Past experience and attention](#past-experience-and-attention)
- [Where the principles conflict](#where-the-principles-conflict)
- [Sources](#sources)

## Who established what

Design writing attributes the whole set to Wertheimer or to "the Gestalt psychologists". Five of them are not his, and one is not even Gestalt.

| Principle | Established by |
|---|---|
| Proximity, similarity, common fate, good continuation, closure, symmetry, Prägnanz | Wertheimer 1923 |
| Figure/ground | **Edgar Rubin 1915** — Danish, not a Gestalt psychologist, and sceptical of the Berlin school |
| Configural figure–ground cues (convexity, symmetry, small area, surroundedness) | Rubin 1915 and Harrower 1936 |
| Common region | **Stephen Palmer 1992** |
| Uniform connectedness, element connectedness | **Palmer & Rock 1994** |
| Synchrony | **Alais, Blake & Lee 1998** |

Two further citation notes. The English Wertheimer everyone reads is Ellis's 1938 abridgement — 50 pages of German reduced to 18, with material omitted, including Wertheimer's own hedge on common fate. Anyone citing "Wertheimer 1923" from the English is citing an abridgement. And "the whole is greater than the sum of its parts" is a misquotation: Koffka wrote "something else than", not "greater than". The page usually given for it (Koffka 1935, p. 176) could not be verified against the text and should not be reproduced.

## Principles

### Proximity

**Not supported by the research: the absolute-pixel version — "8px means related, 24px means separate".** Grouping strength is a function of the *ratio* between competing distances and is invariant under scaling, so an absolute distance carries no prediction at all on its own.

**Statement** — All else being equal, elements nearer to one another group together, and the strength of that grouping is a function of the ratio of competing distances, not of their absolute size.

**Provenance** — Max Wertheimer, "Untersuchungen zur Lehre von der Gestalt II", *Psychologische Forschung* 4 (1923): 301–350; "The Factor of Proximity" in the partial English translation by Willis D. Ellis, *A Source Book of Gestalt Psychology* (London: Routledge & Kegan Paul, 1938), pp. 71–88. First measured by Tadasu Oyama, "Perceptual grouping as a function of proximity", *Perceptual and Motor Skills* 13 (1961): 305–306 — a power function with exponent ≈ 2.89. Quantified by Michael Kubovy, Alex O. Holcombe & Johan Wagemans, "On the lawfulness of grouping by proximity", *Cognitive Psychology* 35, no. 1 (1998): 71–98.

**Predicts** — A row of otherwise identical elements splits at its largest gaps. Kubovy et al. measured this on multistable dot lattices: grouping strength approximates a decreasing exponential (or power) function of *relative* distance, and, verbatim from the abstract, "The configural or wholistic properties that were varied — such as angular separations of the alternative organizations and the symmetry properties of the dot pattern — do not matter" and "this grouping function is robust under transformations of scale in space (Experiment 1) and time (Experiment 2)." Wagemans et al. (2012, p. 1184) give the threshold: "If the ratio of the longer to the shorter vector is larger than about 1.5, grouping along that orientation is almost never seen." This scale invariance is the strongest genuinely predictive result in the family.

**In an interface** — Spacing is a ratio system, not a pixel system. 16px between fields against 40px between sections is 2.5:1 and groups decisively; 24px against 32px is 1.33:1 and leaves the grouping near-bistable, so users parse the same form differently on different visits. Because the effect is scale-invariant, a spacing scale that *multiplies* across breakpoints preserves grouping, while one that adds a fixed offset ("+8px everywhere on desktop") compresses every ratio toward 1 and dissolves the structure it was meant to protect.

**Misapplied as** — A defence of an absolute number. The 8/24 rule works because it is 3:1, and it stops working the instant a neighbouring group uses a different base — which the absolute framing makes invisible. The second misuse is running it backwards: a card grid ships with 12px title-to-body, 16px body-to-meta and 20px card-to-card, and the review calls it "grouping by proximity". Applied forward, the same principle predicts failure — 20/16 is 1.25, well under the ~1.5 at which one organisation dominates.

**Limits** — The distance law was measured on multistable dot lattices near equilibrium, shown for 300 ms, with observers picking one of four orientations. Interface gaps are not competing lattice vectors and reading is not a 300 ms forced choice; the 1.5 ratio is a real measurement inside that paradigm and an extrapolation outside it. Separately, Rock & Brosgole, "Grouping based on phenomenal proximity", *Journal of Experimental Psychology* 67 (1964): 531–538, showed proximity operates on **perceived (3-D) distance, not retinal distance** — so a modal or a floating card on a nearer depth plane does not group with what sits visually adjacent behind it.

### Similarity

**Statement** — All else being equal, elements matching on a feature dimension — lightness, colour, size, shape, orientation — group with each other rather than with non-matching neighbours at the same spacing.

**Provenance** — Wertheimer 1923 (Ellis trans. 1938, pp. 71–88): "the tendency of like parts to band together — which we may call The Factor of Similarity." Quantified for luminance-contrast similarity by Michael Kubovy & Martin van den Berg, "The whole is equal to the sum of its parts: A probabilistic model of grouping by proximity and similarity in regular patterns", *Psychological Review* 115, no. 1 (2008): 131–154.

**Predicts** — A row of evenly spaced alternating filled and open dots is seen as pairs of like dots despite uniform spacing — grouping with no distance cue at all. Wagemans et al. (2012, p. 1190): elements with similar brightness, contrast, colour or texture are more likely to group than elements differing on those dimensions.

**In an interface** — Colour carries grouping across distances proximity cannot reach: every destructive control in one hue reads as one set wherever the controls sit in a toolbar. In a long table, a shared cell tint holds a column together across a scroll. In a nav, one weight for secondary items and another for primary separates them without moving anything.

**Misapplied as** — One dial rather than a set of independent, unequally strong dimensions. Design decks routinely assert that similarity of colour, shape and size are interchangeable; no study establishes that. Elder & Goldberg (2002), on the ecological statistics of edge grouping, found brightness carries useful grouping information while the contrast cue is comparatively weak.

**Limits** — The clean quantitative result is for luminance-contrast similarity in dot lattices at 300 ms. Wagemans et al. (2012, p. 1190) report that for oriented elements, similarity shows "nonadditive interactions with other grouping cues such as proximity and good continuation" — so the additivity result below does not generalise to similarity as a whole.

### Common fate

**Statement** — All else being equal, elements that change together over time — classically, that move in the same direction at the same rate — are grouped together.

**Provenance** — Wertheimer 1923: "The Factor of Uniform Destiny (or of Common Fate)." Extended beyond motion by Allison B. Sekuler & Patrick J. Bennett, "Generalized common fate: Grouping by common luminance changes", *Psychological Science* 12 (2001): 437–444.

**Predicts** — A subset of elements sharing a motion vector segregates from a static or incoherently moving field even when spatially intermixed. Sekuler & Bennett showed the same for luminance: elements that brighten or darken together group even when their absolute luminances differ throughout. Wagemans et al. (2012, p. 1181) characterise the mechanism as "another example of similarity grouping, but based on similarity of changes in feature values ... rather than on the similarity of the feature values themselves."

**In an interface** — A staggered list reveal in which one section's items share an entrance direction and easing while the next arrives from a different origin makes the section boundary legible before any border or spacing does. Skeleton placeholders pulsing in lockstep read as one loading block; independently phased pulses read as separate pending things.

**Misapplied as** — Licence for motion that shares only *timing*, not direction. That is synchrony — a separate and much weaker principle with an entirely different evidence base. The second misuse is treating common fate as a universal override; it has documented failures, including a negligible effect on numerosity discrimination between coherently and incoherently moving sets.

**Limits** — Evidence comes from dense element fields with coherent motion, not from two or three UI objects easing in over 200 ms. Wertheimer hedged it himself, in a passage cut from the Ellis translation that most designers read: "Also this principle [of common fate] is valid in a wide range of conditions; how wide is not yet investigated here" (Wertheimer 1923, p. 316; translated in Wagemans et al., 2012, p. 1181).

### Good continuation

**Not supported by the research: "good continuation is why alignment matters".** What Field et al. measured is the *orientation* of elements along a path, not the flushness of their edges, and nothing in this literature says a user notices a 2px misalignment.

**Statement** — All else being equal, elements are grouped so that the resulting contour continues smoothly rather than turning abruptly.

**Provenance** — Wertheimer 1923: "The Factor of the 'Good Curve'" and "The Factor of Direction." Quantified by David J. Field, Anthony Hayes & Robert F. Hess, "Contour integration by the human visual system: Evidence for a local 'association field'", *Vision Research* 33 (1993): 173–193.

**Predicts** — An X of two crossing arcs is seen as two smooth lines, not four segments meeting at a vertex. Field et al. embedded a path of oriented Gabor elements in a random field of distractors at matched density, eliminating proximity as a cue: aligning the elements tangentially to the path made it easily detected, randomising their orientations made it invisible. That is good continuation isolated from proximity, measured.

**In an interface** — A left-aligned column of labels holds as one vertical structure across gaps far too large for proximity, which is why breaking alignment for a single item costs disproportionate attention. A stepper's connecting rule integrates the steps into one path in a way numbered circles alone do not.

**Misapplied as** — A scientific warrant for alignment in general. A shared left edge is a production convention that happens to be useful; calling it good continuation borrows authority the finding does not extend.

**Limits** — Measured at detection threshold with Gabor patches in noise. It establishes that the visual system can integrate an oriented path out of clutter. It says nothing about preference, aesthetics, or suprathreshold judgments of tidiness.

### Closure

**Not supported by the research: "the mind fills in the gaps, so an incomplete shape reads as complete", and the related claim that closed contours are easier to detect.** Tversky, Geisler & Perry (2004) ran five experiments controlling for uncertainty, eccentricity and element density: "In four of the experiments, we found that closed contours were no easier to detect than open contours, and in the remaining experiment the effects were consistent with the predictions of probability summation." That is a claim about *mechanism* — closure effects are largely explained by good continuation and proximity — not a finding that closure fails to group. Closure remains a grouping principle; Wagemans et al. (2012, p. 1180) present it as one, noting it can dominate continuity, and Palmer (1992, p. 446) refers to "the well-known principles of grouping by closure and proximity".

**Statement** — A line forming a closed or nearly closed figure stops being seen as a line and becomes a bounded surface — a figure with an inside and an outside.

**Provenance** — Wertheimer 1923: "The Factor of Closure." The precise formulation is Kurt Koffka's, *Principles of Gestalt Psychology* (London: Lund Humphries / New York: Harcourt, Brace, 1935), p. 150: "Ordinary lines, whether straight or curved, appear as lines and not as areas. They have shape, but they lack the difference between an inside and an outside... If a line forms a closed, or almost closed, figure, we see no longer merely a line on a homogeneous background, but a surface figure bounded by the line." The detectability refutation is T. Tversky, Wilson S. Geisler & Jeffrey S. Perry, "Contour grouping: closure effects are explained by good continuation and proximity", *Vision Research* 44, no. 24 (2004): 2769–2777.

**Predicts** — Closure converts a 1-D contour into a 2-D shape that can own a background and contain things. It does not predict a detectability advantage.

**In an interface** — A 1px border turns a card into a surface: it can take a fill, cast a shadow, own a depth plane, and contain elements. The same content bracketed by a rule above and below stays a band of text, and behaves differently under scroll and reflow. This is the real, defensible reason bordered containers are not interchangeable with separator-delimited sections.

**Misapplied as** — Justification for logos with dropped strokes and icon sets with broken outlines, on the gap-filling story. A broken-outline icon set may still be a good decision on distinctiveness or brand grounds, but the closure citation is decoration on a taste judgment, not evidence.

**Limits** — Closure's demonstrated role is in figure and shape formation, not in detectability and not in gap-filling. Wagemans et al. (2012, p. 1190) put the classical claim precisely: "The original Gestalt claim was thus not that closure is a grouping cue per se, but rather that it somehow profoundly determines the final percept of form." Elder & Zucker (1993, 1994) place its value as a bridge from 1-D contour to 2-D shape — a much narrower claim than the design canon makes.

### Prägnanz (good Gestalt)

**Not supported by the research: "users prefer simple, clean designs" and "reduce visual complexity".** The original is a claim about how *ambiguous stimuli resolve* — which of several possible organisations a pattern settles into — not about aesthetic preference, cognitive load, or the merits of removing features. It was never operationalised, and no layout decision can be derived from it.

**Statement** — The perceptual field organises itself into the simplest, most stable, most encompassing structure the prevailing conditions permit.

**Provenance** — Wertheimer 1923 (*Prägnanzstufen*, "regions of figural stability"; the Ellis translation notes the term as untranslatable). Physical-systems framing in Wolfgang Köhler, *Die physischen Gestalten in Ruhe und im stationären Zustand* (Braunschweig: Vieweg und Sohn, 1920). Koffka's formulation, *Principles of Gestalt Psychology* (1935), p. 110: "psychological organization will always be as 'good' as the prevailing conditions allow."

**Predicts** — As stated, nothing testable. Wertheimer's own defence is circular: "on the whole the reader should find no difficulty in seeing what is meant here... One recognizes a resultant 'good Gestalt' simply by its own 'inner necessity'" (1923/1938, p. 83). Wagemans et al. (2012, p. 1206) record that Prägnanz was proposed "to avoid a proliferation of laws" as the master law subsuming the others, "but its formulation was left intentionally vague."

**In an interface** — Nothing follows from the principle itself. Where "simplify the interface" is a good argument it rests on independent grounds — fewer decisions, shorter scan paths, less state to get wrong, less code to break. Make those arguments on their own evidence.

**Misapplied as** — The most abused item in the family, cited across design writing as a preference law. "Good" and "simple" are undefined without a specified coding scheme, and different formalisations give different answers for the same display. Gary Hatfield & William Epstein, "The status of the minimum principle in the theoretical analysis of visual perception", *Psychological Bulletin* 97 (1985): 155–186, is the standing examination of whether a minimum principle can carry this weight.

**Limits** — Köhler's physical-field grounding collapsed when Lashley's and Sperry's experiments removed its empirical basis, and no replacement was found (Wagemans et al., 2012, p. 1206). Do not cite Prägnanz to justify a layout decision.

### Symmetry and parallelism

**Statement** — All else being equal, symmetric or parallel elements are grouped together and are more likely to be seen as a coherent figure.

**Provenance** — Wertheimer 1923 listed symmetry, equilibrium and closure among the *Ganzeigenschaften* (whole-properties); Koffka (1935) identified symmetry as a factor of good shape. Parallelism was named as a determinant of perceptual simplicity by Rudolf Arnheim (1967). Psychophysical evidence: Jacob Feldman (2007) found feature comparison across pairs of line segments is significantly faster when the segments are parallel or mirror-symmetric.

**Predicts** — Symmetric regions and parallel segments are grouped and preferentially assigned figure status, measurable as a speed advantage in comparison tasks.

**In an interface** — A symmetric pair of actions (Cancel / Confirm) mirrored about a centre line reads as one decision unit rather than two independent controls. Parallel rules or parallel column edges hold a table's structure when tint and spacing are both unavailable.

**Misapplied as** — A strong grouping force. Kanizsa (*Organization in Vision*, 1979) found symmetry "seems to be easily overruled by good continuation and convexity" (Wagemans et al., 2012, p. 1190). Kanizsa & Gerbino (1976) pitted global symmetry directly against convexity in figure–ground assignment and convexity won. Symmetry is a weak cue that design writing routinely elevates.

**Limits** — Weak relative to good continuation and convexity. The psychophysical evidence is a reaction-time advantage in feature comparison, not a demonstration that symmetric layouts are better understood.

### Figure/ground

**Not supported by the research: the negative-space folklore — that hidden figures in negative space convey meaning unconsciously.** Ke, Gupta, Lo, Ting & Tseng (2023) ran four experiments across North American and Taiwanese samples using a Posner orienting paradigm and found no cue congruency effect unless the arrow was explicitly highlighted, concluding that people do not unconsciously perceive the FedEx arrow to the point of producing an attentional effect. That is the one study that tested the claim directly.

**Statement** — Where two regions share a border, the border is normally assigned to one of them; that region is seen as a shaped figure lying in front, and the other appears to continue behind it, receiving no shape from the shared edge.

**Provenance** — **Edgar Rubin**, *Synsoplevede Figurer* / *Visuell wahrgenommene Figuren: Studien in psychologischer Analyse* (Copenhagen: Gyldendalske Boghandel, 1915), a doctoral thesis defended at the University of Copenhagen in July 1915. This is not a Berlin-school contribution. Rubin was Danish, did not consider himself a Gestalt psychologist, and was sceptical of the Gestaltists' attempt to explain diverse phenomena within one overarching framework, pursuing a descriptive ("aspective") psychology instead; the Gestaltists adopted his distinction. The classic configural cues — convexity, symmetry, small area, surroundedness — trace to Rubin (1915) and Harrower (1936). The negative-space study is Shih-Chiang Ke, Ankit Gupta, Yu-Hui Lo, Chih-Chung Ting & Philip Tseng, "The hidden arrow in the FedEx logo: Do we really unconsciously 'see' it?", *Cognitive Research: Principles and Implications* 8, no. 1 (2023), Article 40, doi:10.1186/s41235-023-00494-x (PMID 37395853).

**Predicts** — Border ownership and the asymmetry of shape: the ground is shapeless at the shared edge. Where cues are balanced, the assignment reverses over time — Rubin's vase/faces figure. Palmer & Brooks (2008) tested six grouping factors — common fate, blur similarity, colour similarity, orientation similarity, proximity and flicker synchrony — as figure–ground factors and found all six produced figure–ground effects in the predicted direction, "albeit to widely varying degrees" (Wagemans et al., 2012, p. 1196). Grouping and figure–ground are not separate systems.

**In an interface** — A modal scrim makes the dialog the figure and the page behind it ground, which is why users stop parsing the page rather than merely finding it dim. A shadowed tooltip owns its edge; the same tooltip with a hairline border in a near-identical tone competes for ownership and reads as a cut-out. Reversible figure/ground is the failure mode behind ambiguous empty states, where neither the container nor its background is clearly in front.

**Misapplied as** — Two errors. First, provenance: attributing it to Wertheimer or "the Gestalt psychologists". Second, the negative-space claim above.

**Limits** — The critical limit for interfaces. Mary A. Peterson & Elizabeth Salvagio, "Inhibitory competition in figure–ground perception: context and convexity", *Journal of Vision* 8, no. 16 (15 December 2008), Article 4, found that for a *single* edge "there is only a weak bias toward seeing the figure on the convex side" — roughly 57% of trials in two-region displays, rising to ~89% only with eight alternating regions, and only when the concave regions were homogeneous in colour. The classic demonstrations used many alternating regions and long exposures. Wagemans et al. (2012, p. 1201): "when studied in more controlled experiments, the classic configural principles turn out weaker than previously supposed." A UI is almost always the two-region case — one card on one background — which is the condition where the effect is weakest.

### Common region

**Statement** — All else being equal, elements located within a common region of space — a connected, homogeneously coloured or textured region, or an enclosing contour — are perceived as grouped.

**Provenance** — **Stephen E. Palmer**, "Common Region: A New Principle of Perceptual Grouping", *Cognitive Psychology* 24, no. 3 (1992): 436–447. Not Wertheimer; 1992, not 1923. Palmer's own statement (p. 438): "The proposed principle of common region states that, all else being equal, elements will be perceived as grouped together if they are located within a common region of space, i.e., if they lie within a connected, homogeneously colored or textured region or within an enclosing contour." Confirmed with reaction times fifteen years later using the repetition discrimination task (Beck & Palmer, 2002; Palmer & Beck, 2007).

**Predicts** — An enclosing contour overrides both proximity and similarity in Palmer's demonstrations (Figs. 2C, 2D). Dashed and even illusory contours suffice (Figs. 2E, 2F). Common region operates *after* stereoscopic depth perception: Palmer's Fig. 3 transparency demonstration shows dots grouping with the coplanar enclosing ellipses, not the retinally nearer ones. It is dominated by the smallest enclosing region and nests hierarchically.

**In an interface** — Palmer's own example is a design one (p. 445): two placards carrying the identical four words STOP / WAR / PEACE / NOW, grouped by common region into rows on one and columns on the other — "The effect on the perceived meaning of these two political placards, however, is profound." In a product: a card background groups a heading, a chart and a footnote that whitespace alone cannot, and a tinted fieldset survives a responsive reflow that destroys a proximity-only grouping.

**Misapplied as** — A border or fill added to "make it a group" when the container cuts across the content's own structure. Common region is strong enough to impose a false grouping that proximity and similarity cannot undo. And because it operates after depth, an elevated card and a flat tint are not interchangeable: a shadow puts the surface on a nearer plane and changes what groups with what, which is exactly what Palmer's Fig. 3 demonstrates. This is also the most commonly misattributed item in the family — the Laws of UX "Law of Common Region" page cites NN/g, Smashing Magazine, Scholarpedia and Wikipedia, and does not cite Palmer 1992 at all.

**Limits** — Palmer's original evidence is phenomenological demonstration, by his own admission (p. 446): "I have argued on phenomenological grounds that common region is an effective factor in perceptual grouping using the same type of arguments that Wertheimer (1923) employed in his original paper." He explicitly refuses the dominance claim made on his behalf (p. 439): "... not mean that common region will always dominate other grouping factors, however. The outcome clearly depends on the number and strength of other factors that oppose it."

### Uniform connectedness

**Not supported by the research: listing it alongside proximity and similarity as a co-equal grouping cue**, which almost every design summary does. Palmer & Rock's entire argument is that it operates at a prior stage; treating it as one more cue in the trade-off inverts the claim. The staged model is itself contested — see Limits.

**Statement** — Before any grouping occurs, the visual system partitions the image into mutually exclusive connected regions of uniform (or smoothly changing) luminance, colour, texture, motion and depth; those regions are the entry-level units on which grouping then operates.

**Provenance** — Stephen E. Palmer & Irvin Rock, "Rethinking perceptual organization: The role of uniform connectedness", *Psychonomic Bulletin & Review* 1, no. 1 (1994): 29–55.

**Predicts** — Not a grouping principle at all, but a claim about what precedes grouping. Wertheimer 1923 never said where the to-be-grouped elements came from; uniform connectedness supplies them. Palmer & Rock showed its effects persist even when opposed by proximity and similarity, and argued it cannot be reduced to grouping because it is not grouping.

**In an interface** — A solid pill button is one unit; the same label with an icon beside it and an underline is three units that grouping then has to reassemble. This is the perceptual argument for filled chips, solid tags and contiguous segmented controls over assemblies of adjacent parts, and why a single filled target is more robustly one thing than a visually tight cluster of separate ones.

**Misapplied as** — See the warning above.

**Limits** — Contested. Mary A. Peterson, "The proper placement of uniform connectedness", *Psychonomic Bulletin & Review* (1994), argued that uniform connectedness is one of many properties relevant to partitioning and that its units are not entry-level units. Ruth Kimchi (2000), using primed matching to trace the microgenesis of organisation, obtained results inconsistent with the entry-level claim. Wagemans et al. (2012, p. 1182): "Palmer and Rock's (1994) claims regarding the foundational status of UC have not been uniformly accepted."

### Element connectedness

**Statement** — All else being equal, distinct elements that share a common border — that are physically connected — are grouped together.

**Provenance** — Palmer & Rock, "Rethinking perceptual organization: The role of uniform connectedness", *Psychonomic Bulletin & Review* 1, no. 1 (1994): 29–55. Measured by Palmer & Beck (2007) with the repetition discrimination task: connected displays produced reliably faster responses than unconnected ones.

**Predicts** — Connectedness overrides proximity: two touching elements group even when a third is nearer. Palmer & Rock argue the ranking question is itself confused — you need distinct units before you can meaningfully speak of the distance between them, so connectedness is prior rather than merely stronger. Humphreys & Riddoch (1993) reported a Balint's syndrome patient who could not discriminate one-colour from two-colour circle arrays but succeeded when red/green pairs were joined by a connecting line.

**In an interface** — A segmented control whose segments share edges is one control; introduce 4px gaps and it becomes three buttons that happen to sit near each other. A connecting rail in a tree view or a stepper does work no amount of spacing can do. Conversely, an accidental hairline between two unrelated blocks welds them.

**Misapplied as** — Drawing a connector to imply a relationship the underlying model does not have. Because connectedness overrides proximity, a stray rule creates a group whitespace cannot dissolve — the fix is to remove the connector, not to add space, and teams routinely try the latter first.

**Limits** — Same *ceteris paribus* caveat as the rest. The strong demonstrations use simple arrays of identical elements, and the reaction-time confirmation is a speeded discrimination task, not a comprehension measure.

### Synchrony

**Not supported by the research.** This is the weakest principle in the family and the one most often invoked to justify UI motion, because timing is the easiest thing to share across components. Wagemans et al. (2012, p. 1181): "the bottom line is that both the existence of grouping [by] synchrony and the mechanism by which it occurs are currently unclear." Do not cite it as settled science in a motion spec.

**Statement** — Elements that change at the same time are grouped together, even when the changes are in different directions or on different feature dimensions.

**Provenance** — **David Alais, Randolph Blake & Sang-Hun Lee**, "Visual features that vary together over time group together over space", *Nature Neuroscience* 1, no. 2 (June 1998): 160–164; and S.-H. Lee & Blake (1999). Critique: Hany Farid & Edward H. Adelson, "Synchrony does not promote grouping in temporally structured displays", *Nature Neuroscience* (2001), and Farid, "Temporal synchrony in perceptual grouping: A critique" (2002), who argue the reported effects are stimulus artifacts detectable by the early visual system.

**Predicts** — A field of black and white dots randomly flipping polarity segregates into two regions where a subset flips synchronously rather than randomly. Unlike common fate, no shared direction of change is required — only simultaneity.

**In an interface** — Co-timed state changes across separated regions: several fields validating at the same instant, or a set of tiles refreshing on the same tick, read as one system responding rather than several independent things. Treat this as a hypothesis to test, not a rule to build on.

**Misapplied as** — A citation for shared animation timing, and as a substitute for common fate. The two have entirely different evidence bases; common fate requires a shared direction of change and has one.

**Limits** — The ecological rationale is weak in the reviewers' own words (Wagemans et al., 2012, p. 1181): "Objects in the natural environment seldom change their properties in different directions or along different dimensions in temporal synchrony. Indeed, it is difficult even to devise plausible examples."

### Past experience and attention

**Not supported by the research: the innateness claim — that grouping is preattentive, universal and learning-independent, and therefore that a "Gestalt-correct" layout needs no testing.** Wertheimer set two criteria that evidence for past-experience effects would have to satisfy; experiments that satisfy both have since found the effects. The literature that founded the principles asserted innateness, and the literature that tested it, on the founders' own criteria, found otherwise.

**Statement** — Past experience and attention influence perceptual organisation, including figure–ground assignment; grouping is not a fixed, early, learning-independent property of the image.

**Provenance** — Wertheimer 1923 (Ellis trans. 1938) named "the Factor of past experience or habit" and set two criteria (p. 86): "(1) that the dominant apprehension [perception] was due to earlier experience (and to nothing else); (2) that nondominant apprehensions in each instance had not been previously experienced." Refuted on his own terms by B. S. Gibson & M. A. Peterson (1994), Peterson & Gibson, and Ruth Kimchi & Batsheva Hadad, "Influence of past experience on perceptual grouping", *Psychological Science* 13 (2002): 41–47.

**Predicts** — The modern finding reverses the classical one. Wagemans et al. (2012, p. 1207): "these findings from studies that satisfy both of Wertheimer's (1923) criteria show that past experience can exert an influence on several aspects of figure–ground perception," and in summary (p. 1201): "the role of past experience and attention has now been clearly demonstrated in experiments that satisfy Wertheimer's own criteria." Grouping is also not confined to early vision: "Rather than being primary, in the sense of preattentive and early, principles of grouping seem to operate at multiple levels" (p. 1207); see also Stephen E. Palmer, "Perceptual grouping: It is later than you think", *Current Directions in Psychological Science* 11 (2002): 101–106.

**In an interface** — Grouping is not a fixed property of your pixels. A returning user groups your layout differently from a first-time user, and learned convention — a cluster top-right is "account controls" — can beat geometry. Attention modulates figure–ground assignment, so where the user is looking changes what is figure. The same layout therefore produces different groupings in different populations: grouping must be tested, and tested with the population you are shipping to.

**Misapplied as** — The most consequential misuse in the family: skipping usability testing because "the layout is Gestalt-correct". An agent citing Gestalt principles as a substitute for evidence about real users is citing a claim that has been specifically refuted.

**Limits** — The refutation is strongest for figure–ground organisation, where Wertheimer's two criteria have been directly satisfied; the evidence for past-experience effects on classical grouping (Kimchi & Hadad 2002) is real but narrower. Do not overstate in the other direction either — image-based cues still do most of the work most of the time.

## Where the principles conflict

**Proximity vs similarity — they add, they do not rank.** Kubovy & van den Berg (2008) presented rectangular dot lattices in which contrast similarity ran either along or against the short axis and obtained grouping indifference curves that are parallel in log-odds space: the conjoint effect equals the sum of the separate effects. Claessens & Wagemans (2005) found the same for proximity and collinearity. So a weaker colour distinction can be bought back with a larger distance ratio, and vice versa; if the two oppose at equal strength the grouping is genuinely bistable and different users will parse it differently. Caveat: additivity was measured for luminance-contrast similarity in dot lattices at 300 ms, and Wagemans et al. (2012, p. 1190) report non-additive interactions between similarity and proximity or good continuation for oriented contour elements. It is not a general law of cue combination.

**Common region vs proximity and similarity — no general resolution exists.** Palmer (1992) demonstrated an enclosing contour overriding both, and NN/g repeats this as a boundary that "can overpower other grouping principles". Palmer refuses the general claim on the next page (p. 439): "Like all other principles of grouping, the proposed factor of common region is a ceteris paribus rule... When the principles are applied to complex cases in which two or more factors vary in opposition, there is (as yet) no way to predict the outcome." That sentence is still the state of the art for anything richer than a dot lattice. Any ranking table of which principle beats which is invented.

**Element connectedness vs proximity — resolved by precedence, not strength.** Connectedness wins in Palmer & Rock's demonstrations, but they argue the contest is malformed: proximity presupposes distinct units, and connectedness is what creates or destroys unit boundaries. Decide connectivity first (is this one object or several?), then spacing. This is why adding whitespace never fixes an accidental connecting rule.

**Uniform connectedness vs everything else — staged, and disputed.** Palmer & Rock resolve it by ordering rather than competition: uniform connectedness runs first and defines the elements grouping then operates on, so it is never in the trade-off. Peterson (1994) and Kimchi (2000) dispute that. Currently unresolved; do not treat the staged model as settled.

**Static vs dynamic figure–ground cues — dynamic cues win.** Kanizsa & Gerbino (1976) pitted global symmetry against convexity and convexity won. Barenholtz & Feldman (2006) showed articulating (hinging) motion overrides both convexity and symmetry where they predict opposite assignments. Barenholtz & Tarr (2009) showed an advancing region's motion overpowers the classic small-area factor. For interfaces: a transition that implies articulation or advance reassigns figure and ground regardless of how the static composition was designed.

**Grouping vs figure–ground — not separate systems.** Palmer & Brooks (2008) tested six grouping factors as figure–ground factors and all six produced figure–ground effects in the predicted direction, "albeit to widely varying degrees" (Wagemans et al., 2012, p. 1196). A change made to fix grouping also shifts figure–ground assignment: adding a tint to group three items also decides which plane they sit on.

**Prägnanz vs the specific factors — it arbitrates nothing.** Prägnanz was proposed precisely as the master law that would subsume the others "to avoid a proliferation of laws" (Wagemans et al., 2012, p. 1206). It was left too vague to adjudicate anything, which is why the conflict problem stayed open for a century.

**The structural conflict underneath all of them.** Wagemans et al. (2012, p. 1206): "the ceteris paribus principles derived from them were easily destroyed by small extensions beyond the original constraints, yielding abundant exceptions to the rule. In somewhat richer stimuli, different factors determining the perceived organization interacted unpredictably, in line with the Gestalt spirit, but frustrating from the perspective of formulating laws." And: "With no testable quantitative models and no plausible neural underpinning, the Gestalt principles remained mere descriptions of interesting perceptual phenomena." An interface is a rich stimulus. Use a principle to generate a falsifiable prediction before building — a gap ratio, a contrast target, a specific expected grouping — then check it against people.

## Sources

**Primary**

- Max Wertheimer, "Untersuchungen zur Lehre von der Gestalt II", *Psychologische Forschung* 4 (1923): 301–350. English (partial) translation by Willis D. Ellis, "Laws of Organization in Perceptual Forms", in *A Source Book of Gestalt Psychology* (London: Routledge & Kegan Paul, 1938), pp. 71–88.
- Edgar Rubin, *Synsoplevede Figurer* / *Visuell wahrgenommene Figuren: Studien in psychologischer Analyse* (Copenhagen: Gyldendalske Boghandel, 1915). Rubin's non-membership of and scepticism toward the Gestalt school is documented in Jörgen L. Pind, *Edgar Rubin and Psychology in Denmark: Figure and Ground* (Springer, 2014).
- Wolfgang Köhler, *Die physischen Gestalten in Ruhe und im stationären Zustand* (Braunschweig: Vieweg und Sohn, 1920).
- Kurt Koffka, *Principles of Gestalt Psychology* (London: Lund Humphries / New York: Harcourt, Brace, 1935). Pages 110 and 150 are quoted with page numbers in Wagemans et al. (2012).
- Tadasu Oyama, "Perceptual grouping as a function of proximity", *Perceptual and Motor Skills* 13 (1961): 305–306.
- Irvin Rock & Leonard Brosgole, "Grouping based on phenomenal proximity", *Journal of Experimental Psychology* 67 (1964): 531–538.
- David J. Field, Anthony Hayes & Robert F. Hess, "Contour integration by the human visual system: Evidence for a local 'association field'", *Vision Research* 33 (1993): 173–193.
- Stephen E. Palmer, "Common Region: A New Principle of Perceptual Grouping", *Cognitive Psychology* 24, no. 3 (1992): 436–447.
- Stephen E. Palmer & Irvin Rock, "Rethinking perceptual organization: The role of uniform connectedness", *Psychonomic Bulletin & Review* 1, no. 1 (1994): 29–55, doi:10.3758/BF03200760. Counter-argument: Mary A. Peterson, "The proper placement of uniform connectedness", same journal, 1994.
- Michael Kubovy, Alex O. Holcombe & Johan Wagemans, "On the lawfulness of grouping by proximity", *Cognitive Psychology* 35, no. 1 (1998): 71–98, doi:10.1006/cogp.1997.0673.
- David Alais, Randolph Blake & Sang-Hun Lee, "Visual features that vary together over time group together over space", *Nature Neuroscience* 1, no. 2 (June 1998): 160–164.
- Allison B. Sekuler & Patrick J. Bennett, "Generalized common fate: Grouping by common luminance changes", *Psychological Science* 12 (2001): 437–444, doi:10.1111/1467-9280.00382.
- Ruth Kimchi & Batsheva Hadad, "Influence of past experience on perceptual grouping", *Psychological Science* 13 (2002): 41–47. And Stephen E. Palmer, "Perceptual grouping: It is later than you think", *Current Directions in Psychological Science* 11 (2002): 101–106.
- T. Tversky, Wilson S. Geisler & Jeffrey S. Perry, "Contour grouping: closure effects are explained by good continuation and proximity", *Vision Research* 44, no. 24 (2004): 2769–2777 (PMID 15342221).
- Michael Kubovy & Martin van den Berg, "The whole is equal to the sum of its parts: A probabilistic model of grouping by proximity and similarity in regular patterns", *Psychological Review* 115, no. 1 (2008): 131–154, doi:10.1037/0033-295X.115.1.131. The title is a deliberate rebuttal of the Gestalt slogan.
- Stephen E. Palmer & J. L. Brooks, "Edge-region grouping in figure-ground organization and depth perception", *Journal of Experimental Psychology: Human Perception and Performance* 34 (2008): 1353–1371.
- Mary A. Peterson & Elizabeth Salvagio, "Inhibitory competition in figure-ground perception: context and convexity", *Journal of Vision* 8, no. 16 (15 December 2008), Article 4, doi:10.1167/8.16.4.
- Gary Hatfield & William Epstein, "The status of the minimum principle in the theoretical analysis of visual perception", *Psychological Bulletin* 97 (1985): 155–186, doi:10.1037/0033-2909.97.2.155.
- Shih-Chiang Ke, Ankit Gupta, Yu-Hui Lo, Chih-Chung Ting & Philip Tseng, "The hidden arrow in the FedEx logo: Do we really unconsciously 'see' it?", *Cognitive Research: Principles and Implications* 8, no. 1 (2023), Article 40, doi:10.1186/s41235-023-00494-x (PMID 37395853). Author names verified against the PubMed record; secondary indexes give them wrongly.

**Review**

- Johan Wagemans, James H. Elder, Michael Kubovy, Stephen E. Palmer, Mary A. Peterson, Manish Singh & Rüdiger von der Heydt, "A Century of Gestalt Psychology in Visual Perception: I. Perceptual Grouping and Figure–Ground Organization", *Psychological Bulletin* 138, no. 6 (2012): 1172–1217, doi:10.1037/a0029333. Companion: Wagemans, Feldman, Gepshtein, Kimchi, Pomerantz, van der Helm & van Leeuwen, "II. Conceptual and Theoretical Foundations", same issue, 1218–1252.

**Design canon — assessed, not relied on**

- Aurora Harley, "Proximity Principle in Visual Design", Nielsen Norman Group, 2 August 2020. Gives no citation to any original study and no numeric spacing guidance.
- Aurora Harley, "The Principle of Common Region: Containers Create Groupings", Nielsen Norman Group, 12 July 2020. Does cite Palmer 1992. Note that the two NN/g articles make competing dominance claims — proximity "can overpower" similarity, a boundary "can overpower" proximity or similarity — that Palmer 1992, p. 439 says cannot be predicted in the general case.
- Laws of UX, "Law of Proximity" and "Law of Common Region". The proximity page cites Wikipedia, Smashing Magazine, NN/g, the Interaction Design Foundation and a Marvel blog post, with no primary source. The common-region page cites NN/g, Smashing Magazine, Scholarpedia and Wikipedia, and does not cite Palmer 1992. Both use the word "law" despite Palmer's own footnote disclaiming it. Evidence of what designers believe, not evidence for the claims.
