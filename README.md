# ncaa-softball-raw

Raw **stats.ncaa.org** play-by-play capture for NCAA **softball** (`sport_code=WSB`)
— the producer half of the pipeline. Discovers a season's contests, then captures
the raw pbp HTML as idempotent, resumable gzip bundles.

The **parser** lives in sdv-py
(`sportsdataverse.baseball.college_softball.parse_college_softball_ncaa_pbp` — a
by-reference re-export of the college-baseball parser; softball uses the identical
per-inning `<table class="table">` layout and play grammar). This repo does not
parse; it captures the raw tree the parser + `-data` ingest consume. Mirrors the
`ncaa-mfb-football-raw` producer split.

> **Men's baseball** lives in **`baseballr-data`** (`python/` producer). This repo
> was split off from the former `ncaa-baseball-raw` to be softball-only.

## Layout

```
python/
  discover.py       # team list (sport_code=WSB) -> team pages -> contest_ids
  capture.py        # /contests/{id}/play_by_play (+ box_score) -> json/{id}.json.gz
  run.py            # live runner (holds one browser session; NCAA_PROXY_POOL env)
  test_discover.py / test_capture.py   # offline
tests/fixtures/     # a real captured pbp page (baseball, as a structural stand-in
                    #   until a WSB game is captured -- identical table layout)
docs/DESIGN.md
scripts/run_capture.sh
```

## Status

- **Capture** works (given contest_ids) — the softball pbp page shares baseball's
  layout, so the shared capture + sdv-py parser apply unchanged.
- **Discovery is a TODO.** `WSB` is the confirmed softball sport_code (site sport
  dropdown), but `inst_team_list?sport_code=WSB` returns a ~23 KB shell with zero
  `/teams/` links — softball's team-list flow differs from baseball's, so
  `discover_season(sport_code="WSB")` currently raises. Provide contest_ids
  directly, or resolve the WSB discovery path (scoreboard / season-division route).

## Run

```sh
NCAA_PROXY_POOL="$(cat proxies.txt)" \
  python python/run.py --sport WSB --year 2025 --out ./raw
```

Transport = `sportsdataverse.mbb.mbb_ncaa_fetch.NcaaFetcher.with_browser`
(patchright + `--headless=new` + a **US-residential** proxy pool). Hold ONE session.
stats.ncaa.org IP-bans scrapers — run sparingly, paced, from a residential IP.
