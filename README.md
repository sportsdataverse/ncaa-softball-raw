# ncaa-baseball-raw

Raw **stats.ncaa.org** play-by-play capture for NCAA **baseball** (`MBA`) and
**softball** (`WSB`) — the producer half of the pipeline. Discovers a season's
contests, then captures the raw pbp HTML as idempotent, resumable gzip bundles.

The **parser** lives in sdv-py
(`sportsdataverse.baseball.college_baseball.parse_college_baseball_ncaa_pbp`,
softball re-exports it) — this repo does not parse; it captures the raw tree the
`-data` ingest and that parser consume. This mirrors the `ncaa-mfb-hoops-raw` /
`ncaa-mbb-hoops-raw` producer split.

## Layout

```
python/
  discover.py       # team list (sport_code=MBA|WSB) -> team pages -> contest_ids
  capture.py        # /contests/{id}/play_by_play (+ box_score) -> json/{id}.json.gz
  run.py            # live runner (holds one browser session; proxy pool from env)
  test_discover.py  # offline (pure parsers + injected fetch)
  test_capture.py   # offline (real fixture + tmp out_dir)
tests/fixtures/     # real captured pbp page(s)
docs/DESIGN.md
scripts/run_capture.sh
```

## Transport

Capture drives `sportsdataverse.mbb.mbb_ncaa_fetch.NcaaFetcher.with_browser`
(patchright + `--headless=new` + a **US-residential** proxy pool — datacenter IPs
get an instant edge 403). Hold ONE session; do not relaunch per-call (the
patchright driver crashes under a relaunch storm). See sdv-py PRs #271 / #276.

## Run

```sh
NCAA_PROXY_POOL="$(cat proxies.txt)" \
  python python/run.py --sport MBA --year 2025 --out ./raw --max 200
```

**stats.ncaa.org IP-bans scrapers** — run sparingly, paced, from a residential IP.
Resume is file-exists based (Ctrl-C safe); a consecutive-failure breaker hard-stops
a ban/challenge storm.

## Status

- **Baseball (MBA):** discovery + capture working (307 D1 teams for 2025).
- **Softball (WSB):** capture works; **discovery is a TODO** — `WSB` is the
  confirmed sport code but `inst_team_list?sport_code=WSB` returns a shell (its
  team-list flow differs from baseball's). Provide contest_ids directly until the
  WSB discovery flow is resolved.
