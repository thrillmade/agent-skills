"""Characterize the `check-prose-retention` gate.

The gate's job is one distinction: reformatting is free, losing content is not.
So the suite is built in matched pairs -- for every edit that must fire there is
a formatting-only edit that must not. A detector that flagged every touched file
would pass half of these and fail the other half, which is the point.

The strongest evidence is at the top: the three real deletions from the #197
link-conversion sweep, vendored under `fixtures/prose-retention/` alongside two
files that took the same conversion and lost nothing. See that directory's
PROVENANCE.md.

Assertions here are on the MEASUREMENT wherever the measurement is the subject.
Asserting `run(...) == []` only proves a case does not fire, which any word
*gain* satisfies for free -- two tests written that way passed with
normalisation deleted outright, so they asserted nothing about the behaviour
they were named for.

`tests/test_prose_retention_mutations.py` proves this file has teeth by breaking
the detector and asserting these tests go red.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

import check_prose_retention as cpr  # noqa: E402 -- conftest puts it on sys.path

FIXTURES = Path(__file__).parent / "fixtures" / "prose-retention"

# The three files the sweep took prose out of, and the net word loss the
# detector measures for each. The numbers are pinned deliberately: they are
# what the escape-hatch ledger row has to carry, so a silent change to the
# measurement is a silent change to the declarations people have already
# written.
HISTORICAL_LOSSES = {
    "web-interface-guidelines-review": 13,
    "clud-bug-collaboration": 44,
    "session-heartbeat": 49,
}

# Same sweep, same scale of change, no content lost.
HISTORICAL_CLEAN = ["reviewing-design-work", "designing-a-design-system"]


def fixture(name: str) -> tuple[str, str]:
    d = FIXTURES / name
    return (
        (d / "before.md").read_text(encoding="utf-8"),
        (d / "after.md").read_text(encoding="utf-8"),
    )


def case(name: str, before: str, after: str) -> dict[str, tuple[str, str]]:
    return {f"skills/{name}/SKILL.md": (before, after)}


def skill_file(name: str, description: str, body: str) -> str:
    return f"---\nname: {name}\ndescription: {description}\n---\n\n# Title\n\n{body}"


def skill(body: str, name: str = "alpha") -> str:
    """A whole SKILL.md around `body`, with a frontmatter block that does not
    change between the two revisions.

    Every case goes through one, because the gate refuses to report a verdict
    on a file whose frontmatter it cannot locate: merging the frontmatter into
    the prose scope is exactly what let 46 words of padding in a `description:`
    pay for a deleted body section. An identical frontmatter on both sides
    scores zero, so wrapping a fragment leaves every number in these tests
    unchanged.
    """
    return skill_file(name, "What this skill does and when to use it.", body)


# --- the historical defect --------------------------------------------------


@pytest.mark.parametrize("name", sorted(HISTORICAL_LOSSES))
def test_fires_on_each_real_deletion(name):
    """Each of the three files that lost prose to the #197 sweep is caught."""
    before, after = fixture(name)
    errors = cpr.run(case(name, before, after))
    assert len(errors) == 1, f"{name}: expected exactly one error, got {errors}"
    assert f"skills/{name}/SKILL.md" in errors[0]


@pytest.mark.parametrize("name", sorted(HISTORICAL_LOSSES))
def test_real_deletion_word_counts_are_stable(name):
    """The measured loss is the number the ledger row must carry."""
    before, after = fixture(name)
    assert cpr.Loss(before, after).net == HISTORICAL_LOSSES[name]


@pytest.mark.parametrize("name", sorted(HISTORICAL_LOSSES))
def test_each_real_deletion_is_charged_to_the_prose(name):
    """All three cut prose -- not frontmatter, not a code block. Pinning the
    scope is what keeps the breakdown in the error message honest.
    """
    before, after = fixture(name)
    assert list(cpr.Loss(before, after).over) == ["prose"]


@pytest.mark.parametrize("name", HISTORICAL_CLEAN)
def test_silent_on_real_link_conversion_that_lost_nothing(name):
    """The control. These took the same sweep across 50-odd lines and kept
    every word; a gate that fires here is a gate nobody will keep.
    """
    before, after = fixture(name)
    assert cpr.run(case(name, before, after)) == []


def test_the_whole_sweep_flags_three_files_and_no_others():
    """All five fixtures in one run, as CI would see them."""
    cases = {}
    for name in list(HISTORICAL_LOSSES) + HISTORICAL_CLEAN:
        cases.update(case(name, *fixture(name)))
    errors = cpr.run(cases)
    assert len(errors) == 3
    flagged = {e.split("::error file=")[1].split("::")[0] for e in errors}
    assert flagged == {f"skills/{n}/SKILL.md" for n in HISTORICAL_LOSSES}


@pytest.mark.parametrize("name", sorted(HISTORICAL_LOSSES))
def test_error_quotes_the_passage_that_went(name):
    """An author has to be able to recognise what they deleted."""
    before, after = fixture(name)
    (error,) = cpr.run(case(name, before, after))
    marker = {
        "web-interface-guidelines-review": "Skills cross-referenced",
        "clud-bug-collaboration": "CLUD_BUG_QUIET",
        "session-heartbeat": "mechanism",
    }[name]
    assert marker in error, f"{name}: error does not quote the lost passage: {error}"


# --- normalising links is the load-bearing move -----------------------------


def test_without_normalisation_the_sharpest_case_reads_as_a_gain():
    """This is why `normalise()` exists, stated as an assertion.

    `[x](../x/SKILL.md)` tokenises to four words where `` `x` `` tokenises to
    one. Converting a dozen of them swamps a 13-word deletion. Measured on the
    real commit: normalised, a 13-word loss; raw, a 41-word *gain*.
    Un-normalised, this gate would have gone green on the file that lost the
    routing rule.
    """
    before, after = fixture("web-interface-guidelines-review")

    import collections

    raw_before = collections.Counter(cpr.WORD_RE.findall(before))
    raw_after = collections.Counter(cpr.WORD_RE.findall(after))
    raw_net = sum((raw_before - raw_after).values()) - sum(
        (raw_after - raw_before).values()
    )

    assert raw_net == -41, "raw comparison should read the sweep as a word gain"
    assert cpr.Loss(before, after).net == 13
    assert raw_net <= cpr.FLOOR["prose"], "raw comparison would not fire"
    assert cpr.Loss(before, after).net > cpr.FLOOR["prose"]


def test_backticks_to_link_is_free():
    """Asserted on the measurement, not on the verdict.

    `run(...) == []` is satisfied by any word gain, so in this direction it
    passed even with normalisation deleted. `net == 0` is the actual claim.
    """
    before = skill("See `spacing-system` and `apca-contrast` for the rules.")
    after = skill(
        "See [spacing-system](../spacing-system/SKILL.md) and "
        "[apca-contrast](../apca-contrast/SKILL.md) for the rules."
    )
    assert cpr.Loss(before, after).net == 0
    assert cpr.run(case("alpha", before, after)) == []


def test_link_back_to_backticks_is_free():
    """The reverse conversion too -- #212 did exactly this to buy budget."""
    after = skill("See `spacing-system` and `apca-contrast` for the rules.")
    before = skill(
        "See [spacing-system](../spacing-system/SKILL.md) and "
        "[apca-contrast](../apca-contrast/SKILL.md) for the rules."
    )
    assert cpr.Loss(before, after).net == 0
    assert cpr.run(case("alpha", before, after)) == []


def test_link_with_an_anchor_normalises_too():
    """Anchored links, asserted on the normalised text itself.

    In the backticks-to-link direction an un-normalised comparison is a word
    gain, so the verdict form of this assertion passed with `normalise()`
    gutted -- it named anchors and tested nothing.
    """
    before = "Read `type-scale` first."
    after = "Read [type-scale](../type-scale/SKILL.md#the-ladder) first."
    assert cpr.normalise(after) == "Read type-scale first."
    assert cpr.Loss(skill(before), skill(after)).net == 0


def test_an_anchored_conversion_cannot_mask_a_deletion():
    """The regression anchor handling exists for, as a measurement.

    Converting four backticked names to ANCHORED links is a large word gain if
    the anchors are not collapsed -- enough to swallow a real deleted clause
    and go green. That is the #197 shape exactly.
    """
    before = skill(
        "Read `type-scale` and `spacing-system` and `apca-contrast` and "
        "`wcag-contrast` first, and never drop the floor rule that follows.\n"
    )
    converted = skill(
        "Read [type-scale](../type-scale/SKILL.md#ladder) and "
        "[spacing-system](../spacing-system/SKILL.md#grid) and "
        "[apca-contrast](../apca-contrast/SKILL.md#lc) and "
        "[wcag-contrast](../wcag-contrast/SKILL.md#aa) first, and never drop "
        "the floor rule that follows.\n"
    )
    # The conversion on its own is free, in both directions.
    assert cpr.Loss(before, converted).net == 0
    assert cpr.Loss(converted, before).net == 0

    # The same conversion, with a clause deleted under cover of it.
    cut = converted.replace(", and never drop the floor rule that follows", "")
    assert cpr.Loss(before, cut).net == 8
    assert len(cpr.run(case("alpha", before, cut))) == 1


def test_de_linking_an_external_reference_is_free():
    """Link maintenance is not prose loss.

    `check-doc-links` exists because links rot, so repointing or unlinking one
    is routine work here. Scoped to SKILL.md links alone, this gate charged 3
    to 8 invented words for de-linking any of the 37 external links in the
    catalog even when the sentence kept every word -- the exact inverse of the
    transform it was built to forgive.
    """
    before = skill(
        "Source: APCA spec at [git.apcacontrast.com]"
        "(https://git.apcacontrast.com/documentation/README). The table maps "
        "directly to the ladder."
    )
    after = skill(
        "Source: APCA spec at git.apcacontrast.com. The table maps directly "
        "to the ladder."
    )
    assert cpr.Loss(before, after).net == 0
    assert cpr.run(case("alpha", before, after)) == []


def test_de_linking_a_repo_file_reference_is_free():
    before = skill(
        "See [validate_skills.py](.github/scripts/validate_skills.py) for the limit."
    )
    after = skill("See `validate_skills.py` for the limit.")
    assert cpr.Loss(before, after).net == 0


def test_a_bare_url_is_not_prose():
    """An address is not a claim. Adding or dropping one scores zero, in both
    directions, so a reference that rotted can be pulled without a ledger row.
    """
    before = skill(
        "The canonical reference is the spec: https://git.apcacontrast.com/docs\n"
    )
    after = skill("The canonical reference is the spec:\n")
    assert cpr.Loss(before, after).net == 0
    assert cpr.Loss(after, before).net == 0


def test_a_link_that_replaces_prose_still_fires():
    """Normalisation must not become a laundry channel: swapping a sentence
    for a bare link is a deletion wearing the free transform's clothes.
    """
    before = skill(
        "Contrast findings cite the perceptual model and the legal baseline "
        "both, and name which one failed."
    )
    after = skill("See [apca-contrast](../apca-contrast/SKILL.md).")
    assert len(cpr.run(case("alpha", before, after))) == 1


# --- formatting is free -----------------------------------------------------


