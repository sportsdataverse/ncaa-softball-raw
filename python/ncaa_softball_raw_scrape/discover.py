"""NCAA softball (sport_code=WSB) season discovery: team list -> team pages ->
contest_ids.

Pure parse functions + an injectable ``fetch_fn`` so discovery is fully offline-
testable; the live default drives ``NcaaFetcher.with_browser`` (real-GPU host +
US residential proxy pool -- see docs/DESIGN.md; datacenter IPs get an edge 403).

**Two discovery routes.** The team-list route
(:func:`discover_season`, ``inst_team_list?sport_code=WSB``) returns a ~23 KB shell
with zero teams for softball -- WSB's team-list flow differs from baseball's, so it
DOES NOT work for WSB. Use the **scoreboard route** instead
(:func:`discover_dates`): the ``season_divisions/{id}/scoreboards`` daily scoreboard
lists every ``/contests/{id}`` played on a date, and works for softball (verified
e2e 2026-07-17: 43 contests for 2025-04-12). The WSB ``season_divisions`` id is
resolved from the site sport dropdown (``?sport_code=WSB`` -> 18763 for 2025); see
:data:`WSB_SEASON_DIVISIONS`. The baseball (``MBA``) producer lives in the
``baseballr-data`` repo.
"""

from __future__ import annotations

import re
from typing import Callable, Iterable, List, Optional

FetchFn = Callable[[str], str]  # (path) -> html

_TEAM_ID_RE = re.compile(r"/teams/(\d+)")
_CONTEST_ID_RE = re.compile(r"/contests/(\d+)/")

#: WSB (softball) ``season_divisions`` ids by season, resolved from the site sport
#: dropdown (``stats.ncaa.org/?sport_code=WSB``). Extend forward as confirmed.
WSB_SEASON_DIVISIONS: "dict[int, int]" = {2025: 18763}


def team_list_path(academic_year: int, division: int = 1, sport_code: str = "WSB") -> str:
    """stats.ncaa.org team-list path. ``sport_code`` WSB=softball / MBA=baseball;
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


def scoreboard_path(season_division_id: int, game_date: str, conference_id: int = 0) -> str:
    """stats.ncaa.org daily scoreboard path. ``game_date`` is ``MM/DD/YYYY``;
    ``conference_id`` 0 = all conferences."""
    return (
        f"season_divisions/{season_division_id}/scoreboards"
        f"?game_date={game_date.replace('/', '%2F')}&conference_id={conference_id}&commit=Submit"
    )


def discover_dates(
    season_division_id: int,
    dates: "Iterable[str]",
    *,
    fetch_fn: Optional[FetchFn] = None,
) -> List[str]:
    """Discover softball ``contest_id``\\ s across a set of dates via the scoreboard.

    This is the WORKING softball route (the team-list route returns a shell for WSB).

    Args:
        season_division_id: e.g. ``WSB_SEASON_DIVISIONS[2025]`` (18763).
        dates: ``MM/DD/YYYY`` strings spanning the season (a launcher passes the
            softball-season calendar; a scoreboard with no games yields nothing).
        fetch_fn: ``(path) -> html``. Defaults to a live browser session.

    Returns:
        Sorted, de-duplicated list of ``contest_id`` strings across all dates.
    """
    fetch = fetch_fn or browser_fetch_fn()
    contests: "set[str]" = set()
    for game_date in dates:
        contests.update(parse_contest_ids(fetch(scoreboard_path(season_division_id, game_date))))
    return sorted(contests)


def discover_season(
    academic_year: int,
    division: int = 1,
    sport_code: str = "WSB",
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
