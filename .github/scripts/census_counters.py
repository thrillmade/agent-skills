#!/usr/bin/env python3
"""Deterministic skill-census counters (Mode A of the weekly census engine).

Called by `.github/workflows/skill-census.yml` once per cycle. Produces the
*mechanical* half of the census: what each consumer repo has subscribed vs.
what it carries locally, which catalog skills nobody subscribes, and which
locally-authored skills have converged across repos (the strongest promotion
signal). The *judgment* half — gap/placement/promotion verdicts — is Mode B
(`census_panel.py`), which reads this script's `census.json`.

Stdlib ONLY (base64, hashlib, json, os, re, subprocess, sys, urllib, datetime).
No pip, so the counters step runs on a bare runner before the panel step
installs the Anthropic SDK. If the panel step is skipped (no
ANTHROPIC_API_KEY), this file's `digest.md` still ships as the cycle's
deliverable. `subprocess` is used narrowly (git plumbing only — `log`/`show`
against the local checkout, see `_algo_proven_for_lineage`), never to shell
out to anything network- or input-derived.

Inputs (env):
  STEWARD_TOKEN   required — GitHub App installation token with read access
                  to the thrillmade org. Missing => exit 1 (infra-fatal).
  OUT_DIR         optional — output directory. Default: $RUNNER_TEMP/census.
  GITHUB_API_URL  optional — API base (Actions sets it). Default public API.

Outputs (written to OUT_DIR):
  census.json     machine-readable snapshot consumed by census_panel.py.
  digest.md       deterministic human-readable rendering (the Mode-B-optional
                  deliverable — always filed even when the panel is off).

Failure posture:
  - A single repo's fetch failing (network, 5xx, malformed lock) never kills
    the run — the error is collected into that repo's `error` field and
    surfaced in both census.json and the digest. Never silently dropped.
  - HTTP 404 on a contents path means "repo doesn't carry that file" and is
    tolerated as None (most repos have no skills-lock.json / .clud-bug.json).
  - exit 1 is reserved for infra-fatal conditions (missing STEWARD_TOKEN).
"""

from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone

# --- Constants -------------------------------------------------------------

# Consumer repos surveyed for subscription state. The catalog repo
# (agent-skills) is intentionally absent — it is the source, not a consumer.
CONSUMER_REPOS = (
    "clud-bug",
    "clud-bug-app",
    "logmind",
    "tokenomics",
    "protocol",
    "reporulez",
    "rezgen",
    "skdd",
)

ORG = "thrillmade"
CATALOG_REPO = "agent-skills"
CATALOG_DIR = "skills"  # read locally from the checkout cwd
CATALOG_SOURCE = f"{ORG}/{CATALOG_REPO}"  # lock `source` value for catalog subs

# Contents API paths probed per consumer repo.
LOCK_PATH = "skills-lock.json"
MANIFEST_PATH = ".claude/skills/.clud-bug.json"
LOCAL_SKILLS_DIR = ".claude/skills"
MANIFEST_FILENAME = ".clud-bug.json"  # excluded from local-dir accounting

# Placement map (authored by the placement agent; may not exist yet). Read
# locally from the checkout cwd. Cross-checked against live subscriptions.
PLACEMENT_MAP_PATH = "docs/placement-map.json"

# Grace: catalog skills that are EXPECTED to have zero subscribers, so a
# zero-subscription count for them is not a coverage gap. Two families:
#
#   1. udts-* — L2 stubs incubating in thrillmade/tokenomics, published here
#      as parity markers only ("do not treat as guidance yet"). Detected by
#      the UDTS_STUB_PREFIX below, not enumerated, so new stubs are covered
#      automatically.
#   2. STRUCTURAL_L0 — the README's L0 universal primitives + L0 design-critic
#      lenses. These are composed by the L1 dispatchers
#      (designing/reviewing/consuming-a-design-system), not subscribed
#      directly by consumer repos, so zero direct subscriptions is by design.
UDTS_STUB_PREFIX = "udts-"
STRUCTURAL_L0 = frozenset(
    {
        # L0 — universal primitives
        "oklch-color-space",
        "apca-contrast",
        "wcag-contrast",
        "chroma-harmonization",
        "palette-relationships",
        "type-scale",
        "line-height-grid",
        "spacing-system",
        "component-sizing-principles",
        "token-naming-conventions",
        "dtcg-format",
        "semver-design-tokens",
        # L0 — design-critic lenses (pair with clud-bug's design review)
        "designing-elite-ui",
        "design-system-consistency",
        "frontend-a11y",
        "visual-polish",
        "orchestrating-elite-agent-qa",
        "web-interface-guidelines-review",
    }
)

STALE_DAYS = 14  # docket issues untouched longer than this are "stale"
API_TIMEOUT = 30  # seconds per request

# --- Catalog content hashing (subscription-drift detection) ----------------
#
# skills-lock.json stores a `computedHash` per subscribed skill — a content
# hash of the catalog SKILL.md at the ref the lock pinned. A refresh that
# fetches a ref whose recomputed content hash differs MUST surface the change
# (SPEC: refresh drift). Surfacing is the census's job; it NEVER auto-fixes.
#
# The hash is produced by the EXTERNAL skills.sh CLI's own content
# normalization. We determined the algorithm empirically: every historical
# version of skills/{brand-voice-review,logmind}/SKILL.md (via `git log` +
# `git show <sha>:<path>`) was hashed with ~40 candidate algorithms — raw
# sha256, trailing-newline-stripped, per-line rstrip, CRLF->LF, git blob
# sha1/sha256, body-only (frontmatter stripped), frontmatter-only, and
# path/source/dir-concat/git-tree composites. NONE reproduced either stored
# computedHash (0488e9…brand-voice-review / 6f20f4…logmind). Conclusion: the
# normalization lives inside the skills.sh CLI and is not reproducible from
# stdlib here.
#
# DUAL MODE. The compute-and-compare path below is real and complete; it is
# gated on CATALOG_HASH_ALGO naming a registered algorithm. Because no local
# algorithm reproduces the stored hashes, CATALOG_HASH_ALGO is None today and
# every catalog subscription is reported 'indeterminate' (once per lock, with
# a reason) — we NEVER report drift we cannot prove. CATALOG_HASH_ALGO stays
# None until someone actually mirrors the skills.sh CLI's normalization into
# _HASH_ALGOS — flipping it to a wrong-but-plausible algorithm is exactly the
# failure mode this module is written to survive.
#
# PER-SKILL DRIFT PROOF (guards the day CATALOG_HASH_ALGO IS set). Even once
# an algorithm is registered, `compute_subscription_drift` never asserts
# 'drift' for a skill on the strength of the algorithm alone — see
# `_algo_proven_for_lineage`. Before calling a mismatch 'drift', it replays
# the algorithm against up to 30 historical versions of that skill's catalog
# SKILL.md (`git log` + `git show <sha>:<path>`) and requires the algorithm to
# reproduce the subscription's stored `computedHash` for at least one of
# them. If none reproduce it, the algorithm is unproven for *this skill's*
# specific pin lineage and the verdict downgrades to 'indeterminate' instead
# of 'drift' — so a single global algorithm flip can never mass-mis-flag
# subscriptions whose lineage it was never actually verified against.