def test_rewrapping_a_paragraph_is_free():
    before = skill("One two three four five six seven eight nine ten eleven twelve.\n")
    after = skill("One two three four five\nsix seven eight nine\nten eleven twelve.\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_reordering_sections_is_free():
    a = "## Alpha\n\nThe first section says one thing about the subject.\n"
    b = "## Beta\n\nThe second section says a different thing entirely.\n"
    assert cpr.run(case("alpha", skill(a + "\n" + b), skill(b + "\n" + a))) == []


def test_moving_a_line_to_another_section_is_free():
    before = skill("## A\n\nkeep this line here\n\n## B\n\nother content entirely\n")
    after = skill("## A\n\n## B\n\nother content entirely\n\nkeep this line here\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_bolding_and_italicising_is_free():
    before = skill("Line height is floored at 1.2 across every role in the scale.\n")
    after = skill(
        "**Line height** is *floored* at `1.2` across every role in the scale.\n"
    )
    assert cpr.run(case("alpha", before, after)) == []


def test_turning_a_paragraph_into_a_list_is_free():
    before = skill("Check contrast then typography then spacing then tokens.\n")
    after = skill("- Check contrast\n- then typography\n- then spacing\n- then tokens\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_a_file_that_did_not_change_is_free():
    text = skill("Some skill body with several words in it.\n")
    assert cpr.run(case("alpha", text, text)) == []


def test_adding_prose_is_free():
    before = skill("A short body.\n")
    after = skill("A short body.\n\nPlus a new paragraph nobody had written before.\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_fixing_a_typo_is_free():
    before = skill("Findings must cite the skills they recieve their authority from.\n")
    after = skill("Findings must cite the skills they receive their authority from.\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_rewording_at_similar_length_is_free():
    before = skill("The primary model is APCA, and WCAG serves only as a cross-check.\n")
    after = skill("APCA is the primary model; WCAG is nothing more than a cross-check.\n")
    assert cpr.run(case("alpha", before, after)) == []


# --- content removal fires --------------------------------------------------


def test_deleting_a_sentence_fires():
    before = skill(
        "Load the skill first.\n"
        "Findings must cite the skills they rest on, every time.\n"
        "Then report.\n"
    )
    after = skill("Load the skill first.\nThen report.\n")
    (error,) = cpr.run(case("alpha", before, after))
    assert "lost 10 words" in error


def test_replacing_a_paragraph_with_a_short_stub_fires():
    """Forty words swapped for three is a deletion, whatever replaced them."""
    before = skill(" ".join(f"substantive{i}" for i in range(40)))
    after = skill("see the other skill")
    assert len(cpr.run(case("alpha", before, after))) == 1


def test_deleting_the_frontmatter_description_fires():
    """The description is the routing text -- losing it is losing content."""
    before = skill_file(
        "alpha",
        "Use when picking a control height or auditing a ladder that has "
        "drifted across a codebase.",
        "Body.\n",
    )
    after = skill_file("alpha", "Use when picking a height.", "Body.\n")
    (error,) = cpr.run(case("alpha", before, after))
    assert "from its frontmatter" in error


# --- each part of the file is scored on its own -----------------------------
#
# This is what stops the gate being paid off. The pressure that caused the
# defect does not price every byte the same: the size cap excludes the
# frontmatter entirely, and fenced code costs 6-13 bytes a word against prose's
# 4.6. Either one lets an author buy real bytes while netting a whole-file word
# count to zero.


def test_padding_the_frontmatter_cannot_pay_for_a_deleted_section():
    """The real historical deletion, plus description padding that nets a
    whole-file count to nothing.

    Reproduced against whole-file scoring: it passed, and `validate-skills`
    stayed green with it, because the frontmatter sits outside the 8192-byte
    cap -- so the padding cost nothing against the constraint that caused the
    defect in the first place.
    """
    before, after = fixture("clud-bug-collaboration")
    padded = []
    for line in after.split("\n"):
        if line.startswith("description:"):
            line += " " + " ".join(f"padding{i}" for i in range(46))
        padded.append(line)
    padded_after = "\n".join(padded)

    import collections

    def whole_file_net(b, a):
        bc = collections.Counter(cpr.words(b))
        ac = collections.Counter(cpr.words(a))
        return sum((bc - ac).values()) - sum((ac - bc).values())

    assert whole_file_net(before, padded_after) <= cpr.FLOOR["prose"], (
        "the padding should net a whole-file count below the floor -- "
        "otherwise this test is not exercising the evasion it names"
    )

    loss = cpr.Loss(before, padded_after)
    assert loss.scopes["prose"] == 44
    assert loss.scopes["frontmatter"] < 0, "the description really did grow"
    assert len(cpr.run(case("clud-bug-collaboration", before, padded_after))) == 1


def test_filler_prose_cannot_pay_for_a_deleted_code_example():
    """A worked example is content. Deleting one and adding a same-length
    sentence of filler frees real bytes -- measured at 139 on test-discipline,
    the tightest file in the catalog -- and nets a whole-body count to zero.
    """
    before = skill_file(
        "alpha",
        "d",
        "Intro paragraph here.\n\n```js\n"
        "jest.mock('./billing', () => ({ chargeCard: jest.fn().mockResolvedValue("
        "{ ok: true }) }))\n"
        "it('completes checkout', async () => { expect(await checkout()).toBe(true) })\n"
        "```\n\nOutro.\n",
    )
    after = skill_file(
        "alpha",
        "d",
        "Intro paragraph here.\n\nMock only what you must and keep the rest of "
        "the real path in play, or the test proves nothing at all whatsoever.\n"
        "\nOutro.\n",
    )
    loss = cpr.Loss(before, after)
    assert loss.scopes["code"] > cpr.FLOOR["code"]
    assert loss.scopes["prose"] < 0, "the filler really did land in the prose"
    assert len(cpr.run(case("alpha", before, after))) == 1


def test_a_code_example_rewritten_at_similar_length_is_free():
    """The control for the scope above. Rewriting an example in another
    notation keeps the example; a gate that fires here is noise.
    """
    before = skill_file("alpha", "d", 'Text.\n\n```json\n{ "strictMode": false }\n```\n')
    after = skill_file("alpha", "d", "Text.\n\n```yaml\nstrictMode: false\n```\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_scopes_are_not_netted_against_each_other():
    """Stated directly on the arithmetic, so the property does not depend on
    any one evasion fixture keeping the shape it has today.
    """
    before = skill_file("alpha", "one two three four five six seven eight", "Nine ten.\n")
    after = skill_file(
        "alpha", "one", "Nine ten eleven twelve thirteen fourteen fifteen.\n"
    )
    loss = cpr.Loss(before, after)
    assert loss.scopes["frontmatter"] == 7
    assert loss.scopes["prose"] == -5
    assert loss.net == 7, "a prose gain must not be subtracted from a frontmatter loss"


# --- the scope split has to be findable, or there is no verdict -------------
#
# Scoring the parts separately is what stops the gate being paid off, and it
# rests entirely on finding the frontmatter. When that fails the split does not
# fail -- it silently returns one scope, and the evasion the split exists to
# stop works again. It is reachable through `validate-skills`, not around it:
# that gate reads with `Path.read_text`, which translates CRLF away before its
# frontmatter regex ever runs, while this one decodes the git blob byte for
# byte. A SKILL.md with CRLF line endings therefore passes validate-skills and
# arrives here with no frontmatter the gate can see.

CRLF_VARIANTS = {
    "crlf": lambda t: t.replace("\n", "\r\n"),
    "cr": lambda t: t.replace("\n", "\r"),
    "bom": lambda t: "﻿" + t,
    "bom_crlf": lambda t: "﻿" + t.replace("\n", "\r\n"),
}


@pytest.mark.parametrize("variant", sorted(CRLF_VARIANTS))
@pytest.mark.parametrize("name", sorted(HISTORICAL_LOSSES))
def test_the_scope_split_is_the_same_under_any_line_ending(variant, name):
    """The property, pinned for every byte-level spelling of a line break
    rather than for LF alone -- which is all it was pinned for, and the gap the
    whole evasion fits through.
    """
    before, _after = fixture(name)
    assert cpr.split_scopes(CRLF_VARIANTS[variant](before)) == cpr.split_scopes(before)


@pytest.mark.parametrize("variant", sorted(CRLF_VARIANTS))
@pytest.mark.parametrize("name", sorted(HISTORICAL_LOSSES))
def test_padding_the_frontmatter_cannot_pay_for_a_deletion_under_any_line_ending(
    variant, name
):
    """The evasion itself, on the gate's own canonical cases.

    Each of the three real deletions, with the description padded past the size
    of the cut and the file's line endings rewritten. Merged into one scope the
    padding cancels the deletion exactly and all three go green.
    """
    rewrite = CRLF_VARIANTS[variant]
    before, after = fixture(name)
    net = HISTORICAL_LOSSES[name]
    padded = "\n".join(
        line + " " + " ".join(f"padding{i}" for i in range(net + 5))
        if line.startswith("description:")
        else line
        for line in after.split("\n")
    )
    loss = cpr.Loss(rewrite(before), rewrite(padded))
    assert loss.scopes["prose"] == net, loss.scopes
    assert loss.scopes["frontmatter"] < 0, "the padding really did land"
    assert len(cpr.run(case(name, rewrite(before), rewrite(padded)))) == 1


UNSCOPABLE = {
    "no frontmatter at all": "# Title\n\nA body with no frontmatter block.\n",
    "an unclosed frontmatter block": "---\nname: alpha\ndescription: d\n\n# Title\n",
    "a frontmatter block that starts late": "\n---\nname: alpha\n---\n\n# Title\n",
    "a fence where the frontmatter should be": "```\nname: alpha\n```\n\n# Title\n",
}


@pytest.mark.parametrize("text", sorted(UNSCOPABLE.values()), ids=sorted(UNSCOPABLE))
def test_a_file_whose_frontmatter_cannot_be_found_gets_no_verdict(text):
    """It refuses, the way it already refuses when it cannot resolve a base.

    Merging the frontmatter into the prose is not a safe default: it is the
    exact configuration in which 46 words of padding in a `description:` buy the
    deletion of a body section, which is one of the two evasions the scope split
    was built for. A gate that cannot make its comparison says so.
    """
    with pytest.raises(cpr.Unscopable):
        cpr.split_scopes(text)


def test_the_control_a_well_formed_skill_file_is_scoped_without_complaint():
    """The control for the refusals above: the refusal is about the file, not
    about the gate having forgotten how to split anything.
    """
    scopes = cpr.split_scopes(skill("Body.\n"))
    assert scopes["frontmatter"].startswith("---\n")
    assert "Body." in scopes["prose"]


def test_the_refusal_names_the_file_and_fails_the_run():
    """A refusal nobody can see is a crash. It has to arrive as an annotation
    against the file, the way the invalid-UTF-8 refusal does.
    """
    broken = "# Title\n\nA body with no frontmatter block at all.\n"
    (error,) = cpr.run(case("alpha", broken, broken + "and one more line.\n"))
    assert error.startswith("::error file=skills/alpha/SKILL.md::")
    assert "frontmatter" in error
    assert "no verdict" in error


def test_a_fence_only_closes_on_a_fence_at_least_as_long():
    """CommonMark's rule, and the reason it matters here: normalising every
    fence to three characters let a ``` line inside a ```` block close it, so a
    block's contents changed scope when somebody edited a line nowhere near it.
    """
    body = "Intro.\n\n````\n```\ncode inside the longer fence\n````\n\nOutro.\n"
    scopes = cpr.split_scopes(skill(body))
    assert "code inside the longer fence" in scopes["code"]
    assert "code inside the longer fence" not in scopes["prose"]
    assert "Intro." in scopes["prose"] and "Outro." in scopes["prose"]


# --- markdown has two spellings of a code block -----------------------------
#
# Reading only the fence left the byte arbitrage above open through the other
# one, at MORE bytes per word rather than fewer -- and it is the one spelling a
# reader of the rendered page cannot tell apart from the other, so nothing in
# review says which was used. The pairs below stand either side of the two
# CommonMark rules that keep the reading off ordinary prose: an indented block
# cannot interrupt a paragraph, and the four spaces are measured from the
# enclosing list item's content column.

INDENTED_EXAMPLE = (
    "    jest.mock('./billing', () => ({ chargeCard: jest.fn() }))\n"
    "    it('completes checkout', async () => expect(await checkout()).toBe(true))\n"
)


def test_filler_prose_cannot_pay_for_a_deleted_INDENTED_code_example():
    """The founding evasion in markdown's other spelling of a code block.

    The fenced version of this trade is `test_filler_prose_cannot_pay_for_a_
    deleted_code_example` above. Written with four spaces instead the example
    scored as PROSE, so deleting it and adding a same-length sentence of filler
    netted the prose scope to nothing and the gate went green -- with the
    incentive intact rather than reduced, because an indented block spends more
    bytes per word than a fence does.
    """
    before = skill_file("alpha", "d", "Intro paragraph here.\n\n" + INDENTED_EXAMPLE + "\nOutro.\n")
    after = skill_file(
        "alpha",
        "d",
        "Intro paragraph here.\n\nMock only what you must and keep the rest of "
        "the real path in play, or the test proves nothing at all whatsoever "
        "here.\n\nOutro.\n",
    )
    loss = cpr.Loss(before, after)
    assert loss.scopes["code"] > cpr.FLOOR["code"], loss.scopes
    assert loss.scopes["prose"] < 0, "the filler really did land in the prose"
    assert len(cpr.run(case("alpha", before, after))) == 1


def test_an_indented_example_rewritten_at_similar_length_is_free():
    """The control for the pair above, matching the fenced one. Reading the
    second spelling must not turn rewriting an example into a removal.
    """
    before = skill_file("alpha", "d", 'Text.\n\n    { "strictMode": false }\n')
    after = skill_file("alpha", "d", "Text.\n\n    strictMode: false\n")
    assert cpr.run(case("alpha", before, after)) == []


def test_an_indented_block_cannot_interrupt_a_paragraph():
    """CommonMark's first rule, on the shape that needs it.

    An over-indented continuation of a wrapped line is one paragraph to every
    renderer. Without this rule a gate reading four spaces as code would move it
    into the code scope -- real prose, rescoped, so a cut to it is charged
    against the wrong floor and payable by the wrong additions.
    """
    body = (
        "A paragraph whose second line is indented well past where it began,\n"
        "    which markdown renders as one paragraph and not as a code block.\n"
    )
    scopes = cpr.split_scopes(skill(body))
    assert "which markdown renders as one paragraph" in scopes["prose"]
    assert scopes["code"].strip() == "", scopes["code"]


def test_a_nested_list_item_keeps_its_own_paragraphs_out_of_the_code_scope():
    """CommonMark's second rule, on the shape that needs THAT one.

    A blank line inside a list item starts a second paragraph OF THAT ITEM, and
    its indent is the item's content column -- five here, past the four that
    would otherwise read as code. The rule above does not cover this one: the
    blank line is there, so only measuring from the item's content column keeps
    it prose.
    """
    body = (
        "1. Outer step.\n"
        "   - Inner bullet that runs on.\n\n"
        "     A second paragraph belonging to the inner bullet.\n"
    )
    scopes = cpr.split_scopes(skill(body))
    assert "A second paragraph belonging to the inner bullet." in scopes["prose"]
    assert scopes["code"].strip() == "", scopes["code"]


def test_an_indented_block_inside_a_list_item_is_still_code():
    """The control for the rule above: measuring from the item's content column
    is a shift, not an exemption. Four spaces past that column is a code block
    however deep the item sits, or the list becomes the place to hide one.
    """
    body = "- A step.\n\n      the_worked(example, goes, here)\n"
    scopes = cpr.split_scopes(skill(body))
    assert "the_worked(example, goes, here)" in scopes["code"]
    assert "the_worked" not in scopes["prose"]


def test_a_tab_indented_block_is_code_too():
    """A tab is four columns to CommonMark. Counting leading SPACES alone would
    leave the same hole in a third spelling of the same block.
    """
    body = "Intro.\n\n\tthe_worked(example, goes, here)\n"
    scopes = cpr.split_scopes(skill(body))
    assert "the_worked(example, goes, here)" in scopes["code"]
    assert "the_worked" not in scopes["prose"]


def test_a_fence_inside_an_indented_block_does_not_open_a_fenced_block():
    """The two spellings cannot nest, and getting that wrong is worse than not
    reading the indented block at all: a ``` line quoted inside one would open a
    fence that swallows every line to the end of the file, changing the scope of
    text nobody edited.
    """
    body = "Intro.\n\n    ```\n    quoted fence\n    ```\n\nOutro paragraph here.\n"
    scopes = cpr.split_scopes(skill(body))
    assert "quoted fence" in scopes["code"]
    assert "Outro paragraph here." in scopes["prose"], scopes["prose"]


# --- a blank line is ONE paragraph boundary, not the only one ----------------
#
# An indented block opens where no paragraph is open, and reading "no paragraph
# is open" as "the line above was blank" was a proxy, not the rule. Every leaf
# block below closes a paragraph on its own line, so CommonMark opens an
# indented block underneath one with no blank line between -- and each pairs
# with a spelling that must still be prose, because the proxy is wrong in both
# directions and only one of them is an evasion.
#
# Every row was adjudicated against markdown-it-py rather than reasoned out, and
# adjudicating refuted two candidates that had been handed over as obvious: an
# HTML BLOCK START does not close anything (`<div>` runs to the next blank line,
# so the line under it is still the block's own content), and a LIST MARKER does
# not either (`- item` opens a paragraph inside the item). Each had a narrow
# true form underneath it that assuming would have missed, and both are here.

PARAGRAPH_BOUNDARIES = [
    # (label, the line under test, does an indented line under it become code)
    ("atx heading", "## Heading", True),
    ("atx heading, closed form", "## Heading ##", True),
    ("seven hashes is not a heading", "####### Heading", False),
    ("no space after the hashes is not one either", "##Heading", False),
    ("thematic break", "***", True),
    ("thematic break, spaced", "* * *", True),
    ("thematic break, underscores", "___", True),
    ("dashes count too", "- - -", True),
    ("a mixed run is not a thematic break", "- * -", False),
    ("nor is this one", "*-*", False),
    ("two is one short of a break", "**", False),
    ("setext underline", "===", True),
    ("setext underline, dashes", "---", True),
    ("an empty item under a paragraph is a setext underline", "- ", True),
    ("html block that closes on its line", "<!-- a note -->", True),
    ("html doctype", "<!DOCTYPE html>", True),
    ("html block that does NOT close on its line", "<div>", False),
    ("html comment left open", "<!-- a note", False),
    ("a list marker with content on it", "- a bullet", False),
    ("an ordinary paragraph line", "more of the paragraph", False),
]


@pytest.mark.parametrize(
    "label,line,is_code", PARAGRAPH_BOUNDARIES, ids=[b[0] for b in PARAGRAPH_BOUNDARIES]
)
def test_a_leaf_block_closes_a_paragraph_without_a_blank_line(label, line, is_code):
    """The rule, one construct at a time, against what CommonMark does.

    THE EVASION this exists to stop: an ATX heading closes the paragraph, so the
    indented example under it is a code block to every renderer and was PROSE
    here -- where it netted against deleted prose. Reproduced on the file the
    module docstring names, deleting web-interface-guidelines-review's
    Verification rule 5 and putting a heading-adjacent example where it stood:
    prose -5, gate green, ledger untouched, and the file 19 bytes SMALLER so the
    trade paid the size pressure too. One blank line further down, the identical
    example scored prose 11 / code -16 and fired.

    The `False` rows are the other direction and they are not filler: a rule
    that closed a paragraph on any of them would move real prose into the code
    scope, which is the false positive that costs a ledger row declaring words
    safe to lose when none were lost.
    """
    body = f"An opening paragraph here.\n{line}\n    an_indented_example()\n"
    scopes = cpr.split_scopes(skill(body))
    where = "code" if is_code else "prose"
    assert "an_indented_example()" in scopes[where], (label, scopes)
    assert "an_indented_example()" not in scopes[
        "prose" if is_code else "code"
    ], (label, scopes)


def test_a_leaf_block_cannot_be_spelled_inside_a_wrapped_line():
    """The guard on the rule above: indented past the threshold with a paragraph
    open, a line is that paragraph's WRAPPED TEXT and no block at all.

    `    ## H` under a paragraph is four words of prose to CommonMark, not a
    heading -- so it closes nothing and the line under it stays prose too.
    Without the guard the rule fires inside every wrapped continuation that
    happens to begin with a hash or a dash, which is a false positive on text
    nobody edited.
    """
    for spelling in ("    ## H", "    ***", "    ---"):
        body = f"An opening paragraph here.\n{spelling}\n    an_indented_example()\n"
        scopes = cpr.split_scopes(skill(body))
        assert "an_indented_example()" in scopes["prose"], (spelling, scopes)
        assert "an_indented_example()" not in scopes["code"], (spelling, scopes)

    # Three spaces is within CommonMark's slack, so that one IS a heading.
    body = "An opening paragraph here.\n   ## H\n    an_indented_example()\n"
    scopes = cpr.split_scopes(skill(body))
    assert "an_indented_example()" in scopes["code"], scopes


def test_a_setext_underline_needs_a_paragraph_above_it():
    """`===` with a blank line over it is a PARAGRAPH, not an underline, so it
    closes nothing and the line under it is its own wrapped text. Reading it as
    an underline regardless rescopes that line into the code examples.
    """
    body = "Intro paragraph.\n\n===\n    an_indented_example()\n"
    scopes = cpr.split_scopes(skill(body))
    assert "an_indented_example()" in scopes["prose"], scopes
    assert "an_indented_example()" not in scopes["code"], scopes


def test_an_empty_list_item_opens_no_paragraph_and_takes_the_marker_s_column():
    """One CommonMark rule with two halves, so one test.

    An item with nothing on its opening line leaves no paragraph open AND puts
    its content column at the marker plus one, whatever the gap after the
    marker. Both halves have to hold or a block indented under `- ` is read as
    the item's own wrapped text: the first half blocks the open, the second
    raises the threshold past the block's indent.

    Adjudicated per marker WIDTH, which is what makes this the column rule and
    not a constant: the boundary is the marker plus one plus four, so under `- `
    six spaces is code and five is not, under `1.` it is seven and six, and
    `-    ` -- four spaces of gap, no content -- measures from the same column
    as `- ` rather than from the end of its gap.
    """
    for marker, code_at, prose_at in (
        ("- ", 6, 5),
        ("-", 6, 5),
        ("-    ", 6, 5),
        ("1.", 7, 6),
        ("10.", 8, 7),
    ):
        body = f"Intro paragraph.\n\n{marker}\n{' ' * code_at}an_indented_example()\n"
        scopes = cpr.split_scopes(skill(body))
        assert "an_indented_example()" in scopes["code"], (marker, scopes)

        # One column short of it, so it is the item's own prose.
        body = f"Intro paragraph.\n\n{marker}\n{' ' * prose_at}the_items_own_text\n"
        scopes = cpr.split_scopes(skill(body))
        assert "the_items_own_text" in scopes["prose"], (marker, scopes)

    # An item WITH content on its opening line opens a paragraph as before.
    body = "Intro paragraph.\n\n- a bullet\n      wrapped continuation here\n"
    scopes = cpr.split_scopes(skill(body))
    assert "wrapped continuation here" in scopes["prose"], scopes


def test_a_blank_line_inside_an_indented_block_belongs_to_the_block():
    """The one thing `_indented` still decides on its own.

    Continuing an indented block and opening one became the same condition once
    a paragraph was modelled, so every WORD-BEARING line in a block is now
    decided by "is a paragraph open" -- which is why the flag survives only to
    say that the gap between two chunks of one block is part of it, as
    CommonMark has it. That is a wordless line and it moves no score, which is
    exactly why it needs asserting here: nothing else in this file would notice
    if it stopped being true, and a flag nothing constrains is a flag the next
    edit is free to get wrong.

    The second case is the same property across a container boundary, where a
    quote closed the block the marker sat above.
    """
    body = "Intro.\n\n    chunk_one()\n\n    chunk_two()\nOutro paragraph.\n"
    scopes = cpr.split_scopes(skill(body))
    assert scopes["code"].split("\n") == ["    chunk_one()", "", "    chunk_two()"], (
        scopes["code"]
    )

    body = "    code_line_one()\n> a quote\n\nOutro paragraph.\n"
    scopes = cpr.split_scopes(skill(body))
    assert scopes["code"].split("\n") == ["    code_line_one()"], scopes["code"]


def test_a_line_that_closed_a_paragraph_is_not_also_a_list_marker():
    """`- ` under a paragraph is a setext underline, and reading it as a marker
    as well pushes a content column that raises the threshold and re-hides the
    block the underline just exposed. A closing leaf block is one block, not
    two.
    """
    body = "An opening paragraph here.\n- \n    an_indented_example()\n"
    scopes = cpr.split_scopes(skill(body))
    assert "an_indented_example()" in scopes["code"], scopes
    assert "an_indented_example()" not in scopes["prose"], scopes


# --- a block quote is a CONTAINER, not a third spelling ---------------------
#
# Reading both spellings still left them both invisible behind a `>`: every rule
# in `Container` allows only whitespace before a fence and measures an indent
# from its own left margin, so one marker suppressed the pair. It shipped in 4
# of this catalog's 49 skills and fired in both directions on real files. The
# pairs below stand either side of that -- what must now be code, and what must
# still be prose.

EXAMPLE_LINES = [
    "```",
    "jest.mock('./billing', () => ({ chargeCard: jest.fn() }))",
    "it('completes checkout', async () => expect(await checkout()).toBe(true))",
    "```",
]

# Every spelling carries the SAME heading above it, so the heading's own words
# cancel and the only thing left to differ is the reading.
HEADING = "## Worked example"

# The same example in every way markdown can spell it -- the container included,
# and the GAP ABOVE IT included. The fence carries no info string, so all eight
# reduce to the same word stream and any difference in the score is a difference
# in the reading alone.
#
# The last two sit directly under the heading, and they are here because the
# first six all sat under a BLANK line and that was the hole. An ATX heading is
# a leaf block: it closes the paragraph, so CommonMark opens an indented block
# on the very next line and renders the two placements to identical HTML. A
# detector that reads only a blank line as a boundary banks that line as prose
# instead -- and the six spellings above, every one of them blank-separated,
# could not see it. The fixture had the blind spot baked in, so the equivalence
# it asserts was true and narrow at the same time.
SPELLINGS = {
    "fenced": f"{HEADING}\n\n" + "\n".join(EXAMPLE_LINES),
    "indented": f"{HEADING}\n\n"
    + "\n".join("    " + ln for ln in EXAMPLE_LINES[1:-1]),
    "quoted fence": f"{HEADING}\n\n" + "\n".join("> " + ln for ln in EXAMPLE_LINES),
    "quoted indent": f"{HEADING}\n\n"
    + "\n".join(">     " + ln for ln in EXAMPLE_LINES[1:-1]),
    "nested quote": f"{HEADING}\n\n" + "\n".join("> > " + ln for ln in EXAMPLE_LINES),
    "no space after the marker": f"{HEADING}\n\n"
    + "\n".join(">" + ln for ln in EXAMPLE_LINES),
    "heading-adjacent indent": f"{HEADING}\n"
    + "\n".join("    " + ln for ln in EXAMPLE_LINES[1:-1]),
    "heading-adjacent fence": f"{HEADING}\n" + "\n".join(EXAMPLE_LINES),
}

CLOSING_PARAGRAPH = (
    "A closing paragraph that says something worth keeping about how this skill "
    "decides what to flag and what it leaves alone entirely.\n"
)


def test_a_worked_example_scores_the_same_in_every_container():
    """DIRECTION (a), as an equivalence: green on a real undeclared cut.

    Deleting a paragraph and putting a worked example in its place is the byte
    arbitrage move 3 exists to stop, and it is one trade however the example is
    written. Spelled as a plain fence it fires. Spelled BLOCK-QUOTED, byte for
    byte the same example, it scored as prose, netted against the cut, and the
    gate passed the removal it fires on in the other spelling.

    Asserted as "all eight spellings score identically" rather than as eight
    separate fire counts, because the defect is precisely that one of them
    scored differently -- and an equivalence cannot be satisfied by a detector
    that has stopped firing at all, which the floor assertion underneath pins.

    The last two spellings are the second round of this: the same trade written
    with the example sitting directly under the heading rather than under a
    blank line. It scored prose -25 against the other six's prose 22 / code -15
    and the gate passed it -- on the real file, deleting
    web-interface-guidelines-review's Verification rule 5, the #197 casualty the
    detector's own docstring names as why it exists. Adding them here rather
    than writing a bespoke test is the point: the equivalence was already the
    right assertion, and the fixture set was what could not see the class.
    """
    before = skill("Intro paragraph here.\n\n" + CLOSING_PARAGRAPH)
    scored = {}
    for name, block in SPELLINGS.items():
        after = skill("Intro paragraph here.\n\n" + block + "\n")
        loss = cpr.Loss(before, after)
        scored[name] = (tuple(sorted(loss.scopes.items())), loss.net)
        assert len(cpr.run(case("alpha", before, after))) == 1, name

    assert len(set(scored.values())) == 1, scored
    (scopes, _net) = scored["fenced"]
    assert dict(scopes)["prose"] > cpr.FLOOR["prose"], scopes
    assert dict(scopes)["code"] < 0, "the example really did land in the code"


def test_wrapping_an_example_in_a_block_quote_is_free():
    """DIRECTION (b), and the worse one: red on a layout-only change.

    Putting `> ` in front of an existing fenced example changes no word. The
    gate scored the block out of the code scope and into the prose scope, so it
    reported words lost from the code examples that were still in the file --
    and the only remedy it could print was a ledger row declaring those words
    safe to lose when none were lost. Following the printed instruction meant
    writing a false entry into a permanent, append-only record. An escape hatch
    that cannot be opened honestly is a bypass with extra steps.

    Both directions of the wrap, because the gate is symmetric and unwrapping
    is the same edit backwards.
    """
    plain = SPELLINGS["fenced"]
    quoted = SPELLINGS["quoted fence"]
    loose = skill("Intro paragraph here.\n\n" + plain + "\n\nOutro.\n")
    wrapped = skill("Intro paragraph here.\n\n" + quoted + "\n\nOutro.\n")

    assert sorted(cpr.words(loose)) == sorted(cpr.words(wrapped)), "layout only"
    for before, after in ((loose, wrapped), (wrapped, loose)):
        loss = cpr.Loss(before, after)
        assert loss.scopes == {"frontmatter": 0, "prose": 0, "code": 0}, loss.scopes
        assert cpr.run(case("alpha", before, after)) == []


def test_a_fence_opened_inside_a_quote_does_not_extend_past_it():
    """The container that closed takes its open blocks with it.

    Left dormant instead of discarded, the fence inside the quote is still open
    when a LATER quote starts, and every line of that one reads as code -- text
    nobody edited, rescoped by a blank line somewhere above it.
    """
    body = (
        "> ```\n"
        "> quoted_code(here)\n"
        "\n"
        "Outro paragraph here.\n"
        "\n"
        "> an ordinary quoted sentence\n"
    )
    scopes = cpr.split_scopes(skill(body))
    assert "quoted_code(here)" in scopes["code"]
    assert "Outro paragraph here." in scopes["prose"], scopes["prose"]
    assert "an ordinary quoted sentence" in scopes["prose"], scopes["prose"]


def test_a_fence_opened_outside_a_quote_is_not_entered():
    """The other direction, and the reason a fence outranks a marker.

    Everything inside a fenced block is literal, so a `>` on a line in one is a
    markdown example the author typed. Peeling it there hands the line to a
    container that does not exist, leaves the real fence open for the rest of
    the file, and rescopes everything below it.
    """
    body = (
        "Intro.\n"
        "\n"
        "```\n"
        "> not a quote, just markdown inside an example\n"
        "```\n"
        "\n"
        "Outro paragraph here.\n"
    )
    scopes = cpr.split_scopes(skill(body))
    assert "not a quote, just markdown inside an example" in scopes["code"]
    assert "Outro paragraph here." in scopes["prose"], scopes["prose"]


def test_four_spaces_before_a_marker_is_code_and_not_a_quote():
    """`QUOTE_RE`'s indent bound is CommonMark's three, and it is what says a
    quoted line inside an indented example is the example's own content. A
    marker matched at any indent would peel it into a container of its own and
    move it back into the prose scope -- the founding evasion again, reached
    by quoting a `>` inside the block.
    """
    body = "Intro.\n\n    > a quoted line inside an indented example\n"
    scopes = cpr.split_scopes(skill(body))
    assert "a quoted line inside an indented example" in scopes["code"]
    assert scopes["prose"].strip().endswith("Intro."), scopes["prose"]


def test_a_quote_inside_a_list_item_keeps_the_item_s_content_column():
    """A container boundary drops the LEAF state and keeps the list nesting.

    Dropping the list columns too would measure the four spaces from the left
    margin again for every line after a quote, so a nested item's own paragraph
    becomes code the moment somebody quotes something above it -- the false
    positive the second CommonMark rule exists to stop, reintroduced through
    the container.
    """
    body = (
        "1. Outer step.\n"
        "\n"
        "   > A quote inside the step.\n"
        "\n"
        "      A continuation six spaces in, still the step's own prose.\n"
    )
    scopes = cpr.split_scopes(skill(body))
    assert "still the step's own prose." in scopes["prose"], scopes["prose"]
    assert scopes["code"].strip() == "", scopes["code"]


def test_what_a_closed_quote_left_open_decides_what_the_next_line_opens():
    """The container boundary, in the three shapes that tell its halves apart.

    A quote ends at the first line with no marker on it -- unless that line
    would not start a block of its own, in which case it continues the quote's
    open PARAGRAPH instead. So what the quote's last block was decides whether
    four spaces underneath it are a code block or a wrapped line, and the
    parent's own indented block is closed by the marker either way.

    Each case below was adjudicated against markdown-it-py rather than reasoned
    out, and each falls to a different half of `reopen`: assuming a boundary
    always breaks the second, assuming never breaks the first, and keeping the
    parent's indented block breaks the third.
    """
    for body, code_lines, prose_lines in (
        # The quote's last block is a fence, so it leaves nothing to continue
        # and the four spaces open a code block.
        (
            "Intro paragraph.\n"
            "> ```\n"
            "> quoted_code()\n"
            "> ```\n"
            "    an_indented_block()\n",
            ["quoted_code()", "an_indented_block()"],
            ["Intro paragraph."],
        ),
        # The quote's last block is a paragraph, so the next line is its own
        # wrapped text however far it is indented.
        (
            "Intro paragraph.\n> - a quoted bullet\n    an_indented_block()\n",
            [],
            ["a quoted bullet", "an_indented_block()"],
        ),
        # The marker closed the indented block that was open OUTSIDE the quote,
        # so the four spaces after it do not resume it.
        (
            "    code_line_one()\n> a quote\n    code_line_two()\n",
            ["code_line_one()"],
            ["a quote", "code_line_two()"],
        ),
    ):
        scopes = cpr.split_scopes(skill(body))
        for wanted in code_lines:
            assert wanted in scopes["code"], (body, wanted, scopes)
            assert wanted not in scopes["prose"], (body, wanted, scopes)
        for wanted in prose_lines:
            assert wanted in scopes["prose"], (body, wanted, scopes)
            assert wanted not in scopes["code"], (body, wanted, scopes)


def test_a_quoted_example_is_read_at_whatever_depth_it_sits():
    """Nesting and the no-space marker are not special cases -- peeling is a
    loop over one marker, so `> > ` costs a second turn and `>` a shorter one.
    Spelled out anyway: each is a way somebody writes a quoted example, and a
    reading that stopped at one level or required the space would leave the
    evasion open one `>` further in.
    """
    for body, wanted in (
        ("> > ```\n> > deeply_quoted(code)\n> > ```\n\nOutro.\n", "deeply_quoted"),
        (">```\n>tight_quoted(code)\n>```\n\nOutro.\n", "tight_quoted"),
    ):
        scopes = cpr.split_scopes(skill(body))
        assert f"{wanted}(code)" in scopes["code"], body
        assert wanted not in scopes["prose"], body
        assert "Outro." in scopes["prose"], body


def test_a_line_with_no_marker_on_it_reads_exactly_as_it_did_before():
    """The container reading must not touch a file that has no `>` in it.

    Measured over 50,000 random documents built from a quote-free alphabet of
    blanks, paragraphs, four- and eight-space indents, tabs, fences of three
    and four characters, list markers and continuations: zero lines change
    classification. The control, with `>` lines back in the alphabet, differs on
    25,126 of 50,000. Pinned here on the shapes the two CommonMark rules turn
    on, which is what the catalog is made of.
    """
    for body in (
        "Intro.\n\n    the_worked(example, goes, here)\n",
        "Intro.\n\n```\nfenced(example)\n```\n\nOutro.\n",
        "- A step.\n\n      the_worked(example, goes, here)\n",
        "1. Outer step.\n   - Inner bullet.\n\n     A second paragraph of it.\n",
        "A paragraph whose second line is indented well past where it began,\n"
        "    which markdown renders as one paragraph and not as a code block.\n",
    ):
        text = skill(body)
        assert cpr.split_scopes(text) == _container_only_scopes(text), body


SKILLS = Path(__file__).resolve().parents[1] / "skills"


def _split_with(text: str, read) -> dict[str, str]:
    """`split_scopes` with some other reading of what a code line is.

    Spelled out here rather than imported, because the subject of the tests
    below is how the shipped reading differs from an older one -- so the older
    one has to be written down, not derived from the thing under test.
    """
    text = cpr.unwrap(text)
    m = cpr.FRONTMATTER_RE.match(text)
    assert m, "the fixture must have locatable frontmatter"
    frontmatter, body = text[: m.end()], text[m.end() :]
    prose: list[str] = []
    code: list[str] = []
    for line in body.split("\n"):
        (code if read(line) else prose).append(line)
    return {
        "frontmatter": frontmatter,
        "prose": "\n".join(prose),
        "code": "\n".join(code),
    }


def _fence_only_scopes(text: str) -> dict[str, str]:
    """The reading as it FIRST shipped: fences and nothing else."""
    return _split_with(text, cpr.Fence().feed)


def _container_only_scopes(text: str) -> dict[str, str]:
    """The reading as it stood one round ago: both spellings, no containers.

    `Container` is that reading exactly, minus the tab expansion `Code` now
    does before it peels a marker -- so the expansion is done here instead, and
    what is left is the container reading and nothing else.
    """
    container = cpr.Container()
    return _split_with(text, lambda ln: container.feed(ln.expandtabs(cpr.TAB_STOP)))


# The skills this catalog ships with a BLOCK-QUOTED worked example in them, and
# therefore the only four whose scope the container reading may move. Named
# rather than counted, because the number is what went wrong: see below.
QUOTED_EXAMPLES = {
    "api-contract-enforcement",
    "brand-voice-review",
    "pii-and-compliance",
    "test-discipline",
}


def test_only_the_files_with_a_quoted_example_change_scope():
    """THE REGRESSION THAT MATTERS, and the round that inverted what it asserts.

    It used to pin the new split to the fence-only one across all 49 files, and
    "0 of 49 move" was offered as the proof that reading a second spelling was
    safe. It was also proof that a reading was MISSING: a block quote suppressed
    both spellings at once, so the four files carrying a quoted example agreed
    with the fence-only reading because both were wrong about them. A test that
    pins a new reading to an old one goes green exactly where the old one's
    defect is inherited.

    So the assertion is not weakened to accommodate them -- it is inverted, and
    both halves are named. These four must move; the other 45 must not. Weakening
    this to "at most a few move" is how the defect survived seven rounds.
    """
    files = sorted(SKILLS.glob("*/SKILL.md"))
    assert len(files) >= 40, f"only {len(files)} SKILL.md files found -- wrong root?"

    moved = {
        path.parent.name
        for path in files
        if cpr.split_scopes(path.read_text(encoding="utf-8"))
        != _fence_only_scopes(path.read_text(encoding="utf-8"))
    }
    assert moved == QUOTED_EXAMPLES, sorted(moved ^ QUOTED_EXAMPLES)


def test_what_moved_in_those_four_is_the_quoted_example_itself():
    """The other half: that they move is not enough, it has to be the bug.

    A file could differ from the fence-only reading for any number of reasons.
    In each of these four the difference is one direction only -- lines the old
    reading scored as prose that are a code block to every renderer -- and each
    one carries a `>` and a fence, which is the shape the container reading was
    written for.
    """
    for name in sorted(QUOTED_EXAMPLES):
        text = (SKILLS / name / "SKILL.md").read_text(encoding="utf-8")
        now, before = cpr.split_scopes(text), _fence_only_scopes(text)
        gained = set(now["code"].split("\n")) - set(before["code"].split("\n"))
        gained = {ln for ln in gained if ln.strip()}
        assert gained, name
        assert all(ln.lstrip().startswith(">") for ln in gained), (name, gained)
        assert any("```" in ln for ln in gained), (name, gained)
        # Nothing went the other way: the reading only ever finds more code.
        lost = set(before["code"].split("\n")) - set(now["code"].split("\n"))
        assert not {ln for ln in lost if ln.strip()}, (name, lost)


def test_the_other_45_are_unchanged_by_the_container_reading_too():
    """The four are the whole of the difference from EITHER older reading.

    Compared against the container-less reading rather than the fence-only one,
    so this cannot pass by the two older readings happening to cancel out. The
    45 have no `>`-marked code in them at all, so the peel must be a no-op on
    every line of them.
    """
    for path in sorted(SKILLS.glob("*/SKILL.md")):
        if path.parent.name in QUOTED_EXAMPLES:
            continue
        text = path.read_text(encoding="utf-8")
        assert cpr.split_scopes(text) == _container_only_scopes(text), path


def test_the_control_the_comparisons_above_notice_a_planted_block():
    """The control, one per comparison. A comparison that could not tell two
    readings apart would pass whatever the split did, which is the shape of a
    search that finds nothing because it is the wrong search.
    """
    planted_indent = skill("Intro paragraph.\n\n" + INDENTED_EXAMPLE)
    assert cpr.split_scopes(planted_indent) != _fence_only_scopes(planted_indent)

    planted_quote = skill("Intro paragraph.\n\n" + SPELLINGS["quoted fence"] + "\n")
    assert cpr.split_scopes(planted_quote) != _fence_only_scopes(planted_quote)
    assert cpr.split_scopes(planted_quote) != _container_only_scopes(planted_quote)


def test_a_cut_beside_an_untouched_indented_example_is_charged_to_the_prose():
    """Why the reclassification costs no false positive, made checkable.

    Both revisions are split by the same rules, so a line nobody edited lands in
    the same scope on both sides and nets to zero there. What is left is the
    edit, charged where it happened -- so moving an example out of the prose
    scope cannot turn a prose cut into a code finding, or the other way round.
    """
    example = "\n" + INDENTED_EXAMPLE + "\n"
    before = skill(
        "Intro paragraph here." + example + "Mock only what you must and keep "
        "the rest of the real path in play.\n"
    )
    after = skill("Intro paragraph here." + example + "Mock only what you must.\n")

    loss = cpr.Loss(before, after)
    assert loss.scopes["code"] == 0, "the untouched example must net to zero"
    assert list(loss.over) == ["prose"], loss.scopes
    assert len(cpr.run(case("alpha", before, after))) == 1


# --- the thresholds ---------------------------------------------------------
#
# Each floor is the top of its own scope's measured noise, with the smallest
# real removal in that scope well above it. These pairs stand either side of
# each boundary, so moving one breaks a test in whichever direction it moves.


def test_two_words_lost_from_prose_is_below_the_floor():
    before = skill("alpha bravo charlie delta echo foxtrot golf hotel\n")
    after = skill("alpha bravo charlie delta echo foxtrot\n")
    assert cpr.Loss(before, after).scopes["prose"] == 2
    assert cpr.run(case("alpha", before, after)) == []


def test_three_words_lost_from_prose_fires():
    before = skill("alpha bravo charlie delta echo foxtrot golf hotel\n")
    after = skill("alpha bravo charlie delta echo\n")
    assert cpr.Loss(before, after).scopes["prose"] == 3
    assert len(cpr.run(case("alpha", before, after))) == 1


def test_a_retired_frontmatter_key_is_below_the_frontmatter_floor():
    """`review_mode: shared` is two tokens, and dropping it across the catalog
    is 31 of this repository's file-revisions -- the single largest source of
    small frontmatter losses in its history, and the noise the frontmatter
    floor is measured to sit above.
    """
    before = "---\nname: alpha\ndescription: d\nreview_mode: shared\n---\n\nBody.\n"
    after = "---\nname: alpha\ndescription: d\n---\n\nBody.\n"
    assert cpr.Loss(before, after).scopes["frontmatter"] == 2
    assert cpr.run(case("alpha", before, after)) == []


def test_three_words_lost_from_the_frontmatter_is_below_the_floor():
    """The boundary itself. Frontmatter is a YAML mapping, not prose: three
    tokens there is routinely one retired key and its value, which is why its
    floor sits a word above the prose floor rather than sharing it.
    """
    before = "---\nname: alpha\ndescription: one two three four five six\n---\n\nB.\n"
    after = "---\nname: alpha\ndescription: one two three\n---\n\nB.\n"
    assert cpr.Loss(before, after).scopes["frontmatter"] == 3
    assert cpr.run(case("alpha", before, after)) == []


def test_four_words_lost_from_the_frontmatter_fires():
    before = "---\nname: alpha\ndescription: one two three four five six\n---\n\nB.\n"
    after = "---\nname: alpha\ndescription: one two\n---\n\nB.\n"
    assert cpr.Loss(before, after).scopes["frontmatter"] == 4
    assert len(cpr.run(case("alpha", before, after))) == 1


# --- the escape hatch -------------------------------------------------------

LEDGER_HEADER = "| skill | words | why |\n|---|---|---|\n"


def declared(*rows: str) -> str:
    return LEDGER_HEADER + "".join(r if r.endswith("\n") else r + "\n" for r in rows)


def a_real_deletion(name: str = "session-heartbeat"):
    return case(name, *fixture(name)), name, HISTORICAL_LOSSES[name]


def skill_errors(*args, **kwargs) -> list[str]:
    """Only the annotations about SKILL.md files.

    `run()` also annotates the ledger itself when a change takes a merged row
    back out of it, and that is a second, separate finding. Tests whose subject
    is the verdict on a skill filter it out here and assert it where it belongs,
    rather than counting two findings as one.
    """
    return [e for e in cpr.run(*args, **kwargs) if "::error file=skills/" in e]


def test_a_row_this_change_adds_lets_the_deletion_through():
    cases, name, net = a_real_deletion()
    after = declared(f"| {name} | {net} | Moved to unattended-operation. |")
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after) == []


def test_a_row_inherited_from_the_base_does_not_count():
    """The anti-blanket rule. A row already on main is somebody else's
    declaration about somebody else's deletion; honouring it would rebuild the
    standing exemption the size gate deliberately removed.
    """
    cases, name, net = a_real_deletion()
    row = declared(f"| {name} | {net} | Moved to unattended-operation. |")
    assert len(cpr.run(cases, ledger_before=row, ledger_after=row)) == 1


def test_editing_an_inherited_rows_reason_does_not_manufacture_a_new_declaration():
    """The anti-blanket rule again, through the edit it did not cover.

    PR1 lands a row and merges. PR2 changes ONLY that row's reason -- one
    character, a typo fix, a full stop -- and separately cuts an unrelated
    paragraph of the same size from the same skill. Keyed on the whole row
    `(skill, count, reason)`, Counter subtraction sees the edited reason as a
    brand-new key, so the edit alone reads as a fresh declaration and the real
    cut rides through covered by wording nobody wrote for it. This needs no
    malice: a drive-by copyedit to an old row, in the same PR as an unrelated
    cut to that skill, silently exempts the cut.
    """
    cases, name, net = a_real_deletion()
    before = declared(f"| {name} | {net} | trimmed the intro |")
    after = declared(f"| {name} | {net} | trimmed the intro. |")  # one character
    assert len(cpr.run(cases, ledger_before=before, ledger_after=after)) == 1


def test_cli_editing_an_inherited_rows_reason_does_not_cover_an_unrelated_cut(repo, capsys):
    """The same defect, end to end through real git revisions.

    Base already carries a declared row from an earlier change (inherited,
    not added by this one). This change cuts three NEW words from the same
    skill and touches the old row only to reword it -- no row this change
    adds actually covers the new cut.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY + "kilo lima mike\n")
    (repo / "docs" / "prose-removals.md").write_text(
        declared("| alpha | 3 | trimmed the intro |")
    )
    base = commit(repo, "PR1: declare and land a 3-word cut")

    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(
        declared("| alpha | 3 | trimmed the intro. |")
    )
    commit(repo, "PR2: cut three more words, only reword the old row")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    assert "::error file=skills/alpha/SKILL.md::" in capsys.readouterr().out


# Every way to edit a row that was already in the base ledger, one per column.
# None of them adds a row, so none of them can declare anything -- which column
# the edit lands in is not part of the rule, and must not become part of it. The
# fourth-column case is here so a column added to this table later is covered
# before it exists: two rounds of review each found this hole in whichever
# column they thought to try, and each was fixed in that column alone.
INHERITED_ROW_EDITS = [
    (
        "its reason",
        "| {name} | {net} | trimmed the intro |",
        "| {name} | {net} | trimmed the intro. |",
    ),
    (
        "its count",
        "| {name} | 4 | trimmed the intro |",
        "| {name} | {net} | trimmed the intro |",
    ),
    (
        "its skill",
        "| some-other-skill | {net} | trimmed the intro |",
        "| {name} | {net} | trimmed the intro |",
    ),
    (
        "a fourth column",
        "| {name} | {net} | trimmed the intro | 2026-01-02 |",
        "| {name} | {net} | trimmed the intro | 2026-03-14 |",
    ),
    (
        # Whitespace is stripped out of every field before a row is keyed, so
        # padding one is an edit that changes nothing the gate looks at. It
        # still adds no row, so it still declares nothing.
        "its whitespace",
        "|  {name}  |  {net}  |  trimmed the intro  |",
        "| {name} | {net} | trimmed the intro |",
    ),
    (
        # `int("0900") == 900`. A leading zero changes the row's text without
        # changing the number, which is what a rule keyed on the row's TEXT
        # rather than on its value would read as a new declaration.
        "a leading zero on its count",
        "| {name} | {net} | trimmed the intro |",
        "| {name} | 0{net} | trimmed the intro |",
    ),
    (
        # `int("9_00") == 900` too -- Python accepts underscore separators, so
        # the text and the value part company a second way.
        "an underscore in its count",
        "| {name} | {net} | trimmed the intro |",
        "| {name} | {net_underscored} | trimmed the intro |",
    ),
    (
        "its count and its reason together",
        "| {name} | 4 | trimmed the intro |",
        "| {name} | {net} | rewrote the whole section |",
    ),
    (
        "its skill, its count and a fourth column together",
        "| some-other-skill | 4 | trimmed the intro | 2026-01-02 |",
        "| {name} | {net} | trimmed the intro | 2026-03-14 |",
    ),
]


def _row_fields(name: str, net: int) -> dict[str, object]:
    digits = str(net)
    return {
        "name": name,
        "net": net,
        "net_underscored": f"{digits[0]}_{digits[1:]}" if len(digits) > 1 else digits,
    }


@pytest.mark.parametrize(
    "before_row,after_row",
    [(b, a) for _f, b, a in INHERITED_ROW_EDITS],
    ids=[f for f, _b, _a in INHERITED_ROW_EDITS],
)
def test_editing_an_inherited_row_declares_nothing(before_row, after_row):
    """The anti-blanket rule, stated over the row rather than over a column.

    A row inherited from the base is somebody else's declaration. Editing one
    adds nothing, so it declares nothing -- whichever field the edit touches.
    Keyed on any part of a row's text, Counter subtraction reads the edited row
    as the old one vanishing and an unrelated one appearing, and the change gets
    a free declaration it never wrote.

    The count column is the dangerous one, and it is why this test is about the
    row and not about a column: an edit to the reason could only ever cover a
    cut as large as the inherited count, but an edit to the count covers any
    number the author cares to type.
    """
    cases, name, net = a_real_deletion()
    fields = _row_fields(name, net)
    before = declared(before_row.format(**fields))
    after = declared(after_row.format(**fields))

    # Control: both ledgers really do carry one parsed row. Without this, "the
    # gate fired" is equally explained by a row the parser never read at all --
    # which is a different mechanism and would leave the hole open.
    assert sum(cpr.parse_ledger(before).values()) == 1, before
    assert sum(cpr.parse_ledger(after).values()) == 1, after

    assert len(skill_errors(cases, ledger_before=before, ledger_after=after)) == 1


@pytest.mark.parametrize(
    "after_row",
    [a for _f, _b, a in INHERITED_ROW_EDITS],
    ids=[f for f, _b, _a in INHERITED_ROW_EDITS],
)
def test_the_discriminator_the_same_row_genuinely_added_is_credited(after_row):
    """The other half of the test above, and the reason it is evidence.

    "The gate fired" is equally explained by a rule that credits nothing ever.
    Each row the test above edits into place is written here as a row the change
    actually ADDS to a ledger that did not have it, and every one of them has to
    be honoured -- otherwise the append-only rule is not a rule, it is an
    outage.
    """
    cases, name, net = a_real_deletion()
    row = after_row.format(**_row_fields(name, net))
    assert (
        cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=declared(row)) == []
    ), row


def test_an_added_row_cannot_launder_an_edit_to_an_inherited_rows_count():
    """Adding a row does not license editing a different one.

    A rule that asks only whether the skill's row COUNT grew is satisfied by one
    throwaway row -- `| alpha | 1 | fixed a typo |` -- while the number that
    actually covers the cut comes from an inherited row whose count was edited
    upward in the same breath. The row that grew the total and the row that
    covers the cut have to be the same row.
    """
    cases, name, net = a_real_deletion()
    before = declared(f"| {name} | 4 | an earlier trim |")
    after = declared(
        f"| {name} | {net} | an earlier trim |", f"| {name} | 1 | fixed a typo |"
    )
    assert len(skill_errors(cases, ledger_before=before, ledger_after=after)) == 1


def test_editing_an_inherited_rows_reason_does_not_void_an_unrelated_declaration():
    """The matched pair for the two rules above, in the free direction.

    A change may not be CREDITED for editing an inherited row; it must not be
    PUNISHED for it either. A drive-by copyedit to an old row -- a typo, a full
    stop -- alongside a genuine new declaration of your own is ordinary, and the
    genuine row still stands. This is what dropping the reason before comparing
    buys: with the reason still in the key the copyedit reads as a withdrawn
    row, and withdrawing a row is what voids the credit.
    """
    cases, name, net = a_real_deletion()
    before = declared("| some-other-skill | 3 | an earlier trim |")
    after = declared(
        "| some-other-skill | 3 | an earlier trim. |",
        f"| {name} | {net} | The routing rule moved to the policy skill. |",
    )
    assert cpr.run(cases, ledger_before=before, ledger_after=after) == []


def test_cli_editing_an_inherited_rows_count_does_not_cover_an_unrelated_cut(
    repo, capsys
):
    """The count-column defect end to end through real git revisions.

    Base already carries a declared row from an earlier change. This change cuts
    three NEW words from the same skill and touches the old row only to raise
    its number -- one character, zero rows added, and the cut is covered.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY + "kilo lima mike\n")
    (repo / "docs" / "prose-removals.md").write_text(
        declared("| alpha | 1 | trimmed the intro |")
    )
    base = commit(repo, "PR1: declare and land a 1-word cut")

    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(
        declared("| alpha | 3 | trimmed the intro |")
    )
    commit(repo, "PR2: cut three more words, only raise the old row's number")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    assert "::error file=skills/alpha/SKILL.md::" in capsys.readouterr().out


def test_the_error_says_the_record_was_rewritten_when_that_is_why_it_fired():
    """An author who edited an old row instead of adding one sees a row in the
    ledger that covers their cut and a gate that fails anyway. The message has
    to name the reason, or the only way out of it is guessing.
    """
    cases, name, net = a_real_deletion()
    before = declared(f"| {name} | 4 | an earlier trim |")
    after = declared(f"| {name} | {net} | an earlier trim |")
    (error,) = skill_errors(cases, ledger_before=before, ledger_after=after)
    assert "back OUT of docs/prose-removals.md" in error, error


def test_a_second_removal_of_the_same_size_can_be_declared_again():
    """The hatch has to open twice.

    Keyed on (skill, count) alone, a skill that had already declared an 11-word
    cut could never declare another: the author followed the printed
    instruction exactly, git showed the row added by their change, and the gate
    failed anyway and reprinted the same instruction. That is a bypass with
    extra steps -- and it was the default case, not an exotic one, since 35 of
    the 49 skills carry two or more bullets of identical word length.
    """
    cases, name, net = a_real_deletion()
    first = f"| {name} | {net} | First cut: the quiet-mode flags moved out. |"
    second = f"| {name} | {net} | Second cut: restated in the routing section. |"
    assert (
        cpr.run(
            cases,
            ledger_before=declared(first),
            ledger_after=declared(first, second),
        )
        == []
    )


def test_a_verbatim_identical_second_row_is_still_a_new_declaration():
    """Rows count with multiplicity, not as a set.

    Two cuts of the same size from the same skill, for the same stated reason,
    are two declarations. Deduplicating them means the second author's row is
    invisible to the gate even though git shows they added it -- the same
    deadlock as keying on (skill, count), reached a different way.
    """
    cases, name, net = a_real_deletion()
    row = f"| {name} | {net} | Superseded by the policy skill. |"
    assert (
        cpr.run(cases, ledger_before=declared(row), ledger_after=declared(row, row))
        == []
    )


def test_a_row_that_understates_the_cut_does_not_count():
    """The count cannot be written blind. Declaring 5 to cover 500 is exactly
    what this rule exists to stop.
    """
    cases, name, net = a_real_deletion()
    after = declared(f"| {name} | {net - 1} | Moved to unattended-operation. |")
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_a_row_that_covers_more_than_the_cut_still_counts():
    """The count is a floor, not an equality.

    A later commit in the same pull request that ADDS words shrinks the net
    below the number already declared. Demanding an exact match makes the most
    ordinary event in a PR's life -- answering a reviewer -- the thing that
    turns the gate red again with a new number, and the row that finally merges
    then describes a diff nobody read.
    """
    cases, name, net = a_real_deletion()
    after = declared(f"| {name} | {net + 30} | Declared before the last review round. |")
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after) == []


def test_a_row_for_a_different_skill_does_not_count():
    cases, _name, net = a_real_deletion()
    after = declared(f"| some-other-skill | {net} | Unrelated. |")
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_a_row_with_no_reason_does_not_count():
    """An undeclared declaration is not one."""
    cases, name, net = a_real_deletion()
    for empty in (f"| {name} | {net} |  |", f"| {name} | {net} | - |"):
        after = declared(empty)
        assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_the_printed_row_pasted_unedited_does_not_count():
    """The hatch is cheap, not automatic. Pasting the failure's own row without
    saying why declares nothing, and that is the one cost it has to keep.
    """
    cases, name, net = a_real_deletion()
    after = declared(cpr.ledger_row(name, net))
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_a_backticked_skill_name_in_the_row_still_counts():
    """People write skill names in backticks everywhere else in this repo."""
    cases, name, net = a_real_deletion()
    after = declared(f"| `{name}` | {net} | Moved to unattended-operation. |")
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after) == []


def test_a_worked_example_of_the_table_declares_nothing():
    """The ledger documents its own format, and a doc that shows a filled-in
    table shows a filled-in table.

    Parsed with no fence awareness, an illustrative example is a live
    declaration -- so the hatch could be used while the real table stayed
    empty, which defeats the record the hatch exists to leave. Table anchoring
    alone does not cover this: the example carries its own header.
    """
    cases, name, net = a_real_deletion()
    after = (
        LEDGER_HEADER
        + "\nA filled-in table looks like this:\n\n```markdown\n"
        + LEDGER_HEADER
        + f"| {name} | {net} | example row |\n```\n"
    )
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_a_row_written_outside_the_table_declares_nothing():
    """Parsing is anchored to the table, so prose further down the document
    that happens to be pipe-shaped is not a declaration.
    """
    cases, name, net = a_real_deletion()
    after = LEDGER_HEADER + f"\nSome later prose.\n\n| {name} | {net} | stray row |\n"
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_a_worked_example_ABOVE_the_table_declares_nothing_and_does_not_shadow_it():
    """The arrangement the ledger's own example was written in, and the one the
    fence reading is actually load-bearing for.

    Below the table a fenced example is already out of scope, because the fence
    line ends the table. Above it, a fence that is not read opens the table on
    the EXAMPLE's header -- so the example's rows declare for real and, since
    only the first table counts, the table a reader would actually write into is
    dead. Both halves are asserted, because either one alone is survivable.
    """
    cases, name, net = a_real_deletion()
    ledger = (
        "A filled-in table looks like this:\n\n```markdown\n"
        + LEDGER_HEADER
        + f"| {name} | {net} | example row |\n```\n\n"
        + LEDGER_HEADER
    )
    assert cpr.parse_ledger(ledger) == {}, "the fenced example declared something"
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=ledger)) == 1

    real = ledger + f"| {name} | {net} | Moved to unattended-operation. |\n"
    assert cpr.parse_ledger(real) == {(name, net): 1}, "the real table went dead"
    assert cpr.run(cases, ledger_before=ledger, ledger_after=real) == []


