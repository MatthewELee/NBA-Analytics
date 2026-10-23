# Ingest

A Python job that pulls NBA data into Postgres. The site never calls the stats sources
live: it reads what this job writes.

| Source | What it provides | Notes |
| --- | --- | --- |
| stats.nba.com via `nba_api` | players, season stats (base and advanced), game logs, schedule, standings, team ratings, awards | Rate limited and often blocks cloud IPs. Set `NBA_API_PROXY` if it refuses the runner. |
| ESPN site API | live scoreboard, news, team colors and logos | Public, no key. |
| balldontlie | games and scores when stats.nba.com fails | Needs `BALLDONTLIE_API_KEY`. Only used by `daily` as a fallback. |

## Run it

```sh
cd ingest
python -m venv .venv && . .venv/bin/activate
pip install -r requirements-dev.txt
export DATABASE_URL=postgres://...

python -m bk_ingest migrate                  # create or update tables (db/migrations)
python -m bk_ingest backfill                 # every player ever, season totals since 1996-97 (slow, run once)
python -m bk_ingest daily                    # teams, players, standings, season stats, game logs, schedule
python -m bk_ingest live                     # ESPN scoreboard for yesterday and today
python -m bk_ingest news
python -m bk_ingest awards                   # one call per active player, about 10 minutes
python -m bk_ingest gamelogs --season 2025-26
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
| daily 10:30 | `daily` |
| Mondays 12:00 | `weekly` (awards) |

Repository secrets: `DATABASE_URL` (required), `NBA_API_PROXY` and `BALLDONTLIE_API_KEY` (optional).
Run any command by hand from the Actions tab with "Run workflow".

## Tests

```sh
python -m pytest -q                                     # transforms only
TEST_DATABASE_URL=postgres://.../scratch python -m pytest -q   # also runs every task against Postgres
```

`TEST_DATABASE_URL` must point at a throwaway database: the tests drop and rebuild its
`public` schema. The test fixtures use made-up players.
