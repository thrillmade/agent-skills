"""The catalog's present name must already be in CATALOG_NAMES.

census_counters.py recognises a subscriber lock as this catalog's if its
`source` is the current name (from the run context) or any name in
CATALOG_NAMES. On the day of a rename the run context covers the new name; the
rename AFTER that only keeps locks written under it recognised if it was
appended to CATALOG_NAMES. This is the gate that makes the append impossible
to forget: in CI, GITHUB_REPOSITORY is this repository, so the test fails on
the first pull request after a rename until the new name is listed.

Deliberately reads the environment -- that is the whole check. Locally, with
no GITHUB_REPOSITORY, the fallback literal stands in for it.
"""

from __future__ import annotations

import os

import census_counters  # conftest puts .github/scripts on sys.path


def test_the_repositorys_own_name_is_listed():
    current = os.environ.get("GITHUB_REPOSITORY", "").strip() or census_counters._SELF_REPO_FALLBACK
    assert current in census_counters.CATALOG_NAMES, (
        f"{current} is not in CATALOG_NAMES in .github/scripts/census_counters.py -- "
        "append it, or locks that name it stop being drift-checkable after the next rename"
    )


def test_the_local_fallback_is_the_newest_listed_name():
    assert census_counters._SELF_REPO_FALLBACK == census_counters.CATALOG_NAMES[-1]