def test_a_commented_out_draft_ABOVE_the_table_declares_nothing_either():
    """The same arrangement through an HTML comment: an older draft kept above
    the live table opens it on the draft's header if comments are not read.
    """
    cases, name, net = a_real_deletion()
    ledger = (
        "<!-- an older draft, kept for reference:\n"
        + LEDGER_HEADER
        + f"| {name} | {net} | an old draft |\n-->\n\n"
        + LEDGER_HEADER
    )
    assert cpr.parse_ledger(ledger) == {}, "the commented draft declared something"
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=ledger)) == 1

    real = ledger + f"| {name} | {net} | Moved to unattended-operation. |\n"
    assert cpr.parse_ledger(real) == {(name, net): 1}, "the real table went dead"
    assert cpr.run(cases, ledger_before=ledger, ledger_after=real) == []


def test_an_INDENTED_draft_ABOVE_the_table_declares_nothing_either():
    """The same arrangement through markdown's other spelling of a code block,
    which is the one this parser did not read.

    An indented example is a code block to every renderer, so nothing on the
    rendered page distinguishes it from the fenced one above -- but its header
    was the FIRST `| skill | words | why |` in the document, so `seen_table`
    latched onto the example and the real table under it was dead. A row added
    exactly where this file instructs then declared nothing and the failure
    reprinted the row the author had just written. An escape hatch that cannot
    be opened is a bypass with extra steps.
    """
    cases, name, net = a_real_deletion()
    ledger = (
        "A filled-in table looks like this:\n\n"
        "    | skill | words | why |\n"
        "    |---|---|---|\n"
        f"    | {name} | {net} | example row |\n\n"
        "Rows go in the table at the bottom of this file.\n\n" + LEDGER_HEADER
    )
    assert cpr.parse_ledger(ledger) == {}, "the indented example declared something"
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=ledger)) == 1

    real = ledger + f"| {name} | {net} | Moved to unattended-operation. |\n"
    assert cpr.parse_ledger(real) == {(name, net): 1}, "the real table went dead"
    assert cpr.run(cases, ledger_before=ledger, ledger_after=real) == []