def _strip_frontmatter(raw: bytes) -> bytes:
    """Return the markdown body with a leading YAML frontmatter block removed."""
    text = raw.decode("utf-8", "replace")
    m = re.match(r"^---\r?\n.*?\r?\n---\r?\n", text, re.DOTALL)
    return text[m.end():].encode("utf-8") if m else raw


def _git_blob_sha1(raw: bytes) -> str:
    h = hashlib.sha1()
    h.update(b"blob %d\x00" % len(raw))
    h.update(raw)
    return h.hexdigest()


# Registered candidate normalizations. Keys are stable names; a future
# determination sets CATALOG_HASH_ALGO to one of these (or adds a new one that
# mirrors the skills.sh CLI). Each maps raw file bytes -> hex digest.
_HASH_ALGOS = {
    "sha256_raw": lambda raw: hashlib.sha256(raw).hexdigest(),
    "sha256_rstrip_nl": lambda raw: hashlib.sha256(
        raw.decode("utf-8", "replace").rstrip("\n").encode("utf-8")
    ).hexdigest(),
    "sha256_lf": lambda raw: hashlib.sha256(
        raw.decode("utf-8", "replace").replace("\r\n", "\n").encode("utf-8")
    ).hexdigest(),
    "sha256_body": lambda raw: hashlib.sha256(_strip_frontmatter(raw)).hexdigest(),
    "git_blob_sha1": _git_blob_sha1,
}

# None => algorithm undetermined => drift is 'indeterminate' (never asserted).
# Set to a key of _HASH_ALGOS once the skills.sh normalization is reproduced.
CATALOG_HASH_ALGO: str | None = None


def compute_catalog_hash(skill_path: str, algo: str | None = None) -> str | None:
    """Recompute the content hash of a CURRENT catalog SKILL.md, read locally
    from the checkout cwd. Returns the hex digest, or None when the algorithm
    is undetermined (default), the algo name is unknown, the path is outside
    the catalog, or the file is unreadable. None => the caller must treat the
    subscription as 'indeterminate' (never 'drift').
    """
    name = algo if algo is not None else CATALOG_HASH_ALGO
    if name is None:
        return None
    fn = _HASH_ALGOS.get(name)
    if fn is None:
        return None
    # Scope to the catalog tree and refuse traversal outside it.
    norm = os.path.normpath(skill_path)
    if norm.startswith("..") or os.path.isabs(norm):
        return None
    if not (norm == CATALOG_DIR or norm.startswith(CATALOG_DIR + os.sep)):
        return None
    try:
        with open(os.path.join(os.getcwd(), norm), "rb") as fh:
            raw = fh.read()
    except OSError:
        return None
    return fn(raw)


_LINEAGE_HISTORY_CAP = 30  # max historical versions walked per skill


