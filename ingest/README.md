# Ingest

A Python job that pulls NBA data into Postgres. The site never calls the stats sources
live: it reads what this job writes.

| Source | What it provides | Notes |
| --- | --- | --- |
| stats.nba.com via `nba_api` | players, career season stats (base and advanced), game logs, schedule, standings, team ratings, awards | Rate limited, and blocks GitHub's runners. Run its commands from a home machine, or set `NBA_API_PROXY`. |
| ESPN site API | scoreboard and schedule, box scores for the current season, news, team colors and logos | Public, no key. Reachable from GitHub. |
| balldontlie | games and scores when stats.nba.com fails | Needs `BALLDONTLIE_API_KEY`. Only used by `daily` as a fallback. |

## Run it

```sh
cd ingest
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgres://...

python -m bk_ingest migrate                  # create or update tables (db/migrations)

# NBA.com (from a home machine)
python -m bk_ingest history                  # once: every player, season totals since 1996-97, awards, Ledger
python -m bk_ingest daily                    # teams, players, standings, season stats, game logs, schedule
python -m bk_ingest weekly                   # awards (one call per active player, about 10 minutes), Ledger

# ESPN (what GitHub runs)
python -m bk_ingest nightly                  # schedule, box scores, season totals, standings, Ledger
python -m bk_ingest live                     # ESPN scoreboard for yesterday and today
python -m bk_ingest news
python -m bk_ingest boxscores --season 2025-26   # any single step runs on its own
python -m bk_ingest probe                    # which sources answer from here
python -m bk_ingest demo --confirm-demo      # dev only: fictional players and games for building pages
```

Each task is logged in `ingest_runs`; the site uses the newest successful run as the
"as of" time on every data view. A failed step doesn't stop the others in its group,
and the command exits non-zero if any step failed.

## Schedule

`.github/workflows/ingest.yml` runs it on GitHub Actions:

| When (UTC) | Command |
| --- | --- |
| every 15 min, 23:00–06:59 | `live` |
| hourly at :05 | `hourly` (news, scoreboard) |
| daily 10:30 | `nightly` (ESPN schedule, box scores, season totals, standings, Ledger) |

`history`, `daily` and `weekly` call stats.nba.com, which times out from GitHub, so they aren't
scheduled there.

ESPN box scores are matched to NBA.com players by name, and the ESPN id is saved on the player.
A player NBA.com hasn't been loaded for gets a placeholder row with id `-(ESPN id)`; the next
`players` run (part of `daily` and `history`) folds it into the real player.

Repository secrets: `DATABASE_URL` (required), `NBA_API_PROXY` and `BALLDONTLIE_API_KEY` (optional).
Run any command by hand from the Actions tab with "Run workflow".

## Tests

```sh
python -m pytest -q                                     # transforms only
TEST_DATABASE_URL=postgres://.../scratch python -m pytest -q   # also runs every task against Postgres
```

`TEST_DATABASE_URL` must point at a throwaway database: the tests drop and rebuild its
`public` schema. The test fixtures use made-up players.