def test_an_indented_row_after_a_blank_separator_is_a_code_block_not_a_row():
    """The one boundary reading the second spelling MOVES in the ledger, pinned
    with both halves of its control rather than left to be discovered.

    Four spaces after a blank line is a code block to every renderer, so such a
    line shows a reader monospaced literal text and not a table row -- and a
    declaration a reader would never see is not one. The two arrangements an
    author actually produces are unaffected and are asserted here beside it: a
    row pasted after a blank separator with no indent still counts (which is the
    case this parser was fixed for once already), and an indented row directly
    under the table still counts, because nothing can open a code block there.
    """
    cases, name, net = a_real_deletion()
    row = f"| {name} | {net} | Moved to unattended-operation. |"

    inert = LEDGER_HEADER + "\n    " + row + "\n"
    assert cpr.parse_ledger(inert) == {}, "an indented block declared something"
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=inert)) == 1

    after_blank = LEDGER_HEADER + "\n" + row + "\n"
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after_blank) == []

    hard_against = LEDGER_HEADER + "    " + row + "\n"
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=hard_against) == []


def test_a_commented_out_table_declares_nothing():
    cases, name, net = a_real_deletion()
    after = (
        LEDGER_HEADER
        + "\n<!-- an older draft of the table, kept for reference:\n"
        + LEDGER_HEADER
        + f"| {name} | {net} | commented out |\n-->\n"
    )
    assert len(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)) == 1


