"""#191: a skill nobody is meant to subscribe to is not a coverage gap.

The placement map marks such a skill `distribution: "catalog-only"`. The census
graces it with a reason that says so; the existing grace reasons keep
precedence; an absent or unreadable map graces nothing, so the failure stays
visible. Asserted on what the reader of the digest sees, including through
`main()`, which is where the map is read.
"""

from __future__ import annotations

import json

import census_counters as cc  # conftest puts .github/scripts on sys.path

REASON = (
    "catalog-only in docs/placement-map.json "
    "(offered to no subscriber, so zero subscriptions is the declared state)"
)
GRACED = "**Graced (zero subscriptions expected):**"
GAPS = "**Coverage gaps (no grace):**"

MAP = {
    "skills": {
        "steward-notes": {"distribution": "catalog-only", "subscribers": []},
        "pick-me": {"distribution": "opt-in", "subscribers": []},
        "udts-widget": {"distribution": "catalog-only", "subscribers": []},
    }
}
CATALOG = ["steward-notes", "pick-me", "udts-widget"]


def _digest(placement_map) -> str:
    repos = {"fake-subscriber": {"read": True, "subscribed": [], "local": [], "untracked": []}}
    signals = cc.compute_signals(CATALOG, repos, placement_map)
    signals["subscription_drift"] = []
    signals["usage"] = {}
    signals["placement_divergence"] = cc.compute_placement_divergence(placement_map, repos)
    census = {
        "cycle": "census-2026-W47",
        "generated_at": "2026-11-16T12:00:00+00:00",
        "repos": repos,
        "signals": signals,
        "stale_docket": {"open_count": 0, "stale_count": 0, "stale": []},
    }
    return cc.render_digest(census)


def test_catalog_only_skill_is_graced_with_its_reason_and_not_a_gap():
    digest = _digest(MAP)
    graced = digest.split(GRACED, 1)[1]
    assert f"- `steward-notes` — {REASON}" in graced
    assert "`steward-notes`" not in digest.split(GRACED, 1)[0].split(GAPS, 1)[-1]


def test_opt_in_skill_with_zero_subscribers_stays_a_gap():
    digest = _digest(MAP)
    gaps = digest.split(GAPS, 1)[1].split(GRACED, 1)[0]
    assert "- `pick-me`" in gaps


def test_no_map_graces_nothing():
    for absent in (None, {}, {"skills": "not a mapping"}, {"skills": {"steward-notes": "oops"}}):
        digest = _digest(absent)
        gaps = digest.split(GAPS, 1)[1].split(GRACED, 1)[0] if GRACED in digest else digest.split(GAPS, 1)[1]
        assert "- `steward-notes`" in gaps, absent
        assert REASON not in digest


def test_udts_keeps_its_own_reason_over_catalog_only():
    digest = _digest(MAP)
    assert "- `udts-widget` — udts-* L2 stub" in digest
    assert f"`udts-widget` — {REASON}" not in digest


def test_main_reads_the_map_from_the_checkout(tmp_path, monkeypatch):
    """The wiring: main() reads docs/placement-map.json once and the digest it
    writes carries the grace."""
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "placement-map.json").write_text(json.dumps(MAP), encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STEWARD_TOKEN", "dummy")
    monkeypatch.setenv("OUT_DIR", str(tmp_path / "out"))
    monkeypatch.setattr(cc, "CONSUMER_REPOS", ["fake-subscriber"])
    monkeypatch.setattr(cc, "read_catalog", lambda: CATALOG)
    monkeypatch.setattr(
        cc,
        "survey_repo",
        lambda repo, token: {"read": True, "subscribed": [], "local": [], "untracked": [], "lock_subscriptions": [], "unscoped_subscriptions": []},
    )
    monkeypatch.setattr(cc, "survey_docket", lambda token, now: {"open_count": 0, "stale_count": 0, "stale": []})
    assert cc.main() == 0
    digest = (tmp_path / "out" / "digest.md").read_text(encoding="utf-8")
    assert f"- `steward-notes` — {REASON}" in digest


def test_a_malformed_placement_map_graces_nothing_and_never_raises():
    for bad in ("a string", 7, ["catalog-only"], [{"steward-notes": 1}], {"skills": "x"}, {"skills": 3}, {"skills": ["steward-notes"]}, {"skills": {"steward-notes": "catalog-only"}}, {"skills": {"steward-notes": ["catalog-only"]}}, {"skills": {"steward-notes": None}}):
        assert cc._grace_reason("steward-notes", bad) is None, bad
        digest = _digest(bad)
        assert "`steward-notes`" in digest.split(GAPS, 1)[1].split(GRACED, 1)[0], bad
