"""Live runner: discover a season's contests + capture their pbp bundles.

Holds ONE ``NcaaFetcher.with_browser`` session (no per-call relaunch -- avoids the
patchright relaunch-storm crash) backed by a US-residential proxy pool read from
the ``NCAA_PROXY_POOL`` env var (newline/comma-separated ``http://user:pass@host:port``).

Usage::

    NCAA_PROXY_POOL="$(cat proxies.txt)" python python/run.py --sport WSB --year 2025 --out ./raw

stats.ncaa.org IP-bans scrapers -- run sparingly, paced, from a residential IP.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys

from capture import capture_season
from discover import (
    WSB_SEASON_DIVISIONS,
    browser_fetch_fn,
    discover_dates,
    discover_season,
)


def _pool() -> "list[str]":
    raw = os.environ.get("NCAA_PROXY_POOL", "")
    return [p.strip() for p in raw.replace(",", "\n").splitlines() if p.strip()]


def _season_dates(year: int) -> "list[str]":
    """MM/DD/YYYY across the D-I softball season (Feb 1 - Jun 15), for the
    scoreboard route. A scoreboard with no games simply yields no contests."""
    start, end = datetime.date(year, 2, 1), datetime.date(year, 6, 15)
    days = (end - start).days
    return [
        (start + datetime.timedelta(days=i)).strftime("%m/%d/%Y")
        for i in range(days + 1)
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description="NCAA baseball/softball raw pbp capture")
    ap.add_argument(
        "--sport",
        default="WSB",
        choices=["WSB", "MBA"],
        help="WSB=softball, MBA=baseball",
    )
    ap.add_argument("--year", type=int, required=True, help="academic year, e.g. 2025")
    ap.add_argument("--division", type=int, default=1)
    ap.add_argument("--out", required=True, help="output repo root for the json/ tree")
    ap.add_argument(
        "--max", type=int, default=None, help="cap NEW captures this run (chunking)"
    )
    args = ap.parse_args()

    pool = _pool()
    if not pool:
        print(
            "NCAA_PROXY_POOL is empty -- set a US-residential proxy pool",
            file=sys.stderr,
        )
        return 2

    fetch = browser_fetch_fn(proxy_pool=pool)  # one held session
    print(f"[discover] {args.sport} {args.year} D{args.division} ...", flush=True)
    if args.sport == "WSB":  # softball: scoreboard route (team-list returns a shell)
        sid = WSB_SEASON_DIVISIONS.get(args.year)
        if sid is None:
            print(f"no WSB season_divisions id for {args.year}", file=sys.stderr)
            return 2
        contests = discover_dates(sid, _season_dates(args.year), fetch_fn=fetch)
    else:  # baseball: team-list route
        contests = discover_season(args.year, args.division, args.sport, fetch_fn=fetch)
    print(f"[discover] {len(contests)} contests", flush=True)
    stats = capture_season(contests, fetch, args.out, max_contests=args.max)
    print(f"[capture] {stats}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