def test_the_ledger_header_is_not_mistaken_for_a_declaration():
    assert cpr.parse_ledger(LEDGER_HEADER) == {}


def test_one_row_clears_one_file_and_leaves_the_others():
    cases = {}
    for name in HISTORICAL_LOSSES:
        cases.update(case(name, *fixture(name)))
    after = declared(
        f"| session-heartbeat | {HISTORICAL_LOSSES['session-heartbeat']} | Deliberate. |"
    )
    errors = cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=after)
    assert len(errors) == 2
    assert not any("session-heartbeat" in e for e in errors)


def test_the_error_prints_the_exact_row_to_paste():
    """The hatch is only cheap if the failure hands you the row. Paste what the
    error prints, replace the placeholder, and the gate passes.

    Split on `cpr.ROW_INTRO` rather than on a copy of that phrase: the detector
    owns the sentence that introduces the row, and a test carrying its own copy
    of it stops finding the row the moment the sentence is reworded -- which is
    a remedy nothing checks, not a passing test.
    """
    cases, name, net = a_real_deletion()
    (error,) = cpr.run(cases)
    assert "docs/prose-removals.md" in error

    printed = error.split(cpr.ROW_INTRO)[1]
    assert printed == cpr.ledger_row(name, net)

    real = printed.replace(
        "<why these words are gone>", "Superseded by the policy skill."
    )
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=declared(real)) == []


def test_the_shipped_ledger_declares_nothing_yet():
    """The file committed with this gate is a header and a rule, not a list of
    exemptions. If a row is ever added, it was added by a change that needed it.
    """
    repo_root = Path(__file__).resolve().parents[1]
    ledger = repo_root / "docs" / "prose-removals.md"
    assert ledger.exists(), "the gate names a ledger that must exist to be usable"
    assert cpr.parse_ledger(ledger.read_text(encoding="utf-8")) == {}


def test_the_shipped_ledger_carries_the_table_the_parser_anchors_to():
    """The control for the test above.

    `parse_ledger` returning nothing is only evidence the ledger is empty if
    the parser can find its table at all -- otherwise a renamed header reads as
    "no declarations" forever, and so does every row anyone ever adds.
    """
    repo_root = Path(__file__).resolve().parents[1]
    text = (repo_root / "docs" / "prose-removals.md").read_text(encoding="utf-8")
    probe = text.rstrip("\n") + "\n| probe-skill | 7 | control row |\n"
    assert cpr.parse_ledger(probe) == {("probe-skill", 7): 1}


# --- a line that does not parse still occupies a slot -----------------------
#
# THE CLASS. Everything above counts PARSED rows, so the append-only rule is an
# invariant over the parse rather than over the file -- and every rule that
# makes `parse_ledger` drop a line is therefore a staging slot. Park a row where
# the parser cannot see it, in a change that merges; make it visible here; and
# the ledger gains a declaration while the covering row sits in this change's
# diff as unchanged context. Cardinality never notices, because the row was
# never counted at base.
#
# Eight predicates dropped a line -- a fence, an HTML comment, no header yet, a
# rule row, a row that does not match, a blank or placeholder reason, a count
# that is not a number, and a second header re-opening the table -- and patching
# any subset of them repeats the round this one was convened to end. The fix has
# to be the shape of the accounting, not the list: every line occupies a slot,
# whether or not it parses, so the total is a property of the FILE and no edit
# to the parse can move it.
#
# Each case below is a matched pair. `->live` is the attack: the staged line is
# made to parse, and no row may be credited for it. `inert` is the control: the
# same staged line, untouched on both sides, next to a row the change really did
# write -- which must still be honoured, or the fix is an outage rather than a
# rule.

ROW = "| {name} | {net} | Moved to unattended-operation. |"

# STAGED  the row is parked where the parser cannot read it, and the change
#         makes it readable. That flip must buy nothing.
# INHERIT the construct no longer hides anything, so the row is an ordinary
#         inherited declaration at both revisions -- which also buys nothing,
#         by the rule that was already there. Two of these were staging slots
#         before this round and are not any more, and saying which is which is
#         the difference between a fix and a coincidence.
# SEALED  the construct never publishes the row at all, at either revision.
STAGED, INHERIT, SEALED = "staged", "inherited", "sealed"