def _algo_proven_for_lineage(skill_path: str, stored_hash: str, algo: str) -> bool:
    """Return True iff `algo` (a key of _HASH_ALGOS) reproduces `stored_hash`
    for AT LEAST ONE historical version of `skill_path`, walking at most
    `_LINEAGE_HISTORY_CAP` versions via `git log` + `git show <sha>:<path>`
    against the local checkout (cwd).

    This is the guard that lets `compute_subscription_drift` assert 'drift'
    for a skill: a hash mismatch against the *current* file only means
    "drift OR the algorithm is wrong for this file" until we've shown the
    algorithm has actually reproduced a real stored hash somewhere in this
    specific skill's history. Best-effort and defensive — any git/hash
    failure is treated as "not proven" (never raises, never asserts drift on
    an exception).
    """
    fn = _HASH_ALGOS.get(algo)
    if fn is None:
        return False
    try:
        log = subprocess.run(
            ["git", "-C", ".", "log", f"-n{_LINEAGE_HISTORY_CAP}", "--format=%H", "--", skill_path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    if log.returncode != 0:
        return False
    shas = [s for s in log.stdout.splitlines() if s.strip()][:_LINEAGE_HISTORY_CAP]
    for sha in shas:
        try:
            show = subprocess.run(
                ["git", "show", f"{sha}:{skill_path}"],
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError):
            continue
        if show.returncode != 0:
            continue
        try:
            if fn(show.stdout) == stored_hash:
                return True
        except Exception:  # noqa: BLE001 — a bad historical blob must not crash the census
            continue
    return False


# --- HTTP ------------------------------------------------------------------


def _api_base() -> str:
    return os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")


def _request(path: str, token: str) -> object | None:
    """GET an absolute-or-relative API path. Returns parsed JSON, or None on
    HTTP 404 (tolerated "not present"). Raises on any other HTTP/URL error so
    the caller can attribute it to a specific repo. Never logs the token.
    """
    url = path if path.startswith("http") else f"{_api_base()}/{path.lstrip('/')}"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("X-GitHub-Api-Version", "2022-11-28")
    req.add_header("User-Agent", "thrillmade-skill-census")
    try:
        with urllib.request.urlopen(req, timeout=API_TIMEOUT) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        # Re-raise with a compact, token-free message for the caller to catch.
        raise RuntimeError(f"HTTP {exc.code} on {path}") from None
    except urllib.error.URLError as exc:
        raise RuntimeError(f"network error on {path}: {exc.reason}") from None


def _get_file_json(repo: str, path: str, token: str) -> object | None:
    """Fetch a JSON *file* via the Contents API and parse it. The Contents
    API returns the file body base64-encoded under `content`; decode then
    json.loads. Returns None if the file is absent (404) or empty.
    """
    payload = _request(f"repos/{ORG}/{repo}/contents/{path}", token)
    if payload is None:
        return None
    if not isinstance(payload, dict) or payload.get("type") != "file":
        # A directory or unexpected shape where a file was expected.
        raise RuntimeError(f"{path} is not a file (Contents API returned a {type(payload).__name__})")
    encoding = payload.get("encoding")
    content = payload.get("content", "")
    if encoding != "base64":
        raise RuntimeError(f"{path} unexpected Contents encoding: {encoding!r}")
    raw = base64.b64decode(content).decode("utf-8")
    if not raw.strip():
        return None
    return json.loads(raw)


def _list_dir(repo: str, path: str, token: str) -> list[dict] | None:
    """List a *directory* via the Contents API. Returns the raw entry list
    (each entry a dict with `name` + `type`), or None if the directory is
    absent (404).
    """
    payload = _request(f"repos/{ORG}/{repo}/contents/{path}", token)
    if payload is None:
        return None
    if not isinstance(payload, list):
        raise RuntimeError(f"{path} is not a directory (Contents API returned a {type(payload).__name__})")
    return payload


# --- Parsers ---------------------------------------------------------------


def parse_lock(lock: object) -> tuple[list[str], list[str]]:
    """Extract (skill_names, sources) from a skills-lock.json payload.

    The lock's exact shape varies by generator, so this is deliberately
    tolerant: it accepts a top-level list, or a dict keyed by `skills` /
    `installed`, or a dict mapping name -> metadata. Anything it can't map to
    a name is skipped rather than raised — a malformed lock degrades to "no
    subscriptions found here", not a repo-level error.
    """
    names: list[str] = []
    sources: list[str] = []

    def _from_entry(entry: object) -> None:
        if isinstance(entry, str):
            names.append(entry)
        elif isinstance(entry, dict):
            name = entry.get("name") or entry.get("slug") or entry.get("skill")
            if isinstance(name, str) and name:
                names.append(name)
            src = entry.get("source")
            if isinstance(src, str) and src:
                sources.append(src)

    if isinstance(lock, list):
        for entry in lock:
            _from_entry(entry)
    elif isinstance(lock, dict):
        container = lock.get("skills") or lock.get("installed")
        if isinstance(container, list):
            for entry in container:
                _from_entry(entry)
        elif isinstance(container, dict):
            for key, meta in container.items():
                if isinstance(key, str):
                    names.append(key)
                if isinstance(meta, dict) and isinstance(meta.get("source"), str):
                    sources.append(meta["source"])
        else:
            # Bare name -> metadata mapping (no `skills`/`installed` wrapper).
            for key, meta in lock.items():
                if key in ("version", "lastUpdate", "lastUpdateVersion"):
                    continue
                if isinstance(key, str):
                    names.append(key)
                if isinstance(meta, dict) and isinstance(meta.get("source"), str):
                    sources.append(meta["source"])

    return _dedupe(names), _dedupe(sources)


def parse_manifest(manifest: object) -> list[str]:
    """Extract installed[].slug from a .clud-bug.json payload."""
    if not isinstance(manifest, dict):
        return []
    installed = manifest.get("installed")
    if not isinstance(installed, list):
        return []
    slugs = [
        entry["slug"]
        for entry in installed
        if isinstance(entry, dict) and isinstance(entry.get("slug"), str)
    ]
    return _dedupe(slugs)


def parse_lock_hashes(lock: object) -> tuple[list[dict], list[str]]:
    """Extract catalog subscriptions carrying a `computedHash` from a
    skills-lock.json payload, tolerant of the same shape variations as
    `parse_lock`. Returns `(checkable, unscoped)`:

        checkable: list of {"slug", "source", "skillPath", "computedHash"}
                   dicts — drift-CHECKABLE catalog subscriptions.
        unscoped:  list of skill-name strings — catalog-scoped subscriptions
                   (valid computedHash + skillPath under the catalog dir)
                   whose lock entry has a missing/falsy `source`.

    A subscription is drift-*checkable* iff, in addition to carrying a
    non-empty `computedHash` and a `skillPath` under the catalog dir, its
    `source` equals `CATALOG_SOURCE` (`thrillmade/agent-skills`) — i.e. the
    lock itself attributes the pin to this catalog. Three-way scoping:

      - `source == CATALOG_SOURCE`  -> checkable (appended to `checkable`).
      - missing/None/falsy `source` -> NOT checkable, but still catalog-
        scoped (has a real computedHash + in-catalog skillPath) — surfaced
        distinctly via `unscoped` rather than silently dropped or miscounted
        as drift-checkable.
      - any other non-matching `source` (a foreign lock source) -> excluded
        entirely; it is not an agent-skills subscription at all, so it never
        enters catalog-subscription counting in either bucket.

    Entries without a stored hash, or whose skillPath isn't under the catalog
    dir, are skipped outright (not raised) — a malformed lock degrades to "no
    drift-checkable subscriptions here", never a repo-level error.
    """
    out: list[dict] = []
    unscoped: list[str] = []

    def _add(slug: object, meta: object) -> None:
        if not isinstance(meta, dict):
            return
        computed = meta.get("computedHash")
        skill_path = meta.get("skillPath")
        name = slug if isinstance(slug, str) and slug else meta.get("slug") or meta.get("name")
        if not (isinstance(computed, str) and computed):
            return
        if not (isinstance(skill_path, str) and skill_path):
            return
        norm = os.path.normpath(skill_path)
        if not (norm == CATALOG_DIR or norm.startswith(CATALOG_DIR + os.sep)):
            return  # not a catalog file — out of drift scope entirely
        resolved_name = name if isinstance(name, str) and name else norm
        src = meta.get("source")
        if not src:
            # Missing/None (or empty) source: catalog-scoped but NOT
            # drift-checkable — bucketed separately, never dropped silently.
            unscoped.append(resolved_name)
            return
        if not (isinstance(src, str) and src == CATALOG_SOURCE):
            # Foreign source — not an agent-skills subscription; excluded
            # entirely from catalog-subscription counting (neither bucket).
            return
        out.append(
            {
                "slug": resolved_name,
                "source": src,
                "skillPath": skill_path,
                "computedHash": computed,
            }
        )

    if isinstance(lock, dict):
        container = lock.get("skills") or lock.get("installed")
        if isinstance(container, dict):
            for key, meta in container.items():
                _add(key, meta)
        elif isinstance(container, list):
            for entry in container:
                if isinstance(entry, dict):
                    _add(entry.get("slug") or entry.get("name"), entry)
        else:
            # Bare name -> metadata mapping (no `skills`/`installed` wrapper).
            for key, meta in lock.items():
                if key in ("version", "lastUpdate", "lastUpdateVersion"):
                    continue
                _add(key, meta)
    elif isinstance(lock, list):
        for entry in lock:
            if isinstance(entry, dict):
                _add(entry.get("slug") or entry.get("name"), entry)

    return out, unscoped


# Usage keys are consumer-controlled input (a repo's own .clud-bug.json) that
# ends up interpolated straight into digest.md markdown (table cells,
# headers) — validate the shape before trusting a key as a skill slug.
USAGE_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,62}$")


def parse_usage(manifest: object) -> tuple[dict, list[str]]:
    """Extract the top-level `usage` object from a .clud-bug.json payload
    (clud-bug skill-usage schema v2: `usage[<slug>] = {loads, citations,
    last_cited}`). Returns `(usage, rejected)`:

        usage:    {slug: {loads, citations, last_cited}} for keys matching
                  USAGE_SLUG_RE (the catalog's skill-name slug shape).
        rejected: raw key strings that did NOT match USAGE_SLUG_RE — counted
                  and surfaced (never silently dropped, never raised on, and
                  never trusted as a slug for interpolation).

    Tolerant: absent/malformed usage => ({}, []) (never raises). Numeric
    fields default to 0; `last_cited` is passed through as a string or None.
    """
    if not isinstance(manifest, dict):
        return {}, []
    usage = manifest.get("usage")
    if not isinstance(usage, dict):
        return {}, []
    out: dict = {}
    rejected: list[str] = []
    for slug, stats in usage.items():
        if not isinstance(slug, str):
            continue
        if not USAGE_SLUG_RE.match(slug):
            rejected.append(slug)
            continue
        if not isinstance(stats, dict):
            continue
        loads = stats.get("loads")
        citations = stats.get("citations")
        last_cited = stats.get("last_cited")
        out[slug] = {
            "loads": loads if isinstance(loads, int) and not isinstance(loads, bool) else 0,
            "citations": citations if isinstance(citations, int) and not isinstance(citations, bool) else 0,
            "last_cited": last_cited if isinstance(last_cited, str) else None,
        }
    return out, rejected


def _dedupe(items: list[str]) -> list[str]:
    """Order-preserving de-duplication."""
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out


# --- Per-repo survey -------------------------------------------------------


def survey_repo(repo: str, token: str) -> dict:
    """Return the per-repo census record. On any non-404 fetch/parse failure,
    returns a record carrying an `error` string instead of crashing the run.
    """
    try:
        lock = _get_file_json(repo, LOCK_PATH, token)
        lock_names, _lock_sources = parse_lock(lock) if lock is not None else ([], [])
        lock_subscriptions, unscoped_subscriptions = (
            parse_lock_hashes(lock) if lock is not None else ([], [])
        )

        manifest = _get_file_json(repo, MANIFEST_PATH, token)
        manifest_slugs = parse_manifest(manifest) if manifest is not None else []
        usage, usage_rejected = parse_usage(manifest) if manifest is not None else ({}, [])

        subscribed = _dedupe(lock_names + manifest_slugs)
        subscribed_set = set(subscribed)

        listing = _list_dir(repo, LOCAL_SKILLS_DIR, token)
        if listing is None:
            local_dirs: list[str] = []
        else:
            dir_names = [
                e["name"]
                for e in listing
                if isinstance(e, dict)
                and e.get("type") == "dir"
                and isinstance(e.get("name"), str)
            ]
            # local_dirs = listing minus subscribed minus the manifest file.
            local_dirs = sorted(
                n
                for n in set(dir_names)
                if n not in subscribed_set and n != MANIFEST_FILENAME
            )

        # untracked == local_dirs: present on disk, in neither manifest.
        return {
            "subscribed": sorted(subscribed),
            "untracked": list(local_dirs),
            "local": list(local_dirs),
            "lock_subscriptions": lock_subscriptions,
            "unscoped_subscriptions": unscoped_subscriptions,
            "usage": usage,
            "usage_rejected": usage_rejected,
        }
    except Exception as exc:  # noqa: BLE001 — collect, never die on one repo.
        return {
            "subscribed": [],
            "untracked": [],
            "local": [],
            "lock_subscriptions": [],
            "unscoped_subscriptions": [],
            "usage": {},
            "usage_rejected": [],
            "error": str(exc),
        }


# --- Org-wide signals ------------------------------------------------------


def read_catalog() -> list[str]:
    """Read the catalog skill list locally from the checkout cwd (skills/)."""
    if not os.path.isdir(CATALOG_DIR):
        return []
    return sorted(
        name
        for name in os.listdir(CATALOG_DIR)
        if os.path.isdir(os.path.join(CATALOG_DIR, name)) and not name.startswith(".")
    )


def _grace_reason(skill: str) -> str | None:
    """Return a grace annotation for an unsubscribed catalog skill, or None
    if its zero-subscription state is a genuine coverage gap.
    """
    if skill.startswith(UDTS_STUB_PREFIX):
        return "udts-* L2 stub (incubating in tokenomics — parity marker, not yet guidance)"
    if skill in STRUCTURAL_L0:
        return "structural L0 (composed by L1 dispatchers, not subscribed directly)"
    return None


def compute_signals(catalog: list[str], repos: dict[str, dict]) -> dict:
    """Derive the org-wide promotion/coverage signals from the per-repo
    records and the local catalog listing.
    """
    # subscriber count per catalog skill
    subscriber_count: dict[str, int] = {skill: 0 for skill in catalog}
    for record in repos.values():
        for skill in record.get("subscribed", []):
            if skill in subscriber_count:
                subscriber_count[skill] += 1

    unsubscribed_catalog_skills = [
        {
            "name": skill,
            "grace": _grace_reason(skill) is not None,
            "grace_reason": _grace_reason(skill),
        }
        for skill in catalog
        if subscriber_count.get(skill, 0) == 0
    ]

    # convergent_local: a local dir name present in >= 2 repos' local sets.
    local_occurrences: dict[str, list[str]] = {}
    for name, record in repos.items():
        for skill in record.get("local", []):
            local_occurrences.setdefault(skill, []).append(name)
    convergent_local = [
        {"name": skill, "repos": sorted(reps), "count": len(reps)}
        for skill, reps in sorted(local_occurrences.items())
        if len(reps) >= 2
    ]
    convergent_local.sort(key=lambda item: (-item["count"], item["name"]))

    untracked_total = sum(len(record.get("untracked", [])) for record in repos.values())

    per_repo_errors = {
        name: record["error"] for name, record in repos.items() if record.get("error")
    }

    return {
        "unsubscribed_catalog_skills": unsubscribed_catalog_skills,
        "convergent_local": convergent_local,
        "untracked_total": untracked_total,
        "per_repo_errors": per_repo_errors,
    }


_USE_DEFAULT_ALGO = object()  # sentinel: "fall back to CATALOG_HASH_ALGO"


def compute_subscription_drift(
    repos: dict[str, dict], algo: object = _USE_DEFAULT_ALGO
) -> list[dict]:
    """For every repo whose skills-lock.json subscribes catalog skills,
    recompute each subscription's catalog SKILL.md hash (current, local) and
    compare to the stored computedHash. Emits one record per verdict:

        {"repo", "skill", "status": ok|drift|indeterminate|unscoped,
         "stored", "recomputed", "note"}

    DUAL MODE (see CATALOG_HASH_ALGO):
      - algorithm KNOWN  -> per-subscription 'ok' (hashes equal) or 'drift'
        (hashes differ AND the algorithm is PROVEN for this skill's pin
        lineage — see `_algo_proven_for_lineage`; otherwise 'indeterminate'
        with note "algo unproven for this skill's pin lineage", never
        'drift' on an unproven algorithm). The census SURFACES real drift and
        never auto-fixes.
      - algorithm UNDETERMINED -> a SINGLE 'indeterminate' record per lock
        (one reason line, no per-skill noise). We never report drift we
        cannot prove.

    Additionally, per repo, any subscriptions `parse_lock_hashes` bucketed as
    `unscoped_subscriptions` (catalog-scoped but missing/None `source`, so not
    drift-checkable at all) get their OWN 'unscoped' record — reported
    alongside 'indeterminate', never merged into it, so the two "we didn't
    check this" reasons (algorithm undetermined vs. source not attributable
    to this catalog) stay distinguishable.

    `algo` overrides CATALOG_HASH_ALGO (used by the self-test to exercise the
    compute path); by default it uses the module-level setting.
    """
    algo = CATALOG_HASH_ALGO if algo is _USE_DEFAULT_ALGO else algo
    records: list[dict] = []
    for repo in sorted(repos):
        subs = repos[repo].get("lock_subscriptions") or []
        unscoped = repos[repo].get("unscoped_subscriptions") or []

        if unscoped:
            records.append(
                {
                    "repo": repo,
                    "skill": None,
                    "status": "unscoped",
                    "count": len(unscoped),
                    "skills": sorted(unscoped),
                    "note": (
                        f"{len(unscoped)} subscription(s) with missing/None "
                        "`source` in skills-lock.json — not attributable to "
                        f"this catalog ({CATALOG_SOURCE}), so not "
                        "drift-checkable; excluded from catalog-subscription "
                        "drift counting entirely (distinct from 'indeterminate')"
                    ),
                }
            )

        if not subs:
            continue
        if algo is None:
            slugs = sorted(s["slug"] for s in subs)
            records.append(
                {
                    "repo": repo,
                    "skill": None,
                    "status": "indeterminate",
                    "count": len(subs),
                    "skills": slugs,
                    "note": (
                        f"hash algorithm undetermined (external skills.sh "
                        f"normalization not reproduced); {len(subs)} catalog "
                        f"subscription(s) not verifiable — not reported as drift"
                    ),
                }
            )
            continue
        for sub in sorted(subs, key=lambda s: s["slug"]):
            stored = sub["computedHash"]
            recomputed = compute_catalog_hash(sub["skillPath"], algo)
            if recomputed is None:
                records.append(
                    {
                        "repo": repo,
                        "skill": sub["slug"],
                        "status": "indeterminate",
                        "stored": stored,
                        "recomputed": None,
                        "note": f"catalog file {sub['skillPath']} unreadable/out of scope",
                    }
                )
            elif recomputed == stored:
                records.append(
                    {
                        "repo": repo,
                        "skill": sub["slug"],
                        "status": "ok",
                        "stored": stored,
                        "recomputed": recomputed,
                        "note": "",
                    }
                )
            elif not _algo_proven_for_lineage(sub["skillPath"], stored, algo):
                # A mismatch alone doesn't prove drift — it's equally
                # consistent with the algorithm being wrong for this file.
                # Never assert 'drift' unless the algorithm has reproduced a
                # real stored hash somewhere in THIS skill's history.
                records.append(
                    {
                        "repo": repo,
                        "skill": sub["slug"],
                        "status": "indeterminate",
                        "stored": stored,
                        "recomputed": recomputed,
                        "note": "algo unproven for this skill's pin lineage",
                    }
                )
            else:
                records.append(
                    {
                        "repo": repo,
                        "skill": sub["slug"],
                        "status": "drift",
                        "stored": stored,
                        "recomputed": recomputed,
                        "note": (
                            f"catalog {sub['skillPath']} moved since lock "
                            f"({stored[:12]}… → {recomputed[:12]}…) — refresh to reconcile"
                        ),
                    }
                )
    return records


def aggregate_usage(repos: dict[str, dict]) -> dict:
    """Aggregate per-skill usage (clud-bug schema v2 `usage[<slug>]`) across
    repos. Sums `loads` + `citations`; keeps the most-recent `last_cited`;
    records which repos reported each skill. Returns:

        {"present": bool, "total_citations": int, "total_loads": int,
         "skills": {slug: {loads, citations, last_cited, repos: [...]}},
         "rejected": {repo: [raw_key, ...]}, "rejected_count": int}

    `present` is False when no surveyed repo emitted a usage block (the
    expected state until clud-bug consumers start writing schema v2).
    `rejected`/`rejected_count` roll up `parse_usage`'s per-repo
    `usage_rejected` (keys that failed USAGE_SLUG_RE) — counted and named by
    repo, never silently dropped.
    """
    skills: dict[str, dict] = {}
    rejected: dict[str, list[str]] = {}
    for repo in sorted(repos):
        usage = repos[repo].get("usage") or {}
        for slug, stats in usage.items():
            agg = skills.setdefault(
                slug, {"loads": 0, "citations": 0, "last_cited": None, "repos": []}
            )
            agg["loads"] += stats.get("loads", 0)
            agg["citations"] += stats.get("citations", 0)
            last = stats.get("last_cited")
            if isinstance(last, str) and (agg["last_cited"] is None or last > agg["last_cited"]):
                agg["last_cited"] = last
            if repo not in agg["repos"]:
                agg["repos"].append(repo)
        repo_rejected = repos[repo].get("usage_rejected") or []
        if repo_rejected:
            rejected[repo] = list(repo_rejected)
    for agg in skills.values():
        agg["repos"].sort()
    total_citations = sum(a["citations"] for a in skills.values())
    total_loads = sum(a["loads"] for a in skills.values())
    return {
        "present": bool(skills),
        "total_citations": total_citations,
        "total_loads": total_loads,
        "skills": skills,
        "rejected": rejected,
        "rejected_count": sum(len(v) for v in rejected.values()),
    }


def read_placement_map() -> dict | None:
    """Read docs/placement-map.json locally from the checkout cwd. Returns the
    parsed object, or None if the file is absent (authored by a parallel
    agent — its absence is tolerated) or unparseable.
    """
    path = os.path.join(os.getcwd(), PLACEMENT_MAP_PATH)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def compute_placement_divergence(
    placement_map: dict | None, repos: dict[str, dict]
) -> dict:
    """Cross-check the placement map's declared `subscribers[]` against LIVE
    observed subscriptions (each repo's `subscribed` set). Returns:

        {"available": bool, "note": str, "divergences": [
            {"skill", "declared": [...], "observed": [...],
             "missing": [...], "extra": [...]}
        ]}

    `missing` = declared subscriber not observed live; `extra` = observed
    subscriber the map omits. These feed placement verdicts (Mode B).
    """
    if not isinstance(placement_map, dict):
        return {
            "available": False,
            "note": f"{PLACEMENT_MAP_PATH} absent — placement cross-check skipped",
            "divergences": [],
        }
    skills = placement_map.get("skills")
    if not isinstance(skills, dict):
        return {
            "available": False,
            "note": f"{PLACEMENT_MAP_PATH} present but has no `skills` object — cross-check skipped",
            "divergences": [],
        }

    # Observed subscribers per skill: repo names whose live `subscribed` carries it.
    observed: dict[str, set[str]] = {}
    for repo, record in repos.items():
        for skill in record.get("subscribed", []):
            observed.setdefault(skill, set()).add(repo)

    divergences: list[dict] = []
    for slug, meta in sorted(skills.items()):
        declared_raw = meta.get("subscribers") if isinstance(meta, dict) else None
        declared = {r for r in declared_raw if isinstance(r, str)} if isinstance(declared_raw, list) else set()
        observed_set = observed.get(slug, set())
        missing = declared - observed_set
        extra = observed_set - declared
        if missing or extra:
            divergences.append(
                {
                    "skill": slug,
                    "declared": sorted(declared),
                    "observed": sorted(observed_set),
                    "missing": sorted(missing),
                    "extra": sorted(extra),
                }
            )
    return {
        "available": True,
        "note": "",
        "divergences": divergences,
    }


def _parse_ts(value: str) -> datetime | None:
    """Parse a GitHub ISO-8601 timestamp (trailing 'Z') to an aware datetime."""
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def survey_docket(token: str, now: datetime) -> dict:
    """Count + list open `census`-labelled issues on the catalog repo that
    have gone stale (no update in > STALE_DAYS days). Pull-requests share the
    /issues endpoint and are filtered out.
    """
    try:
        payload = _request(
            f"repos/{ORG}/{CATALOG_REPO}/issues"
            f"?labels=census&state=open&per_page=100",
            token,
        )
    except Exception as exc:  # noqa: BLE001 — the docket is a best-effort
        # signal; a failure here must not crash the always-on digest.
        return {"error": str(exc), "open_count": 0, "stale_count": 0, "stale": []}

    if not isinstance(payload, list):
        return {"error": "unexpected /issues shape", "open_count": 0, "stale_count": 0, "stale": []}

    issues = [i for i in payload if isinstance(i, dict) and "pull_request" not in i]
    stale: list[dict] = []
    for issue in issues:
        ts = _parse_ts(issue.get("updated_at", ""))
        if ts is None:
            continue
        days = (now - ts).days
        if days > STALE_DAYS:
            stale.append(
                {
                    "number": issue.get("number"),
                    "title": issue.get("title", ""),
                    "updated_at": issue.get("updated_at"),
                    "days_stale": days,
                }
            )
    stale.sort(key=lambda s: (-s["days_stale"], s["number"] or 0))
    result = {
        "open_count": len(issues),
        "stale_count": len(stale),
        "stale": stale,
    }
    # No silent truncation: flag if we hit the single-page ceiling.
    if len(payload) == 100:
        result["note"] = "hit per_page=100 ceiling — additional open census issues may exist (pagination not walked)."
    return result


# --- Rendering -------------------------------------------------------------


def _md_safe(value: str) -> str:
    """Strip characters that could break a markdown table cell or inject
    formatting when interpolating repo-controlled data (e.g. a usage slug)
    into the digest: '|' (breaks table columns), backtick (breaks code-span
    nesting), and newlines (breaks a single-line cell). Defense in depth on
    top of the upstream shape validation (USAGE_SLUG_RE already restricts
    usage keys to `[a-z0-9-]`) — belt and suspenders, not the only guard.
    """
    return value.replace("|", "").replace("`", "").replace("\n", " ").replace("\r", " ")


def _cycle_tag(now: datetime) -> str:
    """census-<ISO year>-W<ISO week, zero-padded>. Matches the workflow's
    `date -u +%G-W%V` cycle tag so census.json and the filed issues agree.
    """
    iso_year, iso_week, _ = now.isocalendar()
    return f"census-{iso_year}-W{iso_week:02d}"


def render_digest(census: dict) -> str:
    """Deterministic markdown rendering of the census snapshot."""
    signals = census["signals"]
    lines: list[str] = []
    lines.append(f"# Skill census digest — {census['cycle']}")
    lines.append("")
    lines.append(f"Generated {census['generated_at']} (Mode A — deterministic counters).")
    lines.append("")

    # Per-repo table
    lines.append("## Per-repo subscription state")
    lines.append("")
    lines.append("| Repo | Subscribed | Untracked (local, in no manifest) | Notes |")
    lines.append("|---|---:|---|---|")
    for name in CONSUMER_REPOS:
        record = census["repos"].get(name, {})
        if record.get("error"):
            lines.append(f"| `{name}` | — | — | ⚠️ error: {record['error']} |")
            continue
        subscribed = record.get("subscribed", [])
        untracked = record.get("untracked", [])
        untracked_cell = ", ".join(f"`{u}`" for u in untracked) if untracked else "—"
        lines.append(f"| `{name}` | {len(subscribed)} | {untracked_cell} | |")
    lines.append("")

    # Signals
    lines.append("## Signals")
    lines.append("")

    convergent = signals["convergent_local"]
    lines.append("### Convergent local skills (present in ≥2 repos — strongest promotion evidence)")
    lines.append("")
    if convergent:
        lines.append("| Skill | Repo count | Repos |")
        lines.append("|---|---:|---|")
        for item in convergent:
            reps = ", ".join(f"`{r}`" for r in item["repos"])
            lines.append(f"| `{item['name']}` | {item['count']} | {reps} |")
    else:
        lines.append("_None this cycle — no locally-authored skill appears in 2+ repos._")
    lines.append("")

    unsub = signals["unsubscribed_catalog_skills"]
    lines.append("### Unsubscribed catalog skills (subscribed by zero repos)")
    lines.append("")
    real_gaps = [s for s in unsub if not s["grace"]]
    graced = [s for s in unsub if s["grace"]]
    if real_gaps:
        lines.append("**Coverage gaps (no grace):**")
        lines.append("")
        for s in real_gaps:
            lines.append(f"- `{s['name']}`")
        lines.append("")
    else:
        lines.append("_No un-graced coverage gaps — every zero-subscription catalog skill is expected (grace)._")
        lines.append("")
    if graced:
        lines.append("**Graced (zero subscriptions expected):**")
        lines.append("")
        for s in graced:
            lines.append(f"- `{s['name']}` — {s['grace_reason']}")
        lines.append("")

    lines.append(f"### Untracked total\n\n{signals['untracked_total']} locally-authored skill dir(s) across all surveyed repos sit in no manifest.")
    lines.append("")

    errors = signals["per_repo_errors"]
    if errors:
        lines.append("### Per-repo errors")
        lines.append("")
        for name, err in sorted(errors.items()):
            lines.append(f"- `{name}`: {err}")
        lines.append("")

    # Subscription drift — recomputed catalog hash vs. each lock's computedHash.
    lines.append("## Subscription drift")
    lines.append("")
    drift = signals.get("subscription_drift", [])
    if not drift:
        lines.append("_No repo subscribes catalog skills with a stored `computedHash` — nothing to check._")
        lines.append("")
    else:
        drifted = [r for r in drift if r["status"] == "drift"]
        indeterminate = [r for r in drift if r["status"] == "indeterminate"]
        unscoped = [r for r in drift if r["status"] == "unscoped"]
        if CATALOG_HASH_ALGO is None:
            lines.append(
                "> Hash algorithm **undetermined** — the `computedHash` is produced by the "
                "external skills.sh CLI's normalization, which no local candidate reproduces "
                "(verified against every historical version of the catalog files). Drift is "
                "reported `indeterminate` per lock; the census never asserts drift it cannot "
                "prove. Set `CATALOG_HASH_ALGO` once the normalization is mirrored to unlock "
                "`ok`/`drift` verdicts (each still guarded per-skill against its own pin "
                "lineage — see the module docstring)."
            )
            lines.append("")
        lines.append("| Repo | Skill | Status | Note |")
        lines.append("|---|---|---|---|")
        for r in drift:
            if r.get("skill") is None:
                skill_cell = f"{r.get('count', 0)} sub(s): " + ", ".join(
                    f"`{_md_safe(s)}`" for s in r.get("skills", [])
                )
            else:
                skill_cell = f"`{_md_safe(r['skill'])}`"
            badge = {
                "ok": "✅ ok",
                "drift": "⚠️ drift",
                "indeterminate": "❔ indeterminate",
                "unscoped": "🚫 unscoped",
            }.get(r["status"], r["status"])
            note = r.get("note", "") or ""
            lines.append(f"| `{r['repo']}` | {skill_cell} | {badge} | {note} |")
        lines.append("")
        summary_parts = []
        if drifted:
            summary_parts.append(
                f"**{len(drifted)} drifted subscription(s)** — the catalog moved since the "
                "lock was written. Surfaced only; refresh in the consumer repo to reconcile "
                "(the census never auto-fixes)."
            )
        if indeterminate:
            summary_parts.append(
                f"**{len(indeterminate)} lock(s)/subscription(s) indeterminate** — no drift "
                "asserted (algorithm undetermined, or unproven for that skill's pin lineage)."
            )
        if unscoped:
            summary_parts.append(
                f"**{len(unscoped)} lock(s) with unscoped subscription(s)** — missing/None "
                "`source` in skills-lock.json, not attributable to this catalog, so not "
                "drift-checkable (distinct from 'indeterminate')."
            )
        for part in summary_parts:
            lines.append(part)
        lines.append("")

    # Usage citations — clud-bug skill-usage schema v2 aggregation.
    lines.append("## Usage citations")
    lines.append("")
    usage = signals.get("usage", {"present": False, "skills": {}})
    if usage.get("present"):
        lines.append(
            f"Aggregated across surveyed repos: {usage['total_citations']} citation(s), "
            f"{usage['total_loads']} load(s)."
        )
        lines.append("")
        lines.append("| Skill | Loads | Citations | Last cited | Repos |")
        lines.append("|---|---:|---:|---|---|")
        for slug in sorted(usage["skills"]):
            s = usage["skills"][slug]
            reps = ", ".join(f"`{r}`" for r in s.get("repos", []))
            lines.append(
                f"| `{_md_safe(slug)}` | {s['loads']} | {s['citations']} | "
                f"{s.get('last_cited') or '—'} | {reps} |"
            )
        lines.append("")
    else:
        lines.append(
            "_No usage data — `usage[]` not yet emitted by consumers "
            "(clud-bug schema v2 pending). Never failed on absence._"
        )
        lines.append("")
    rejected_count = usage.get("rejected_count", 0)
    if rejected_count:
        rejected_repos = usage.get("rejected", {})
        lines.append(
            f"> {rejected_count} usage key(s) across {len(rejected_repos)} repo(s) rejected "
            "(did not match the skill-slug shape `^[a-z0-9][a-z0-9-]{0,62}$`) — not "
            "aggregated above; see `signals.usage.rejected` in census.json for the raw keys."
        )
        lines.append("")

    # Placement-map cross-check — declared subscribers vs. live observation.
    lines.append("## Placement divergence")
    lines.append("")
    placement = signals.get("placement_divergence", {"available": False, "divergences": []})
    if not placement.get("available"):
        lines.append(f"_{placement.get('note', 'placement cross-check unavailable')}._")
        lines.append("")
    else:
        divs = placement.get("divergences", [])
        if not divs:
            lines.append("_Placement map agrees with live subscriptions — no divergence._")
            lines.append("")
        else:
            for d in divs:
                parts = []
                if d["missing"]:
                    parts.append("declared-but-not-observed: " + ", ".join(f"`{r}`" for r in d["missing"]))
                if d["extra"]:
                    parts.append("observed-but-not-declared: " + ", ".join(f"`{r}`" for r in d["extra"]))
                lines.append(f"- `{d['skill']}` — " + "; ".join(parts))
            lines.append("")

    # Stale docket
    docket = census["stale_docket"]
    lines.append("## Docket staleness")
    lines.append("")
    if docket.get("error"):
        lines.append(f"⚠️ Could not survey the docket: {docket['error']}")
        lines.append("")
    else:
        lines.append(
            f"{docket['open_count']} open `census` issue(s); "
            f"{docket['stale_count']} stale (no update in > {STALE_DAYS} days)."
        )
        lines.append("")
        if docket.get("note"):
            lines.append(f"> {docket['note']}")
            lines.append("")
        if docket["stale"]:
            lines.append("| Issue | Days stale | Last update | Title |")
            lines.append("|---:|---:|---|---|")
            for s in docket["stale"]:
                lines.append(
                    f"| #{s['number']} | {s['days_stale']} | {s['updated_at']} | {s['title']} |"
                )
            lines.append("")

    # Coverage caps — explicit statement of what this cycle did NOT measure.
    lines.append("## Coverage caps — what this cycle did NOT measure")
    lines.append("")
    lines.append(
        "This is a **structural** census only: it counts what each repo has "
        "subscribed, carries locally, and leaves untracked, plus catalog "
        "subscription coverage. It does **not** measure:"
    )
    lines.append("")
    usage_present = signals.get("usage", {}).get("present")
    if usage_present:
        lines.append(
            "- **Usage / firing frequency** — now partially wired: see **Usage "
            "citations** above (aggregated from consumers' `usage[]` blocks)."
        )
        lines.append(
            "- **Citation data** — partially wired via `usage[<slug>].citations` "
            "(clud-bug schema v2); coverage is limited to repos already emitting it."
        )
    else:
        lines.append("- **Usage / firing frequency** — how often each skill actually loads in agent sessions.")
        lines.append(
            "- **Citation data** — `usage[]` not yet emitted by consumers "
            "(clud-bug schema v2 pending); no skill carries citation counts this cycle."
        )
    lines.append("")
    if usage_present:
        lines.append(
            "Structural convergence (see Signals) remains the primary promotion "
            "evidence; observed-use data is still sparse."
        )
    else:
        lines.append(
            "Those signals are not yet wired. Promotion/demotion judgments this "
            "cycle rest on structural convergence (see Signals), not observed use."
        )
    lines.append("")

    return "\n".join(lines) + "\n"


# --- Main ------------------------------------------------------------------


def main() -> int:
    token = os.environ.get("STEWARD_TOKEN", "").strip()
    if not token:
        print("::error::STEWARD_TOKEN is empty — cannot run the census counters.", file=sys.stderr)
        return 1

    out_dir = os.environ.get("OUT_DIR", "").strip()
    if not out_dir:
        runner_temp = os.environ.get("RUNNER_TEMP", "/tmp")
        out_dir = os.path.join(runner_temp, "census")
    os.makedirs(out_dir, exist_ok=True)

    now = datetime.now(timezone.utc)
    catalog = read_catalog()

    repos: dict[str, dict] = {}
    for repo in CONSUMER_REPOS:
        repos[repo] = survey_repo(repo, token)

    signals = compute_signals(catalog, repos)
    # Additive signals (never mutate compute_signals' existing contract).
    signals["subscription_drift"] = compute_subscription_drift(repos)
    signals["usage"] = aggregate_usage(repos)
    signals["placement_divergence"] = compute_placement_divergence(
        read_placement_map(), repos
    )
    stale_docket = survey_docket(token, now)

    census = {
        "cycle": _cycle_tag(now),
        "generated_at": now.isoformat(),
        "repos": repos,
        "catalog": catalog,
        "signals": signals,
        "stale_docket": stale_docket,
    }

    census_path = os.path.join(out_dir, "census.json")
    digest_path = os.path.join(out_dir, "digest.md")
    with open(census_path, "w", encoding="utf-8") as fh:
        json.dump(census, fh, indent=2, sort_keys=False)
        fh.write("\n")
    with open(digest_path, "w", encoding="utf-8") as fh:
        fh.write(render_digest(census))

    # One-line ok summary to stdout (matches the org's `ok <k=v>` house style).
    error_repos = len(signals["per_repo_errors"])
    drift_recs = signals["subscription_drift"]
    drift_count = sum(1 for r in drift_recs if r["status"] == "drift")
    indeterminate_count = sum(1 for r in drift_recs if r["status"] == "indeterminate")
    unscoped_count = sum(1 for r in drift_recs if r["status"] == "unscoped")
    usage_rejected_count = signals["usage"].get("rejected_count", 0)
    print(
        "ok "
        f"cycle={census['cycle']} "
        f"catalog={len(catalog)} "
        f"repos={len(repos)} "
        f"repo_errors={error_repos} "
        f"convergent={len(signals['convergent_local'])} "
        f"unsubscribed={len(signals['unsubscribed_catalog_skills'])} "
        f"untracked_total={signals['untracked_total']} "
        f"drift={drift_count} "
        f"drift_indeterminate={indeterminate_count} "
        f"drift_unscoped={unscoped_count} "
        f"usage_citations={signals['usage']['total_citations']} "
        f"usage_rejected={usage_rejected_count} "
        f"placement_divergences={len(signals['placement_divergence']['divergences'])} "
        f"stale_docket={stale_docket.get('stale_count', 0)} "
        f"out={out_dir}"
    )
    return 0


def local_selftest(argv: list[str]) -> int:
    """Network-free self-test (STEWARD_TOKEN not required). Exercises hash
    determination + drift classification + placement-map read against the
    LOCAL checkout only, printing results. Optional `--lock <path>` points at a
    real skills-lock.json to run the empirical hash determination against
    (defaults to ./skills-lock.json if present).

    Never fetches anything. Returns 0 always (a diagnostic, not a gate).
    """
    lock_path = None
    if "--lock" in argv:
        i = argv.index("--lock")
        if i + 1 < len(argv):
            lock_path = argv[i + 1]
    if lock_path is None and os.path.isfile(os.path.join(os.getcwd(), LOCK_PATH)):
        lock_path = os.path.join(os.getcwd(), LOCK_PATH)

    print("== census_counters --local-selftest ==")
    print(f"cwd={os.getcwd()}")
    print(f"CATALOG_HASH_ALGO={CATALOG_HASH_ALGO!r} "
          f"(None => drift is 'indeterminate'; algorithm undetermined)")
    print(f"registered algorithms: {sorted(_HASH_ALGOS)}")

    catalog = read_catalog()
    print(f"\n-- catalog ({len(catalog)} skills) --")
    print(", ".join(catalog) if catalog else "(none)")

    # 1) Hash determination against a real lock (if available).
    print("\n-- hash determination (recompute each catalog file, all algos) --")
    subs: list[dict] = []
    unscoped: list[str] = []
    if lock_path and os.path.isfile(lock_path):
        try:
            with open(lock_path, "r", encoding="utf-8") as fh:
                lock = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f"  could not read lock {lock_path}: {exc}")
            lock = None
        subs, unscoped = parse_lock_hashes(lock) if lock is not None else ([], [])
        print(f"  lock={lock_path} — {len(subs)} catalog subscription(s), "
              f"{len(unscoped)} unscoped (missing/None source): {unscoped}")
        for sub in subs:
            print(f"  * {sub['slug']} (skillPath={sub['skillPath']})")
            print(f"      stored     : {sub['computedHash']}")
            any_match = False
            for name in sorted(_HASH_ALGOS):
                got = compute_catalog_hash(sub["skillPath"], name)
                mark = "  <== MATCH" if got == sub["computedHash"] else ""
                if got == sub["computedHash"]:
                    any_match = True
                print(f"      {name:<16}: {got}{mark}")
            if not any_match:
                print("      => NO local algorithm reproduces the stored hash "
                      "(external skills.sh normalization).")
    else:
        print("  no lock provided/found — skipping empirical determination "
              "(pass --lock <path> to run it).")

    # 2) Drift classification — dual mode demonstration, plus the per-skill
    # lineage-proof guard (a mismatch alone is never enough to assert 'drift').
    print("\n-- drift classification (dual mode + per-skill lineage proof) --")
    if subs or unscoped:
        pseudo = {
            "selftest-lock": {
                "subscribed": [],
                "lock_subscriptions": subs,
                "unscoped_subscriptions": unscoped,
            }
        }
        default_recs = compute_subscription_drift(pseudo)
        print(f"  CATALOG_HASH_ALGO={CATALOG_HASH_ALGO!r}: "
              f"{[r['status'] for r in default_recs]}")
        for r in default_recs:
            print(f"    {r['status']:<13} skill={r.get('skill')} note={r.get('note')}")
        # Demonstrate the compute path with an algorithm forced on (no global
        # mutation — the override is a parameter). sha256_raw is known NOT to
        # be the real skills.sh normalization, so the per-skill lineage-proof
        # guard (_algo_proven_for_lineage) should downgrade every mismatch to
        # 'indeterminate' rather than assert 'drift' — this is the guard
        # working as designed, not a regression.
        forced = compute_subscription_drift(pseudo, algo="sha256_raw")
        print(f"  algo='sha256_raw' (illustrative, deliberately wrong): "
              f"{[r['status'] for r in forced]}")
        for r in forced:
            if r.get("skill") is None:
                print(f"    {r['status']:<13} skill=None note={r.get('note')}")
            else:
                print(f"    {r['status']:<13} skill={r.get('skill')} note={r.get('note')} "
                      f"stored={str(r.get('stored'))[:12]}… recomputed={str(r.get('recomputed'))[:12]}…")
        if any(r["status"] == "drift" for r in forced):
            print("  NOTE: a forced-wrong algorithm still produced 'drift' — this would mean "
                  "_algo_proven_for_lineage matched a historical version by coincidence.")
        else:
            print("  (forced-algo verdicts are 'indeterminate', not 'drift' — the per-skill "
                  "lineage-proof guard correctly refused to assert drift for an algorithm "
                  "unproven against this skill's history.)")
    else:
        print("  no lock — skipping drift demonstration.")

    # 3) Placement-map read + cross-check.
    print("\n-- placement-map cross-check --")
    pm = read_placement_map()
    if pm is None:
        print(f"  {PLACEMENT_MAP_PATH}: ABSENT/unreadable (tolerated).")
    else:
        skills = pm.get("skills") if isinstance(pm, dict) else None
        n = len(skills) if isinstance(skills, dict) else 0
        print(f"  {PLACEMENT_MAP_PATH}: present, version={pm.get('version')}, "
              f"updated={pm.get('updated')}, skills={n}")
    print("  NOTE: offline self-test observes NO live subscriptions, so every "
          "declared subscriber below reads as 'missing' — this only exercises "
          "the code path; real divergences need a networked run.")
    result = compute_placement_divergence(pm, {})
    print(f"  cross-check available={result['available']} "
          f"note={result['note']!r} divergences={len(result['divergences'])}")
    for d in result["divergences"]:
        print(f"    - {d['skill']}: missing={d['missing']} extra={d['extra']}")

    print("\nok selftest done")
    return 0


if __name__ == "__main__":
    if "--local-selftest" in sys.argv:
        sys.exit(local_selftest(sys.argv[1:]))
    sys.exit(main())
