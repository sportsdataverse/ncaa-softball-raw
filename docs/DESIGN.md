# NCAA softball raw pbp — design

**Status:** built 2026-07-17 (as part of a baseball+softball producer; split into
this softball-only repo — men's baseball moved to `baseballr-data`). Parser shipped
in sdv-py (#279); this is the producer (discover + capture).

## Understanding
- **Same platform as baseball.** stats.ncaa.org serves per-inning
  `<table class="table">` play-by-play at `/contests/{id}/play_by_play`, gated by
  Akamai bm-verify (cleared by `NcaaFetcher.with_browser`). Softball pbp uses the
  identical layout + play grammar as baseball, so the sdv-py parser
  (`parse_college_softball_ncaa_pbp`, a by-reference re-export of the baseball
  parser) and this capture apply unchanged.
- **The parser lives in sdv-py** — this repo only captures the raw tree.

## Pipeline
1. **Discover** (`discover.py`): team list (`sport_code=WSB`) → team pages → dedup
   contest_ids. **TODO:** WSB `inst_team_list` returns a shell (see risks).
2. **Capture** (`capture.py`): `/contests/{id}/play_by_play` (+ `box_score`) →
   gzip JSON bundle `json/{id}.json.gz`. Idempotent; consecutive-failure breaker.
3. **Parse** (downstream, sdv-py): `parse_college_softball_ncaa_pbp` on each bundle.
4. **Publish** (`-data`, later): tidy parquet + gh release.

## Decisions
| Decision | Why |
|---|---|
| Softball-only repo | split from ncaa-baseball-raw; baseball -> baseballr-data |
| Parser in sdv-py, capture here | mirrors MBB/MFB split; one parser, many producers |
| Hold one browser session | avoids the patchright relaunch-storm (EPIPE) crash |

## Open risks
1. **WSB discovery (primary TODO)** — `inst_team_list?sport_code=WSB` returns a
   ~23 KB shell with zero `/teams/` links; WSB is the confirmed sport_code but its
   team-list flow differs from baseball's. Resolve via the scoreboard /
   season-division route, or provide contest_ids directly. Capture works given ids.
2. **No native WSB fixture yet** — the offline capture test uses a real baseball
   pbp page as a structural stand-in (identical table layout) until a WSB game is
   captured.
3. **IP bans / relaunch storm** — pace rotation, residential only; hold the IP.