# (label, what the base ledger stages, what the head ledger turns it into, what
#  the head ledger then shows a reader)
STAGING_SLOTS = [
    (
        "inside a fenced block",
        LEDGER_HEADER + "```markdown\n" + ROW + "\n```\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "inside a longer fence a shorter one does not close",
        LEDGER_HEADER + "````markdown\n```\n" + ROW + "\n````\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "inside an indented code block",
        LEDGER_HEADER + "\nAn example:\n\n    " + ROW + "\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "inside an HTML comment",
        LEDGER_HEADER + "<!--\n" + ROW + "\n-->\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "above the header, before the table opens",
        ROW + "\n" + LEDGER_HEADER,
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "shaped like the table's rule row",
        LEDGER_HEADER + "|---|---|---|\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "a row missing its third cell",
        LEDGER_HEADER + "| {name} | {net}\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "a reason still on the printed placeholder",
        LEDGER_HEADER + "| {name} | {net} | <why these words are gone> |\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "a blank reason",
        LEDGER_HEADER + "| {name} | {net} |  |\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "a count that is not a number",
        LEDGER_HEADER + "| {name} | forty-nine | Moved to unattended-operation. |\n",
        LEDGER_HEADER + ROW + "\n",
        STAGED,
    ),
    (
        "below prose the change then deletes",
        LEDGER_HEADER + "\nA later section.\n\n" + ROW + "\n",
        LEDGER_HEADER + "\n\n" + ROW + "\n",
        STAGED,
    ),
    (
        # A malformed row used to end the table, hiding every row under it. It
        # does not any more: the table ends where markdown ends it, so this row
        # is published at both revisions and fixing the broken one above it
        # publishes nothing new.
        "a row below a malformed row that used to hide it",
        LEDGER_HEADER + "| broken\n" + ROW + "\n",
        LEDGER_HEADER + "| broken | row | here |\n" + ROW + "\n",
        INHERIT,
    ),
    (
        # A blank line used to end the table. It does not any more, for the same
        # reason an author's pasted row after a blank separator has to be read.
        "below a blank line the change then deletes",
        LEDGER_HEADER + "\n" + ROW + "\n",
        LEDGER_HEADER + ROW + "\n",
        INHERIT,
    ),
    (
        # A second header re-opened the table, so any table anywhere in the
        # document was live. Only the first one counts now, so this row is
        # never published at all.
        "under a second header further down the document",
        LEDGER_HEADER + "\nA later section.\n\n" + ROW + "\n",
        LEDGER_HEADER + "\nA later section.\n\n" + LEDGER_HEADER + ROW + "\n",
        SEALED,
    ),
]


def _staged(template: str, name: str, net: int) -> str:
    return template.format(name=name, net=net)


@pytest.mark.parametrize(
    "before_ledger,after_ledger,shows",
    [(b, a, s) for _f, b, a, s in STAGING_SLOTS],
    ids=[f for f, _b, _a, _s in STAGING_SLOTS],
)
def test_a_line_the_parser_had_dropped_cannot_become_a_declaration(
    before_ledger, after_ledger, shows
):
    """The attack direction, one per acceptance predicate.

    The base ledger already carries the row, in a form this gate does not read.
    The change makes it readable and nothing else -- no row is written in this
    diff. Every one of these was a green run before the slot accounting landed.
    """
    cases, name, net = a_real_deletion()
    before = _staged(before_ledger, name, net)
    after = _staged(after_ledger, name, net)

    # Control on the premise, stated per case rather than assumed. "The gate
    # fired" is worth nothing without knowing WHICH construct the head ledger
    # publishes: a flip that is still credited, a row that was inherited all
    # along, and a row nobody can publish are three different results.
    assert cpr.parse_ledger(before)[(name, net)] == (1 if shows == INHERIT else 0)
    assert cpr.parse_ledger(after)[(name, net)] == (0 if shows == SEALED else 1)

    assert len(skill_errors(cases, ledger_before=before, ledger_after=after)) == 1


@pytest.mark.parametrize(
    "before_ledger",
    [b for _f, b, _a, _s in STAGING_SLOTS],
    ids=[f for f, _b, _a, _s in STAGING_SLOTS],
)
def test_the_control_an_untouched_inert_line_does_not_block_a_real_row(before_ledger):
    """The free direction, and the reason the test above is evidence.

    A rule that credited nothing would pass every case above. Here the same
    staged line sits unchanged in both ledgers -- a fenced example, a commented
    draft, a malformed row nobody has fixed -- while the change writes a row
    into the table, and that row still counts.
    """
    cases, name, net = a_real_deletion()
    before = _staged(before_ledger, name, net)
    row = _staged(ROW, name, net) + "\n"
    after = before.replace(LEDGER_HEADER, LEDGER_HEADER + row, 1)
    assert after != before, "the control did not actually add a row"
    assert cpr.run(cases, ledger_before=before, ledger_after=after) == []


def test_every_line_of_the_ledger_occupies_a_slot():
    """The property the class fix rests on, stated directly on the accounting.

    The total is the file's non-blank line count, which no change to what parses
    can move. That is what turns the append-only rule from an invariant over the
    PARSE -- where a line becoming readable is a free row -- into one over the
    FILE.
    """
    text = (
        LEDGER_HEADER
        + "| alpha | 5 | a real row |\n"
        + "| broken\n"
        + "\n"
        + "Some prose.\n"
        + "```\n| beta | 6 | fenced |\n```\n"
        + "<!-- | gamma | 7 | commented | -->\n"
    )
    non_blank = [ln for ln in text.split("\n") if ln.strip()]
    assert sum(cpr.ledger_slots(text).values()) == len(non_blank)


def test_the_append_only_rule_holds_over_every_small_ledger_pair():
    """Exhaustive, not asserted: with the same number of non-blank lines on both
    sides, a surplus row without a withdrawal is impossible.

    `withdrawn` empty means head has at least as many slots of every identity as
    base; equal totals then force the two multisets to be equal, so there is no
    surplus at all. Searched rather than argued, because the argument only holds
    while the accounting stays total -- and it is exactly the totality that four
    rounds of column patches did not have.
    """
    alphabet = [
        "| alpha | 5 | a reason |",
        "| alpha | 6 | a reason |",
        "| beta | 5 | a reason |",
        "|---|---|---|",
        "| skill | words | why |",
        "<!-- | alpha | 5 | a reason | -->",
        "```",
        "Some prose.",
    ]
    import itertools

    def ledgers(n):
        for combo in itertools.product(alphabet, repeat=n):
            yield LEDGER_HEADER + "".join(ln + "\n" for ln in combo)

    def rows(slots):
        return {s: n for s, n in slots.items() if s[0] == "row"}

    checked = violations = 0
    for n in range(4):
        cached = [cpr.ledger_slots(t) for t in ledgers(n)]
        for before in cached:
            for after in cached:
                checked += 1
                if rows(after - before) and not (before - after):
                    violations += 1
    assert checked > 250_000, f"the search only compared {checked} pairs"
    assert violations == 0, f"{violations} of {checked} pairs bought a free row"


def test_the_control_the_search_above_can_see_a_violation():
    """The control for the search. A search that finds nothing may be the wrong
    search, so run it against a case that must hit: let head carry one extra
    line and the equal-cardinality premise is gone, which is precisely when a
    surplus without a withdrawal is possible.
    """
    alphabet = [
        "| alpha | 5 | a reason |",
        "|---|---|---|",
        "<!-- | alpha | 5 | a reason | -->",
        "Some prose.",
    ]
    import itertools

    def slots(n):
        return [
            cpr.ledger_slots(LEDGER_HEADER + "".join(ln + "\n" for ln in combo))
            for combo in itertools.product(alphabet, repeat=n)
        ]

    found = 0
    for before in slots(1):
        for after in slots(2):
            if {s for s in (after - before) if s[0] == "row"} and not (before - after):
                found += 1
    assert found > 0, "the search cannot see a violation, so finding none proves nothing"


def test_a_change_that_only_reformats_the_table_declares_nothing():
    """A schema change to the table is not a declaration, and does not have to
    be one: widening the header and the rule row costs nothing and buys nothing.
    """
    cases, name, net = a_real_deletion()
    before = LEDGER_HEADER + f"| {name} | {net} | an earlier trim |\n"
    after = (
        "| skill | words | why | declared |\n"
        "|---|---|---|---|\n"
        f"| {name} | {net} | an earlier trim | 2026-03-14 |\n"
    )
    assert cpr.parse_ledger(after)[(name, net)] == 1, "the wider table still parses"
    assert len(skill_errors(cases, ledger_before=before, ledger_after=after)) == 1


def test_a_column_added_to_the_header_does_not_disable_the_hatch():
    """The append-only rule's own comment promises it survives "a column added
    to this table years from now". Anchored to a three-column header exactly,
    adding one stopped the parser finding the table at all -- so every row in it
    went silent and the hatch could not be opened by anybody.
    """
    cases, name, net = a_real_deletion()
    wide = "| skill | words | why | declared |\n|---|---|---|---|\n"
    after = wide + f"| {name} | {net} | Moved to unattended-operation. | 2026-03-14 |\n"
    assert cpr.run(cases, ledger_before=wide, ledger_after=after) == []


# --- the record stands ------------------------------------------------------


def test_taking_a_merged_row_back_out_of_the_ledger_fails_on_its_own():
    """"Rows stay after they merge" was asserted by the ledger and enforced
    nowhere: a change that removed every row while touching no SKILL.md went
    green, because a withdrawal only ever voided the change's OWN declarations
    and this change had none to void.
    """
    kept = declared("| alpha | 5 | an earlier trim |", "| beta | 9 | another |")
    errors = cpr.run({}, ledger_before=kept, ledger_after=LEDGER_HEADER)
    assert len(errors) == 1, errors
    assert errors[0].startswith("::error file=docs/prose-removals.md::")
    assert "alpha" in errors[0] and "beta" in errors[0]


def test_the_control_a_ledger_nothing_was_removed_from_is_silent():
    """The control. A change that only ADDS rows to the ledger, touching no
    SKILL.md, is ordinary and must stay silent.
    """
    before = declared("| alpha | 5 | an earlier trim |")
    after = declared("| alpha | 5 | an earlier trim |", "| beta | 9 | another |")
    assert cpr.run({}, ledger_before=before, ledger_after=after) == []


def test_copyediting_an_inherited_rows_reason_is_not_taking_it_out():
    """A row's identity is its skill and its count, so wording is free to be
    fixed. Otherwise "the record stands" would make a typo unfixable.
    """
    before = declared("| alpha | 5 | an earlier trim |")
    after = declared("| alpha | 5 | an earlier trim. |")
    assert cpr.run({}, ledger_before=before, ledger_after=after) == []


def test_a_second_table_further_down_declares_nothing_at_either_revision():
    """"That table only", made true. A second `| skill | words | why |` header
    re-opened parsing, so a table anywhere in the document was live -- and the
    rule the ledger states about itself was false in both directions.
    """
    cases, name, net = a_real_deletion()
    second = (
        LEDGER_HEADER
        + "\nAn appendix of rows we decided against:\n\n"
        + LEDGER_HEADER
        + f"| {name} | {net} | never agreed |\n"
    )
    assert cpr.parse_ledger(second) == {}
    assert len(skill_errors(cases, ledger_before=LEDGER_HEADER, ledger_after=second)) == 1


# --- the hatch opens --------------------------------------------------------


def test_a_row_appended_to_the_real_shipped_ledger_opens_the_hatch():
    """The live failure, against the file in this repository as it stands.

    Its table is the last thing in the file, so appending is what an author
    does. A blank line between the rule row and the new row -- the shape a
    `>>` or an editor's trailing newline produces -- ended the table, the row
    went unread, and the gate failed and reprinted the row the author had just
    written. An escape hatch that cannot be opened is a bypass with extra steps.
    """
    cases, name, net = a_real_deletion()
    shipped = (Path(__file__).resolve().parents[1] / "docs" / "prose-removals.md").read_text(
        encoding="utf-8"
    )
    row = f"| {name} | {net} | Moved to unattended-operation. |"
    for separator in ("", "\n", "\n\n"):
        after = shipped + separator + row + "\n"
        assert cpr.run(cases, ledger_before=shipped, ledger_after=after) == [], (
            f"separator {separator!r} left the row unread"
        )


def test_the_failure_never_reprints_a_row_the_author_already_wrote():
    """The property behind the test above, stated so it cannot regress into
    some other separator. If the gate prints a row to paste, pasting it must
    end the failure.
    """
    cases, name, net = a_real_deletion()
    shipped = (Path(__file__).resolve().parents[1] / "docs" / "prose-removals.md").read_text(
        encoding="utf-8"
    )
    (error,) = cpr.run(cases, ledger_before=shipped, ledger_after=shipped)
    printed = error.split(cpr.ROW_INTRO)[1]
    filled = printed.replace(cpr.REASON_PLACEHOLDER, "Moved to unattended-operation.")
    assert cpr.run(cases, ledger_before=shipped, ledger_after=shipped + "\n" + filled + "\n") == []


def test_rewriting_the_ledgers_own_prose_voids_the_rows_the_change_adds():
    """The price of counting the file rather than the parse, pinned deliberately
    so it reads as a decision and not as a surprise.

    Every non-blank line of the ledger is a slot, prose included, because the
    line that ENDS the table decides which rows are inside it -- delete it and
    rows below become declarations nobody wrote. So an unrelated edit to this
    file's own prose, in the same change as a genuine row, is a withdrawal and
    voids it. Loud, explicable, and the message says which: separate the two
    changes, or put the line back. The alternative -- keying prose lines by
    anything coarser than their text -- makes them fungible, and one added line
    of prose then pays for a row published out of a line the diff shows as
    unchanged context.
    """
    cases, name, net = a_real_deletion()
    before = "Two lines of\nintroduction here.\n\n" + LEDGER_HEADER
    after = "One line of introduction here.\n\n" + LEDGER_HEADER + (
        f"| {name} | {net} | Moved to unattended-operation. |\n"
    )
    (error,) = skill_errors(cases, ledger_before=before, ledger_after=after)
    assert "back OUT of docs/prose-removals.md" in error, error
    assert "Put back what it removed" in error, error

    # The control: the same row, with the prose left alone, is honoured.
    untouched = before + f"| {name} | {net} | Moved to unattended-operation. |\n"
    assert cpr.run(cases, ledger_before=before, ledger_after=untouched) == []


def test_the_first_failure_tells_the_author_to_replace_the_placeholder():
    """The row the failure hands over is one the gate will reject.

    `ledger_row` fills the reason with `REASON_PLACEHOLDER` and `_declaration`
    rejects precisely that -- correctly, since somebody deciding the words are
    safe to lose is the one thing this hatch has to cost. So the sentence that
    hands the row over has to say so, or it is an instruction that does not
    work, printed by the gate whose own docstring calls an escape hatch that
    cannot be opened a bypass with extra steps.
    """
    cases, _name, _net = a_real_deletion()
    (error,) = cpr.run(cases)
    assert cpr.REASON_PLACEHOLDER in error
    assert "replaced by the reason" in error, error


def test_pasting_the_printed_row_does_not_reprint_the_same_failure(repo, capsys):
    """The loop, pinned on the two screens the author actually saw.

    Round 1 printed `| alpha | 7 | <why these words are gone> |` and closed with
    "Add the row printed above ... and this gate passes". Round 2, after the
    author did exactly that and no more, was the SAME RUN BYTE FOR BYTE -- no
    mention of the placeholder, of filling anything in, or of what had changed.
    Nothing tells them the row they just pasted is the one thing being rejected.

    Asserted on whole stdout rather than on a phrase, because the identity of
    the two screens is what an author is stuck in: a proxy assertion on some
    phrase goes green the moment any incidental byte differs.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    base = commit(repo, "base")

    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    commit(repo, "cut it down")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    first = capsys.readouterr().out
    printed = first.split(cpr.ROW_INTRO)[1].split("\n")[0]
    assert printed == cpr.ledger_row("alpha", 7), first

    # The author does exactly what the failure said, and no more.
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER + printed + "\n")
    commit(repo, "paste the row the gate printed, unedited")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    second = capsys.readouterr().out
    assert second != first, (
        "the second failure is byte-identical to the first, so acting on the "
        f"message told the author nothing:\n{second}"
    )
    assert cpr.REASON_PLACEHOLDER in second
    assert "replace the placeholder with the reason" in second, second

    # The control. The same paste with the reason written in reaches green, so
    # the failure above is about the placeholder and not about the paste -- and
    # the two steps the two messages asked for do end the loop.
    (repo / "docs" / "prose-removals.md").write_text(
        LEDGER_HEADER
        + printed.replace(cpr.REASON_PLACEHOLDER, "Superseded by the dispatcher.")
        + "\n"
    )
    commit(repo, "fill the reason in")
    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0, capsys.readouterr().out


def test_the_first_message_alone_is_enough_to_reach_green(repo, capsys):
    """One step, not two. The test above proves the loop is broken once the
    author pastes unedited; this one proves they never have to.

    An author who does what the FIRST failure says -- paste the row with the
    placeholder replaced -- passes without seeing a second failure at all.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    base = commit(repo, "base")

    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    commit(repo, "cut it down")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    printed = capsys.readouterr().out.split(cpr.ROW_INTRO)[1].split("\n")[0]

    (repo / "docs" / "prose-removals.md").write_text(
        LEDGER_HEADER
        + printed.replace(cpr.REASON_PLACEHOLDER, "Superseded by the dispatcher.")
        + "\n"
    )
    commit(repo, "do exactly what the first failure said")
    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0, capsys.readouterr().out


