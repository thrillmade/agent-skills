#!/usr/bin/env python3
"""Deterministic skill-census counters (Mode A of the weekly census engine).

Called by `.github/workflows/skill-census.yml` once per cycle. Produces the
*mechanical* half of the census: what each consumer repo has subscribed vs.
what it carries locally, which catalog skills nobody subscribes, and which
locally-authored skills have converged across repos (the strongest promotion
signal). The *judgment* half — gap/placement/promotion verdicts — is Mode B
(`census_panel.py`), which reads this script's `census.json`.

Stdlib ONLY (urllib, json, os, sys, datetime). No pip, so the counters step
runs on a bare runner before the panel step installs the Anthropic SDK. If
the panel step is skipped (no ANTHROPIC_API_KEY), this file's `digest.md`
still ships as the cycle's deliverable.

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
import json
import os
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

# Contents API paths probed per consumer repo.
LOCK_PATH = "skills-lock.json"
MANIFEST_PATH = ".claude/skills/.clud-bug.json"
LOCAL_SKILLS_DIR = ".claude/skills"
MANIFEST_FILENAME = ".clud-bug.json"  # excluded from local-dir accounting

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

        manifest = _get_file_json(repo, MANIFEST_PATH, token)
        manifest_slugs = parse_manifest(manifest) if manifest is not None else []

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
        }
    except Exception as exc:  # noqa: BLE001 — collect, never die on one repo.
        return {
            "subscribed": [],
            "untracked": [],
            "local": [],
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
    lines.append("- **Usage / firing frequency** — how often each skill actually loads in agent sessions.")
    lines.append("- **Citation data** — which skills get referenced in PRs, reviews, or decision logs.")
    lines.append("")
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
    print(
        "ok "
        f"cycle={census['cycle']} "
        f"catalog={len(catalog)} "
        f"repos={len(repos)} "
        f"repo_errors={error_repos} "
        f"convergent={len(signals['convergent_local'])} "
        f"unsubscribed={len(signals['unsubscribed_catalog_skills'])} "
        f"untracked_total={signals['untracked_total']} "
        f"stale_docket={stale_docket.get('stale_count', 0)} "
        f"out={out_dir}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
