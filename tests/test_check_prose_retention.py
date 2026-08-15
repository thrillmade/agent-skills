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
    before = "See `spacing-system` and `apca-contrast` for the rules."
    after = (
        "See [spacing-system](../spacing-system/SKILL.md) and "
        "[apca-contrast](../apca-contrast/SKILL.md) for the rules."
    )
    assert cpr.Loss(before, after).net == 0
    assert cpr.run(case("alpha", before, after)) == []


def test_link_back_to_backticks_is_free():
    """The reverse conversion too -- #212 did exactly this to buy budget."""
    after = "See `spacing-system` and `apca-contrast` for the rules."
    before = (
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
    assert cpr.Loss(before, after).net == 0


def test_an_anchored_conversion_cannot_mask_a_deletion():
    """The regression anchor handling exists for, as a measurement.

    Converting four backticked names to ANCHORED links is a large word gain if
    the anchors are not collapsed -- enough to swallow a real deleted clause
    and go green. That is the #197 shape exactly.
    """
    before = (
        "Read `type-scale` and `spacing-system` and `apca-contrast` and "
        "`wcag-contrast` first, and never drop the floor rule that follows.\n"
    )
    converted = (
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
    before = (
        "Source: APCA spec at [git.apcacontrast.com]"
        "(https://git.apcacontrast.com/documentation/README). The table maps "
        "directly to the ladder."
    )
    after = (
        "Source: APCA spec at git.apcacontrast.com. The table maps directly "
        "to the ladder."
    )
    assert cpr.Loss(before, after).net == 0
    assert cpr.run(case("alpha", before, after)) == []


def test_de_linking_a_repo_file_reference_is_free():
    before = "See [validate_skills.py](.github/scripts/validate_skills.py) for the limit."
    after = "See `validate_skills.py` for the limit."
    assert cpr.Loss(before, after).net == 0


def test_a_bare_url_is_not_prose():
    """An address is not a claim. Adding or dropping one scores zero, in both
    directions, so a reference that rotted can be pulled without a ledger row.
    """
    before = "The canonical reference is the spec: https://git.apcacontrast.com/docs\n"
    after = "The canonical reference is the spec:\n"
    assert cpr.Loss(before, after).net == 0
    assert cpr.Loss(after, before).net == 0


def test_a_link_that_replaces_prose_still_fires():
    """Normalisation must not become a laundry channel: swapping a sentence
    for a bare link is a deletion wearing the free transform's clothes.
    """
    before = (
        "Contrast findings cite the perceptual model and the legal baseline "
        "both, and name which one failed."
    )
    after = "See [apca-contrast](../apca-contrast/SKILL.md)."
    assert len(cpr.run(case("alpha", before, after))) == 1


# --- formatting is free -----------------------------------------------------


def test_rewrapping_a_paragraph_is_free():
    before = "One two three four five six seven eight nine ten eleven twelve.\n"
    after = "One two three four five\nsix seven eight nine\nten eleven twelve.\n"
    assert cpr.run(case("alpha", before, after)) == []


def test_reordering_sections_is_free():
    a = "## Alpha\n\nThe first section says one thing about the subject.\n"
    b = "## Beta\n\nThe second section says a different thing entirely.\n"
    assert cpr.run(case("alpha", a + "\n" + b, b + "\n" + a)) == []


def test_moving_a_line_to_another_section_is_free():
    before = "## A\n\nkeep this line here\n\n## B\n\nother content entirely\n"
    after = "## A\n\n## B\n\nother content entirely\n\nkeep this line here\n"
    assert cpr.run(case("alpha", before, after)) == []


def test_bolding_and_italicising_is_free():
    before = "Line height is floored at 1.2 across every role in the scale.\n"
    after = "**Line height** is *floored* at `1.2` across every role in the scale.\n"
    assert cpr.run(case("alpha", before, after)) == []


def test_turning_a_paragraph_into_a_list_is_free():
    before = "Check contrast then typography then spacing then tokens.\n"
    after = "- Check contrast\n- then typography\n- then spacing\n- then tokens\n"
    assert cpr.run(case("alpha", before, after)) == []


def test_a_file_that_did_not_change_is_free():
    text = "Some skill body with several words in it.\n"
    assert cpr.run(case("alpha", text, text)) == []


def test_adding_prose_is_free():
    before = "A short body.\n"
    after = "A short body.\n\nPlus a new paragraph nobody had written before.\n"
    assert cpr.run(case("alpha", before, after)) == []


def test_fixing_a_typo_is_free():
    before = "Findings must cite the skills they recieve their authority from.\n"
    after = "Findings must cite the skills they receive their authority from.\n"
    assert cpr.run(case("alpha", before, after)) == []


def test_rewording_at_similar_length_is_free():
    before = "The primary model is APCA, and WCAG serves only as a cross-check.\n"
    after = "APCA is the primary model; WCAG is nothing more than a cross-check.\n"
    assert cpr.run(case("alpha", before, after)) == []


# --- content removal fires --------------------------------------------------


def test_deleting_a_sentence_fires():
    before = (
        "Load the skill first.\n"
        "Findings must cite the skills they rest on, every time.\n"
        "Then report.\n"
    )
    after = "Load the skill first.\nThen report.\n"
    (error,) = cpr.run(case("alpha", before, after))
    assert "lost 10 words" in error


def test_replacing_a_paragraph_with_a_short_stub_fires():
    """Forty words swapped for three is a deletion, whatever replaced them."""
    before = " ".join(f"substantive{i}" for i in range(40))
    after = "see the other skill"
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


# --- the thresholds ---------------------------------------------------------
#
# Each floor is the top of its own scope's measured noise, with the smallest
# real removal in that scope well above it. These pairs stand either side of
# each boundary, so moving one breaks a test in whichever direction it moves.


def test_two_words_lost_from_prose_is_below_the_floor():
    before = "alpha bravo charlie delta echo foxtrot golf hotel\n"
    after = "alpha bravo charlie delta echo foxtrot\n"
    assert cpr.Loss(before, after).scopes["prose"] == 2
    assert cpr.run(case("alpha", before, after)) == []


def test_three_words_lost_from_prose_fires():
    before = "alpha bravo charlie delta echo foxtrot golf hotel\n"
    after = "alpha bravo charlie delta echo\n"
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
    """
    cases, name, net = a_real_deletion()
    (error,) = cpr.run(cases)
    assert "docs/prose-removals.md" in error

    printed = error.split("in this same change: ")[1]
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
    assert cpr.parse_ledger(probe) == {("probe-skill", 7, "control row"): 1}


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
    before = "\n".join(
        f"Sentence {i} really does say something quite particular here indeed."
        for i in range(8)
    )
    after = "\n".join(f"Sentence {i} says something particular." for i in range(8))
    loss = cpr.Loss(before, after)
    assert loss.net > cpr.FLOOR["prose"]
    assert loss.excerpt() == "(no single passage accounts for it -- read the diff)"


def test_the_excerpt_is_quoted_when_one_passage_does_explain_the_loss():
    """The control for the test above: the gate must still name what went when
    a single block accounts for it, which is the case authors need most.
    """
    before = (
        "Load the skill first.\n"
        "Findings must cite every one of the skills they rest on, each time.\n"
        "Then report.\n"
    )
    after = "Load the skill first.\nThen report.\n"
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


BODY = "alpha bravo charlie delta echo foxtrot golf hotel india juliet\n"

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
    (repo / "skills" / "alpha" / "SKILL.md").write_text("alpha bravo charlie\n")
    commit(repo, "cut it down")

    assert cpr.main(["--base", base, "--head", "HEAD"]) == 1
    assert "::error file=skills/alpha/SKILL.md::" in capsys.readouterr().out


def test_cli_passes_once_the_ledger_row_lands_in_the_same_change(repo, capsys):
    (repo / "skills" / "alpha" / "SKILL.md").write_text(BODY)
    (repo / "docs" / "prose-removals.md").write_text(LEDGER_HEADER)
    base = commit(repo, "base")

    (repo / "skills" / "alpha" / "SKILL.md").write_text("alpha bravo charlie\n")
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

    (repo / "skills" / "alpha" / "SKILL.md").write_text("alpha bravo charlie\n")
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
    (repo / "skills" / "gamma" / "SKILL.md").write_text(
        "Wholly unrelated words: quixotic zephyr marmalade thimble.\n"
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
        "alpha bravo charlie delta echo foxtrot golf\n"
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