def test_no_row_is_printed_when_the_ledger_already_shows_one_covering_the_cut():
    """"Add this row" is the message being wrong about the reader's own diff.

    A row covering the cut is on their screen, in the file the message names, and
    the message hands them a row keyed the same way to add underneath it. Two
    ledgers reach this and neither is exotic: an inherited row, and the author's
    own row voided by something they took out of that file in the same change.
    `Loss.excerpt` already names being wrong about the reader's own diff as how
    a gate stops being read.
    """
    cases, name, net = a_real_deletion()
    inherited = declared(f"| {name} | {net} | an earlier trim |")
    (error,) = skill_errors(cases, ledger_before=inherited, ledger_after=inherited)
    assert cpr.ledger_row(name, net) not in error, error
    assert "already shows a row covering this cut" in error, error

    voided_before = "Two lines of\nintroduction here.\n\n" + LEDGER_HEADER
    voided_after = "One line of introduction here.\n\n" + LEDGER_HEADER + (
        f"| {name} | {net} | Moved to unattended-operation. |\n"
    )
    (error,) = skill_errors(
        cases, ledger_before=voided_before, ledger_after=voided_after
    )
    assert cpr.ledger_row(name, net) not in error, error
    assert "already shows a row covering this cut" in error, error


def test_the_control_the_row_is_still_printed_when_the_ledger_shows_nothing():
    """The discriminator for the test above. A rule that never printed a row
    would satisfy it, and would be the deadlock this hatch exists to avoid.
    """
    cases, name, net = a_real_deletion()
    for ledger_after in (
        LEDGER_HEADER,  # nothing at all
        declared(f"| {name} | {net - 1} | too small to cover it |"),
        declared(f"| some-other-skill | {net} | a different skill |"),
    ):
        (error,) = skill_errors(
            cases, ledger_before=LEDGER_HEADER, ledger_after=ledger_after
        )
        assert cpr.ledger_row(name, net) in error, error


def test_filling_in_the_placeholder_is_only_offered_when_it_would_actually_work():
    """The remedy is TESTED before it is printed, not asserted.

    A row pasted from the failure sits in the ledger AND the change took a line
    out of that file: filling the placeholder in clears nothing, because while
    anything is missing no row the change adds counts. Offering "replace the
    placeholder with the reason" as the remedy there is the same defect one
    layer along -- an instruction that does not reach green. `hatch_state` runs
    the filled ledger back through the same credit rules the verdict came from,
    so what it offers is what it has just checked.
    """
    cases, name, net = a_real_deletion()
    before = "Two lines of\nintroduction here.\n\n" + LEDGER_HEADER
    after = "One line of introduction here.\n\n" + LEDGER_HEADER + (
        cpr.ledger_row(name, net) + "\n"
    )
    assert cpr.hatch_state(before, after, name, net) == cpr.ABSENT

    (error,) = skill_errors(cases, ledger_before=before, ledger_after=after)
    assert cpr.DRAFT_INTRO not in error, error
    assert cpr.SLOTS_WITHDRAWN in error, error

    # The control: the same paste with the ledger's prose left alone IS the
    # drafted state, so the refusal above is about the withdrawal and not about
    # the detection having stopped working.
    untouched = before + cpr.ledger_row(name, net) + "\n"
    assert cpr.hatch_state(before, untouched, name, net) == cpr.DRAFTED


def test_the_message_explains_a_withdrawal_even_when_no_added_row_covers_the_cut():
    """The remedy has to be true of the failure the author is looking at.

    The explanation was printed only when a row in the surplus would otherwise
    have covered the cut. Any other author who had taken something out of the
    ledger was told to "add the row printed above and this gate passes" -- which
    is false while a withdrawal stands, because no row they add can count.
    """
    cases, name, net = a_real_deletion()
    before = declared("| some-other-skill | 3 | an earlier trim |")
    after = declared(f"| {name} | {net - 1} | too small to cover it |")
    (error,) = skill_errors(cases, ledger_before=before, ledger_after=after)
    assert "back OUT of docs/prose-removals.md" in error, error


# --- message voice ----------------------------------------------------------


def test_the_error_is_a_github_annotation_naming_the_file():
    cases, name, _net = a_real_deletion()
    (error,) = cpr.run(cases)
    assert error.startswith(f"::error file=skills/{name}/SKILL.md::")


def test_the_error_says_what_is_free_so_the_rule_is_learnable():
    """The repo's messages explain why the rule exists and what to do. Without
    this, an author's first read is "the gate hates my reformatting".
    """
    cases, _name, _net = a_real_deletion()
    (error,) = cpr.run(cases)
    for phrase in ("score zero here", "content, not layout", "deliberate"):
        assert phrase in error, f"missing {phrase!r} from: {error}"


def test_the_error_names_which_part_of_the_file_lost_the_words():
    """Three scopes means the author has to be told which one fired. "You lost
    12 words" over a file whose body is untouched is a riddle.
    """
    before = skill_file("alpha", "one two three four five six seven eight", "Body.\n")
    after = skill_file("alpha", "one two", "Body.\n")
    (error,) = cpr.run(case("alpha", before, after))
    assert "6 from its frontmatter" in error


def test_the_breakdown_adds_up_to_the_number_the_ledger_row_carries():
    """A part below its floor still lost words, and the total the author is
    told to declare includes them. Listing only the parts that fired leaves the
    breakdown short of the total, and the reader guessing which is real.
    """
    before = skill_file("alpha", "one two three four five", "Nine ten eleven twelve.\n")
    after = skill_file("alpha", "one two three", "Nine ten.\n")
    loss = cpr.Loss(before, after)
    assert loss.scopes["frontmatter"] == 2, "below the frontmatter floor"
    assert loss.scopes["prose"] == 2, "below the prose floor on its own"
    # Neither part fires on its own, so nothing is reported at all.
    assert cpr.run(case("alpha", before, after)) == []

    bigger = skill_file("alpha", "one two three", "Nine.\n")
    loss = cpr.Loss(before, bigger)
    (error,) = cpr.run(case("alpha", before, bigger))
    assert f"lost {loss.net} words" in error
    parts = [int(p.split()[0]) for p in loss.breakdown().split(", ")]
    assert sum(parts) == loss.net, f"{loss.breakdown()} does not total {loss.net}"


def test_the_remedy_block_is_true_of_the_metric_it_gates(repo, capsys):
    """The one user-facing surface that had no test at all.

    It used to tell an author over the size limit to "rewrite the section
    tighter rather than cutting it -- a rewrite that says the same thing in
    fewer words scores zero here". False of a word-multiset metric: fewer
    words IS fewer words, by construction. Measured against the shipped
    detector, a real tightening rewrite ("In order to make sure that the
    reviewer is able to understand the finding, you should always be certain
    to include the exact file and the exact line number in every single
    comment that you write." -> "Cite the exact file and line in every
    comment so the reviewer can check it.") nets 21 and fires. An author who
    did exactly what the message said, then re-pushed, hit the identical
    failure -- the escape hatch this design argues against, landed on its own
    primary advice.
    """
    before, after = (
        skill(
            "In order to make sure that the reviewer is able to understand the "
            "finding, you should always be certain to include the exact file "
            "and the exact line number in every single comment that you write.\n"
        ),
        skill(
            "Cite the exact file and line in every comment so the reviewer can "
            "check it.\n"
        ),
    )
    assert cpr.Loss(before, after).net == 21, "the tightening rewrite must fire"

    (repo / "skills" / "alpha" / "SKILL.md").write_text(before)
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(after)
    commit(repo, "tighten the section")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = capsys.readouterr().out

    for false_claim in ("rewrite the section", "Reach for deletion", "in fewer words"):
        assert false_claim not in out, f"the remedy still claims {false_claim!r}: {out}"

    # What genuinely scores zero must be named, and only that.
    assert "tightening" in out
    assert "docs/prose-removals.md" in out


# --- the guidance closes on the failure it is under -------------------------
#
# One closing line served every failure mode: "Add the row printed above to
# docs/prose-removals.md in this same change and this gate passes." It was false
# on every mode but one. Three of them print no row at all -- a file whose
# frontmatter cannot be located, a blob that would not come back, a ledger the
# change rewound -- and on the fourth the row it printed carried the placeholder
# `_declaration` rejects. Each case below is a failure and the line under it.


def flat(text: str) -> str:
    """Whitespace-normalised. The guidance block is hard-wrapped, so a sentence
    that has to be in it can land either side of a line break.
    """
    return " ".join(text.split())


def test_the_guidance_does_not_ask_for_a_row_where_no_row_was_printed(repo, capsys):
    """A SKILL.md whose frontmatter cannot be located gets no verdict and no
    row. Closing with "add the row printed above" over it points at nothing.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(
        "# Title\n\nA body with no frontmatter block at all.\n"
    )
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(
        "# Title\n\nA body with no frontmatter block at all.\n\nAnd another line.\n"
    )
    commit(repo, "edit a file this gate cannot scope")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = flat(capsys.readouterr().out)
    assert "row printed above" not in out, out
    assert "Open each file named above with a `---` line" in out, out


def test_the_guidance_does_not_ask_for_a_row_when_the_ledger_was_rewound(repo, capsys):
    """A change that takes a merged row back out fails on its own, with no
    SKILL.md involved. There is no row to paste, and no cut to declare.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(
        declared("| beta | 9 | an earlier trim |")
    )
    base = commit(repo, "base carries a merged row")
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    commit(repo, "wipe the ledger, touch no skill")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = flat(capsys.readouterr().out)
    assert "row printed above" not in out, out
    assert "Put the row(s) named above back into docs/prose-removals.md" in out, out


def test_the_guidance_asks_for_the_reason_when_the_row_is_already_pasted(repo, capsys):
    """The mode this whole fix is for, read at the closing line rather than in
    the annotation: the row is there, the placeholder is not filled in, and
    "add the row printed above" is an instruction the author already followed.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    (repo / "docs" / "prose-removals.md").write_text(
        LEDGER_HEADER + cpr.ledger_row("alpha", 7) + "\n"
    )
    commit(repo, "cut it down and paste the printed row unedited")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = flat(capsys.readouterr().out)
    assert "row printed above" not in out, out
    assert f"Replace {cpr.REASON_PLACEHOLDER} on the row already in" in out, out


def test_the_control_the_guidance_does_ask_for_the_row_when_there_is_one(repo, capsys):
    """The discriminator for the three above. A block that never mentioned the
    row would satisfy all of them and would have deleted the remedy instead of
    correcting it.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    commit(repo, "cut it down")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = flat(capsys.readouterr().out)
    assert "Add the row printed above to docs/prose-removals.md" in out, out
    assert f"with {cpr.REASON_PLACEHOLDER} replaced by the reason" in out, out


def test_the_guidance_does_not_promise_green_while_a_withdrawal_stands():
    """"and this gate passes" is a claim, and a withdrawal makes it false: while
    anything is missing from the ledger no row the change adds counts at all.
    """
    cases, name, net = a_real_deletion()
    held = cpr.remedies(
        cpr.run(
            cases,
            ledger_before=declared("| some-other-skill | 3 | an earlier trim |"),
            ledger_after=declared(f"| {name} | {net - 1} | too small to cover it |"),
        )
    )
    assert not any("this gate passes" in line for line in held), held
    assert any("Put back every line this change took out" in line for line in held), held

    # The control: with nothing withdrawn the promise is true, and is made.
    free = cpr.remedies(cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=LEDGER_HEADER))
    assert any("this gate passes" in line for line in free), free


def test_the_guidance_does_not_promise_green_over_a_file_it_could_not_scope():
    """The same claim, on the mode the ledger's two did not cover.

    "and this gate passes" is about the RUN, not about one finding, and the run
    exits 1 while any finding stands. A change that cuts prose from one skill
    and carries another whose frontmatter cannot be located gets two
    annotations; the promise was withheld only for a ledger withdrawal, so this
    author was told that adding the row was the whole cost and got exit 1 for
    doing exactly that. The remedy is checked here rather than asserted, the way
    `hatch_state` checks the drafted one.
    """
    cases, name, net = a_real_deletion()
    broken = "# Title\n\nA body with no frontmatter block at all.\n"
    both = {**cases, **case("bravo", broken, broken + "and one more line.\n")}
    row = declared(f"| {name} | {net} | Moved to unattended-operation. |")

    lines = cpr.remedies(cpr.run(both))
    assert any("Add the row printed above" in line for line in lines), lines
    assert any("Open each file named above" in line for line in lines), lines
    assert not any("this gate passes" in line for line in lines), lines
    assert cpr.run(both, ledger_before=LEDGER_HEADER, ledger_after=row), (
        "the row really does leave this run red -- otherwise the promise was "
        "true and this test is about nothing"
    )

    # The control: the same cut on its own promises green, and reaches it.
    alone = cpr.remedies(cpr.run(cases))
    assert any("this gate passes" in line for line in alone), alone
    assert cpr.run(cases, ledger_before=LEDGER_HEADER, ledger_after=row) == []


def test_the_guidance_does_not_ask_for_a_second_row_that_would_not_count_either():
    """A change whose own covering row is voided by a withdrawal is told to put
    the ledger back -- not to write another row, which would be voided too.

    The inherited case is the one where a new row IS the answer, and the two
    read almost identically in the ledger, so the remedy is keyed on which of
    them the annotation said rather than on the state being recomputed.
    """
    cases, name, net = a_real_deletion()
    voided = cpr.remedies(
        cpr.run(
            cases,
            ledger_before="Two lines of\nintroduction here.\n\n" + LEDGER_HEADER,
            ledger_after="One line of introduction here.\n\n"
            + LEDGER_HEADER
            + f"| {name} | {net} | Moved to unattended-operation. |\n",
        )
    )
    assert not any("as a NEW row" in line for line in voided), voided
    assert any("Put back every line this change took out" in line for line in voided), voided

    # The control: an inherited row really is answered by a new row of your own.
    inherited = declared(f"| {name} | {net} | an earlier trim |")
    lines = cpr.remedies(
        cpr.run(cases, ledger_before=inherited, ledger_after=inherited)
    )
    assert any("as a NEW row" in line for line in lines), lines


def test_the_guidance_closes_with_something_even_for_an_unmarked_error():
    """A block that closes with a remedy for a failure that did not happen is
    the defect; closing with nothing at all is the same defect, quieter.
    """
    assert cpr.remedies(["::error::an annotation carrying no known marker"]) == [
        cpr.NO_REMEDY
    ]


def test_the_control_every_failure_this_gate_emits_is_marked():
    """The control for the fallback above. `NO_REMEDY` is only ever a backstop
    if every mode the gate actually produces selects a real line -- otherwise
    the backstop is the message and nothing says so.
    """
    cases, name, net = a_real_deletion()
    broken = "# Title\n\nA body with no frontmatter block at all.\n"
    modes = {
        "undeclared, ledger empty": cpr.run(cases),
        "undeclared, row pasted unedited": cpr.run(
            cases,
            ledger_before=LEDGER_HEADER,
            ledger_after=LEDGER_HEADER + cpr.ledger_row(name, net) + "\n",
        ),
        "undeclared, covering row inherited": cpr.run(
            cases,
            ledger_before=declared(f"| {name} | {net} | an earlier trim |"),
            ledger_after=declared(f"| {name} | {net} | an earlier trim |"),
        ),
        "undeclared, plus a withdrawal": cpr.run(
            cases,
            ledger_before=declared("| some-other-skill | 3 | an earlier trim |"),
            ledger_after=declared(f"| {name} | {net - 1} | too small |"),
        ),
        "the ledger rewound, no skill touched": cpr.run(
            {}, ledger_before=declared("| alpha | 5 | a trim |"), ledger_after=LEDGER_HEADER
        ),
        "frontmatter refused": cpr.run(case("alpha", broken, broken + "one more.\n")),
        "a blob that would not come back": [
            f"::error file=skills/alpha/SKILL.md{cpr.UNREADABLE_BLOB} between "
            "the two revisions, but its content at HEAD could not be read."
        ],
    }
    for label, errors in modes.items():
        assert errors, f"{label}: produced no annotation, so it is not a mode"
        lines = cpr.remedies(errors)
        assert cpr.NO_REMEDY not in lines, f"{label} fell through to the backstop"


