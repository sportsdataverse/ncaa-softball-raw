"""NCAA baseball/softball season discovery: team list -> team pages -> contest_ids.

Pure parse functions + an injectable ``fetch_fn`` so discovery is fully offline-
testable; the live default drives ``NcaaFetcher.with_browser`` (real-GPU host +
US residential proxy pool -- see docs/DESIGN.md; datacenter IPs get an edge 403).

Sport codes: ``MBA`` = baseball (D1 = division 1), ``WSB`` = softball.

**Softball caveat (verified 2026-07-17):** ``WSB`` is the confirmed softball
sport_code (site sport dropdown), but ``inst_team_list?sport_code=WSB`` returns a
~23 KB shell with zero ``/teams/`` links -- softball's team-list flow differs from
baseball's. Baseball (``MBA``) discovery works as written (307 D1 teams for 2025).
Resolving the WSB team-list flow is a TODO; capture (below) works for both sports
once contest_ids are in hand.
"""

from __future__ import annotations

import re
from typing import Callable, List, Optional

FetchFn = Callable[[str], str]  # (path) -> html

_TEAM_ID_RE = re.compile(r"/teams/(\d+)")
_CONTEST_ID_RE = re.compile(r"/contests/(\d+)/")


def team_list_path(academic_year: int, division: int = 1, sport_code: str = "MBA") -> str:
    """stats.ncaa.org team-list path. ``sport_code`` MBA=baseball / WSB=softball;
    ``division`` 1/2/3 = D-I/II/III."""
    return f"team/inst_team_list?academic_year={academic_year}&conf_id=-1&division={division}&sport_code={sport_code}"


def parse_team_ids(html: str) -> List[str]:
    """Distinct ``/teams/{id}`` ids from a team-list page (order preserved)."""
    return list(dict.fromkeys(_TEAM_ID_RE.findall(html or "")))


def parse_contest_ids(html: str) -> List[str]:
    """Distinct ``/contests/{id}`` ids from a team page (order preserved)."""
    return list(dict.fromkeys(_CONTEST_ID_RE.findall(html or "")))


def browser_fetch_fn(proxy_pool: "Optional[List[str]]" = None) -> FetchFn:
    """Build a live ``(path) -> html`` fetch backed by one NcaaFetcher browser
    session. Pass a US-residential ``proxy_pool``; hold the session (no per-call
    relaunch) to avoid the patchright relaunch-storm crash."""
    from sportsdataverse.mbb.mbb_ncaa_fetch import NcaaFetcher

    fetcher = NcaaFetcher.with_browser(proxy_pool=proxy_pool)
    return lambda path: fetcher.fetch_html(path, force=True)


def discover_season(
    academic_year: int,
    division: int = 1,
    sport_code: str = "MBA",
    *,
    fetch_fn: Optional[FetchFn] = None,
) -> List[str]:
    """Discover every ``contest_id`` in a season (team list -> team pages -> dedup).

    Args:
        academic_year: e.g. ``2025`` for the spring-2025 season.
        division: 1 = D-I (default), 2/3 = D-II/III.
        sport_code: ``MBA`` (baseball) or ``WSB`` (softball).
        fetch_fn: ``(path) -> html``. Defaults to a live browser session.

    Returns:
        Sorted, de-duplicated list of ``contest_id`` strings.

    Raises:
        ValueError: the team list resolved zero teams -- raised loudly instead of
            returning a hollow list. For ``WSB`` this is currently expected (the
            team-list flow differs; see the module docstring).
    """
    fetch = fetch_fn or browser_fetch_fn()
    teams = parse_team_ids(fetch(team_list_path(academic_year, division, sport_code)))
    if not teams:
        raise ValueError(
            f"no teams for academic_year={academic_year} division={division} "
            f"sport_code={sport_code}" + (" (WSB team-list flow is a known TODO)" if sport_code == "WSB" else "")
        )
    contests: "set[str]" = set()
    for team_id in teams:
        contests.update(parse_contest_ids(fetch(f"teams/{team_id}")))
    return sorted(contests)
