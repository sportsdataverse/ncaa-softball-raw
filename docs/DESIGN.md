# NCAA baseball + softball raw pbp — design

**Status:** built 2026-07-17. Parser shipped in sdv-py (#279); this is the
producer (discover + capture).

## Understanding
- **Feasible + validated:** stats.ncaa.org serves per-inning
  `<table class="table">` play-by-play at `/contests/{id}/play_by_play` (~45–55 KB),
  gated by Akamai bm-verify (cleared by `NcaaFetcher.with_browser`). Baseball D1
  discovery via `team/inst_team_list?...&sport_code=MBA&division=1` → 307 teams for
  2025; team pages → `/contests/{id}` links.
- **The parser is the crux and already lives in sdv-py** — this repo only captures
  the raw tree, mirroring the MBB/MFB producer split.

## Pipeline
1. **Discover** (`discover.py`): team list (MBA|WSB) → team pages → dedup contest_ids.
2. **Capture** (`capture.py`): `/contests/{id}/play_by_play` (+ `box_score`) →
   gzip JSON bundle `json/{id}.json.gz`. Idempotent (file-exists resume);
   consecutive-failure breaker.
3. **Parse** (downstream, sdv-py): `parse_college_baseball_ncaa_pbp` on each bundle.
4. **Publish** (`-data`, later): tidy parquet + gh release.

## Decisions
| Decision | Why |
|---|---|
| Source = stats.ncaa.org | official all-division data; parser validated on it |
| Parser in sdv-py, capture here | mirrors MBB/MFB split; one parser, many producers |
| One repo for MBA + WSB | identical page layout + grammar; sport_code param |
| Hold one browser session | avoids the patchright relaunch-storm (EPIPE) crash |

## Open risks
1. **Softball (WSB) discovery** — `inst_team_list?sport_code=WSB` returns a shell;
   WSB is the confirmed code but its team-list flow differs. TODO: resolve the WSB
   discovery path (scoreboard / season-division route). Capture works given ids.
2. **IP bans** — stats.ncaa.org bans scrapers; pace rotation, residential only.
3. **Relaunch storm (EPIPE)** — hold the IP, rotate on real failure only.