def test_the_error_does_not_claim_nothing_replaced_the_words():
    """It used to assert "and nothing replaced them" on every failure --
    including the commonest one, tightening prose, where the replacement is
    sitting on the adjacent `+` line. An author whose first encounter with a
    gate is a message that is wrong about their own diff learns to distrust it,
    which is the route-around this design is trying to avoid.
    """
    cases, _name, _net = a_real_deletion()
    (error,) = cpr.run(cases)
    assert "nothing replaced them" not in error


def test_the_excerpt_is_withheld_when_no_single_passage_explains_the_loss():
    """Scattered tightening has no "Gone:" passage to quote. Quoting the
    best-scoring block regardless meant quoting text still present in the file.
    """
    before = skill(
        "\n".join(
            f"Sentence {i} really does say something quite particular here indeed."
            for i in range(8)
        )
    )
    after = skill(
        "\n".join(f"Sentence {i} says something particular." for i in range(8))
    )
    loss = cpr.Loss(before, after)
    assert loss.net > cpr.FLOOR["prose"]
    assert loss.excerpt() == "(no single passage accounts for it -- read the diff)"


def test_the_excerpt_is_quoted_when_one_passage_does_explain_the_loss():
    """The control for the test above: the gate must still name what went when
    a single block accounts for it, which is the case authors need most.
    """
    before = skill(
        "Load the skill first.\n"
        "Findings must cite every one of the skills they rest on, each time.\n"
        "Then report.\n"
    )
    after = skill("Load the skill first.\nThen report.\n")
    assert "Findings must cite" in cpr.Loss(before, after).excerpt()


# --- scope ------------------------------------------------------------------


def test_only_paths_handed_in_are_checked():
    """`run()` compares what `collect()` gives it."""
    assert cpr.run({}) == []


@pytest.mark.parametrize(
    "path,is_a_skill",
    [
        ("skills/alpha/SKILL.md", True),
        ("skills/alpha/reference.md", False),
        ("skills/alpha/nested/SKILL.md", False),
        ("README.md", False),
        ("docs/prose-removals.md", False),
    ],
)
def test_only_skill_files_are_in_scope(path, is_a_skill):
    """Widened to any `.md`, this gate calls a trimmed README a SKILL.md and
    prints a ledger row for a skill named "" -- the false-positive direction,
    which is the one that gets a gate routed around.
    """
    assert bool(cpr.SKILL_GLOB_RE.match(path)) is is_a_skill


# --- the git plumbing and CLI -----------------------------------------------


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    )
    return out.stdout


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A throwaway git repo shaped like this one: skills/<name>/SKILL.md plus
    the ledger. The CLI resolves paths against the cwd, so chdir into it.
    """
    r = tmp_path / "repo"
    (r / "skills" / "alpha").mkdir(parents=True)
    (r / "docs").mkdir()
    git(r.parent, "init", "-q", str(r))
    git(r, "config", "user.email", "t@example.com")
    git(r, "config", "user.name", "t")
    monkeypatch.chdir(r)
    return r


def commit(r: Path, message: str) -> str:
    git(r, "add", "-A")
    git(r, "commit", "-q", "-m", message)
    return git(r, "rev-parse", "HEAD").strip()


BODY_TEXT = "alpha bravo charlie delta echo foxtrot golf hotel india juliet\n"
BODY = skill(BODY_TEXT)

# Long enough that git's rename detection has something to match on.
LONG_BODY = (
    "---\nname: {name}\ndescription: A skill about one particular thing.\n---\n\n"
    "# Title\n\nThe first paragraph explains the rule and why it is the rule.\n\n"
    "The second paragraph gives the worked example and the counter-example.\n\n"
    "The third paragraph says what to do when the rule does not apply here.\n"
)


def test_cli_passes_when_nothing_was_lost(repo, capsys):
    """Two skills present, one touched. The count in the success line is a
    claim about what was compared, so it is pinned: without the unchanged-file
    guard the gate reports every skill in the repository as changed, and that
    line is the only evidence anyone reads on a green run.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "skills" / "untouched").mkdir()
    (repo / "skills" / "untouched" / "SKILL.md").write_text(BODY)
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY + "kilo lima mike\n")
    commit(repo, "add words")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0
    out = capsys.readouterr().out
    assert "No undeclared prose removal" in out
    assert "OK: 1 changed SKILL.md file(s)" in out, out


def test_cli_fails_on_an_undeclared_removal(repo, capsys):
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    commit(repo, "cut it down")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    assert "::error file=skills/alpha/SKILL.md::" in capsys.readouterr().out


def test_cli_passes_once_the_ledger_row_lands_in_the_same_change(repo, capsys):
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    base = commit(repo, "base")

    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    (repo / "docs" / "prose-removals.md").write_text(
        declared("| alpha | 7 | Superseded by the dispatcher. |")
    )
    commit(repo, "cut it down, declared")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0, capsys.readouterr().out


def test_cli_ignores_a_ledger_row_that_was_already_on_the_base(repo):
    """The anti-blanket rule again, this time through real git revisions."""
    row = declared("| alpha | 7 | Superseded by the dispatcher. |")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(row)
    base = commit(repo, "base carries the row already")

    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    commit(repo, "cut it down, riding an inherited row")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1


def rename_skill(repo: Path, old: str, new: str, text: str) -> None:
    (repo / "skills" / new).mkdir()
    (repo / "skills" / old / "SKILL.md").rename(repo / "skills" / new / "SKILL.md")
    (repo / "skills" / old).rmdir()
    (repo / "skills" / new / "SKILL.md").write_text(text)


def test_cli_catches_a_deletion_hidden_behind_a_rename(repo, capsys):
    """Renaming a skill takes its path out of both sides of the comparison.

    Keyed on paths, the gate then compared nothing at all and printed
    "0 changed SKILL.md file(s)" over a real deletion -- reporting success for
    a comparison it never made, which is the failure its own base-resolution
    guard exists to prevent. Renaming is documented ordinary practice here, and
    it is exactly the moment content goes missing.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(LONG_BODY.format(name="alpha"))
    base = commit(repo, "base")

    cut = LONG_BODY.format(name="beta").replace(
        "The second paragraph gives the worked example and the counter-example.\n\n", ""
    )
    rename_skill(repo, "alpha", "beta", cut)
    commit(repo, "rename the skill and drop a paragraph")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = capsys.readouterr().out
    assert "::error file=skills/beta/SKILL.md::" in out
    assert "worked example" in out, "the error should quote what the rename hid"


def test_cli_control_a_rename_that_loses_nothing_is_free(repo, capsys):
    """The control for the test above: renaming without cutting anything has to
    stay silent, or nobody can rename a skill.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(LONG_BODY.format(name="alpha"))
    base = commit(repo, "base")

    rename_skill(repo, "alpha", "beta", LONG_BODY.format(name="beta"))
    commit(repo, "rename the skill, keep every word")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0
    out = capsys.readouterr().out
    # The frontmatter `name:` moves with the directory, so this is a real
    # content change that happens to lose nothing -- it is compared, and it
    # passes.
    assert "OK: 1 changed SKILL.md file(s)" in out, out


def test_cli_a_byte_identical_rename_is_not_counted_as_a_change(repo, capsys):
    """git lists a 100%-similar rename as changed while the bytes are the same.

    That is the one path that reaches the guard keeping `cases` to files whose
    content actually moved, and it is what makes the count in the success line
    mean "content changed" rather than "paths git mentioned". (A stale `name:`
    is `validate-skills`' business, not this gate's.)
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(LONG_BODY.format(name="alpha"))
    base = commit(repo, "base")

    rename_skill(repo, "alpha", "beta", LONG_BODY.format(name="alpha"))
    commit(repo, "move the directory, touch not one byte of the file")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0
    assert "OK: 0 changed SKILL.md file(s)" in capsys.readouterr().out


def test_cli_ignores_a_new_skill_and_a_deleted_one(repo, capsys):
    """Whole-file adds and deletes are out of scope -- git renders them as a
    file appearing or disappearing, which review cannot miss -- but the gate
    says how many it skipped rather than printing a bare OK over them.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    base = commit(repo, "base")

    (repo / "skills" / "alpha" / "SKILL.md").unlink()
    (repo / "skills" / "gamma").mkdir()
    # Nothing in common with alpha but the frontmatter keys, and long enough
    # that git's 25% rename detection cannot pair the two: this test is about
    # an add plus a delete, and a pairing would quietly turn it into a rename
    # test that happens to still pass.
    (repo / "skills" / "gamma" / "SKILL.md").write_text(
        skill_file(
            "gamma",
            "Wholly unrelated: quixotic zephyr marmalade thimble.",
            "\n".join(f"unrelated{i} sentence about nothing alpha ever said." for i in range(20)),
        )
    )
    commit(repo, "swap one skill for another")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0
    out = capsys.readouterr().out
    assert "1 added and 1 deleted whole" in out, out


def test_cli_ignores_a_shrinking_file_that_is_not_a_skill(repo, capsys):
    """Scope, through the real diff. A trimmed README is not this gate's
    business, and calling one a SKILL.md prints a row for a skill named "".
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "README.md").write_text(
        "One two three four five six seven eight nine ten eleven twelve.\n"
    )
    base = commit(repo, "base")
    (repo / "README.md").write_text("One two.\n")
    commit(repo, "trim the readme hard")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0
    assert "OK: 0 changed SKILL.md file(s)" in capsys.readouterr().out


def test_cli_reports_an_annotated_error_on_invalid_utf8_instead_of_a_traceback(
    repo, capsys
):
    """A byte that is not valid UTF-8 must fail closed WITH an annotation.

    `_git`/`_show` decoded with `text=True`, so a stray invalid byte in a
    SKILL.md raised an uncaught `UnicodeDecodeError` that crashed the process.
    The run does exit non-zero -- fails closed, correctly -- but as a bare
    stack trace with no `::error file=...::` annotation, so CI shows no file
    annotation for it at all: the failure is real but invisible in the PR's
    Files view.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_bytes(BODY.encode())
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_bytes(
        b"Not valid UTF-8 from here: \xff\xfe\n"
    )
    commit(repo, "corrupt the file")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    cap = capsys.readouterr()
    assert "::error file=skills/alpha/SKILL.md::" in cap.out, cap.out
    assert "Traceback" not in cap.out and "Traceback" not in cap.err, cap.err


def test_cli_defaults_its_base_to_the_merge_base(repo, capsys):
    """The documented local command and CI have to compute the same number.

    Comparing against the trunk TIP attributes main's own edits to this branch:
    prose added on main after the fork reads as prose the branch deleted. The
    ledger row carries that number, so a base that disagrees with CI's makes
    the row CI demands and the row the author was told to write differ.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    git(repo, "branch", "-M", "main")
    fork = commit(repo, "base")

    git(repo, "checkout", "-q", "-b", "topic")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(
        skill("alpha bravo charlie delta echo foxtrot golf\n")
    )
    commit(repo, "the branch drops three words")

    git(repo, "checkout", "-q", "main")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(
        BODY + "kilo lima mike november oscar papa quebec romeo sierra tango\n"
    )
    commit(repo, "main gains ten words nobody on the branch touched")
    git(repo, "checkout", "-q", "topic")

    assert cpr.main([]) == 1
    default_base = capsys.readouterr().out
    assert "lost 3 words" in default_base, default_base

    assert cpr.main(["--base", "main"]) == 1
    tip_base = capsys.readouterr().out
    assert "lost 13 words" in tip_base, (
        "the trunk tip should charge this branch for main's ten words -- if it "
        "no longer does, this test has stopped demonstrating the difference"
    )

    assert cpr.main(["--base", fork]) == 1


def test_cli_defaults_its_base_to_dev_when_the_branch_forked_from_it(repo, capsys):
    """Panel repro: every branch in this repository forks from and targets
    `dev`, and `dev` routinely carries growth `main` does not have yet. A
    default that only ever tries `main` compares this branch against an
    older snapshot -- so a real cut can read as a net gain against `main`
    while it is a real loss against the actual fork point, `dev`. That is
    the dangerous direction: it prints OK where CI, which merge-bases
    against the PR's actual base, fires.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    git(repo, "branch", "-M", "main")
    commit(repo, "base")

    git(repo, "checkout", "-q", "-b", "dev")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(
        BODY + " ".join(f"kilo{i}" for i in range(60)) + "\n"
    )
    commit(repo, "dev grows the file well past main")

    git(repo, "checkout", "-q", "-b", "topic")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    commit(repo, "the branch cuts more than dev grew, back to the original text")

    git(repo, "checkout", "-q", "topic")

    # The buggy default (main only) still has to be reachable explicitly --
    # this is the wrong number CI will never ask for.
    assert cpr.main(["--base", "main"]) == 0
    stale = capsys.readouterr().out
    assert "No undeclared prose removal" in stale, stale

    assert cpr.main([]) == 1, "the default must reach the branch's real fork point"
    out = capsys.readouterr().out
    assert "lost 60 words" in out, out


def test_cli_refuses_to_pass_when_the_base_cannot_be_resolved(repo, capsys):
    """A gate that cannot resolve its base has checked nothing. Reporting
    success there is the failure this repo's coverage guard exists to stop.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    commit(repo, "base")

    assert cpr.main(["--base", "nope-not-a-ref", "--head", "HEAD"]) == 1
    out = capsys.readouterr().out
    assert "cannot resolve the base revision" in out
    assert "fetch-depth: 0" in out, "the message must name the fix"


def test_cli_control_the_same_repo_passes_with_a_real_base(repo, capsys):
    """Control-test for the test above: prove the harness can return 0, so the
    refusal is evidence about the base and not about the fixture.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    base = commit(repo, "base")
    assert cpr.main(["--base", base, "--head", "HEAD"]) == 0


def test_cli_compares_a_skill_whose_path_git_would_quote(repo, capsys):
    """`--name-status` quotes any path with a byte outside the printable ASCII
    range, so `skills/<non-ascii>/SKILL.md` arrives wrapped in double quotes and
    escaped. The path glob then does not match it, the file drops out of the
    comparison, and the run prints "OK: 0 changed SKILL.md file(s)" over a real
    deletion -- success reported for a comparison never made, which this gate's
    own `Diff` docstring says cannot happen.
    """
    name = "α-skill"
    (repo / "skills" / name).mkdir()
    (repo / "skills" / name / "SKILL.md").write_text(skill(BODY_TEXT, name))
    base = commit(repo, "base")
    (repo / "skills" / name / "SKILL.md").write_text(skill("alpha bravo charlie\n", name))
    commit(repo, "cut it down")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    assert f"::error file=skills/{name}/SKILL.md::" in capsys.readouterr().out


def test_cli_refuses_to_report_ok_over_a_file_it_could_not_read(repo, capsys, monkeypatch):
    """The other half of the docstring's promise. Whatever the reason a blob
    cannot be fetched, a file git listed as changed and this gate did not
    compare has to be named, not counted as zero.
    """
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    base = commit(repo, "base")
    (repo / "skills" / "alpha" / "SKILL.md").write_text(skill("alpha bravo charlie\n"))
    commit(repo, "cut it down")

    monkeypatch.setattr(cpr, "_show", lambda rev, path: None)
    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    out = capsys.readouterr().out
    assert "skills/alpha/SKILL.md" in out, out
    assert "OK:" not in out, out


def test_cli_catches_a_deletion_in_a_crlf_skill_file(repo, capsys):
    """End to end, through real git revisions, on the shape that passes
    `validate-skills` and defeated the scope split here: CRLF line endings, a
    deleted section, and a padded `description:` paying for it.
    """
    before, after = fixture("clud-bug-collaboration")
    padded = "\n".join(
        line + " " + " ".join(f"padding{i}" for i in range(60))
        if line.startswith("description:")
        else line
        for line in after.split("\n")
    )
    d = repo / "skills" / "clud-bug-collaboration"
    d.mkdir()
    (d / "SKILL.md").write_bytes(before.replace("\n", "\r\n").encode())
    base = commit(repo, "base")
    (d / "SKILL.md").write_bytes(padded.replace("\n", "\r\n").encode())
    commit(repo, "delete the section, pad the description")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    assert "CLUD_BUG_QUIET" in capsys.readouterr().out
