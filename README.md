# Baller Knowledge

An NBA analytics site set like a printed program: players, teams, side-by-side comparisons, and a ledger of records and awards.

Built with Nuxt 3, TypeScript, hand-written CSS and D3. See [`CLAUDE.md`](./CLAUDE.md) for the full spec, design direction and build plan.

## Run it

```sh
npm install
npm run dev        # http://localhost:3000
npm run build      # production build
npm run typecheck
```

Server routes read from Postgres. Copy `.env.example` to `.env` and set `NUXT_DATABASE_URL`; the data is loaded by the Python job in [`ingest/`](./ingest/README.md).

No database access to the live sources? `python -m bk_ingest demo --confirm-demo` (from `ingest/`) fills a dev database with fictional players and games, labelled as demo data on every page.

The house style lives at [`/styleguide`](http://localhost:3000/styleguide). All colors, type sizes and rules are tokens in `assets/styles/tokens.css`.

## Deploy (Cloudflare Workers)

The repo is connected to a Cloudflare Worker named `ball-knowledge` (Workers Builds), live at https://ball-knowledge.matt-e-lee.workers.dev.

- **Build settings:** build command `npm run build`, deploy command `npx wrangler deploy`, root directory `/`. Node comes from `.node-version`.
- **Config:** `wrangler.jsonc` holds the Worker name, the `nodejs_compat` flag and the bindings. Nitro detects the Workers build, uses its `cloudflare-module` preset, and writes the merged config to `.output/server/wrangler.json` (adding `no_nodejs_compat_v2` on purpose). Add bindings in `wrangler.jsonc`, not the dashboard: every deploy replaces the dashboard's bindings with the file's.
- **Database:** the Hyperdrive configuration for the Neon database is bound as `HYPERDRIVE` in `wrangler.jsonc`.

### Going live with real data

NBA.com blocks GitHub's servers, so the data comes in two ways. Career history comes from NBA.com, loaded once from your own computer. The current season is kept up to date every night from ESPN, which GitHub can reach.

1. Create a free Postgres database (Neon or Supabase) and add its connection string to GitHub as the repository secret `DATABASE_URL` (Settings → Secrets and variables → Actions).
2. **Load the history from your computer, once.** You need Python 3.12 and Git. In a terminal:

   ```sh
   git clone https://github.com/MatthewELee/NBA-Analytics.git
   cd NBA-Analytics/ingest
   python -m venv .venv
   .venv\Scripts\activate            # Windows. On macOS or Linux: source .venv/bin/activate
   pip install -r requirements.txt
   $env:DATABASE_URL = "postgresql://..."   # Windows PowerShell. On macOS or Linux: export DATABASE_URL="postgresql://..."
   python -m bk_ingest migrate
   python -m bk_ingest history
   ```

   `history` loads every player NBA.com has, season totals for every season since 1996-97, every active player's awards, and then the Ledger. It takes roughly half an hour and is safe to run again if it stops partway. Add `--first-season 1946-47` to go back to the league's first season. The Ledger then also shows where a player stands on the all-time lists.
3. **Start the nightly updates.** In GitHub, run the **Ingest** workflow by hand once (Actions → Ingest → Run workflow, command `nightly`). This loads this season's games and box scores so far. After that the schedule takes over: `nightly` at 6:30am ET (scores, schedule, box scores, season totals, standings and the Ledger), `live` every 15 minutes during games, and `hourly` for news.
4. In Cloudflare, create a Hyperdrive configuration with the same connection string and put its id in `wrangler.jsonc` under the `HYPERDRIVE` binding (already done for the live site).

**Now and then, from your computer** (same terminal setup, then one command):

- `python -m bk_ingest weekly` picks up new awards, such as Player of the Week, MVP and All-NBA. ESPN doesn't publish these in a form we can read.
- `python -m bk_ingest daily` replaces the computed standings and season stats with NBA.com's own, with official tiebreakers, PIE and player ratings, and full bios for players new this season.

How the nightly path works: ESPN box scores fill the game logs, and season totals, TS%, eFG%, usage, records, ranks, ratings and pace are computed from them (`ingest/bk_ingest/rollup.py`). ESPN players are matched to NBA.com players by name. Someone NBA.com hasn't been loaded for yet, usually a rookie, gets a placeholder that the next `daily` or `history` run folds into the real player, keeping the same page address. Ranks ignore the NBA's tiebreakers until `daily` runs.

With an `NBA_API_PROXY` secret, the NBA.com commands can run on GitHub as well. A `BALLDONTLIE_API_KEY` secret is optional and only used as a fallback for scores. `python -m bk_ingest probe` reports which sources answer from wherever it runs.

To try a production build locally: `NITRO_PRESET=cloudflare_module npm run build`, then `npx wrangler --cwd .output dev`.

## Status

- [x] Step 1: foundation, tokens, fonts, Day and Night editions, styleguide
- [x] Step 2: ingest job, Postgres schema, server routes
- [x] Step 3: player, team and compare pages
- [x] Step 4: home, the Ledger, search, season selector
- [ ] Live data and deploy

## API

All routes return `{ data, meta: { source, asOf, season? } }`.

| Route | Returns |
| --- | --- |
| `GET /api/players?q=` | player search |
| `GET /api/players/:slug?season=` | bio, season line, accolades, news |
| `GET /api/players/:slug/games?season=&last=` | game log |
| `GET /api/players/:slug/career?type=` | one line per season |
| `GET /api/teams?season=` | standings |
| `GET /api/teams/:abbr?season=` | record, ratings, roster, recent and upcoming games |
| `GET /api/teams/:abbr/games?season=` | results with running point differential |
| `GET /api/news?player=&team=&limit=` | ESPN headlines |
| `GET /api/scoreboard?date=` | games on an Eastern-time date |
| `GET /api/leaders?stat=pts\|reb\|ast\|ts&season=` | league leaders |
| `GET /api/ledger?kind=&player=&team=&before=` | Ledger entries, newest first, with a `next` cursor |
| `GET /api/story?season=&date=` | the stat of the day |
| `GET /api/search?q=` | players and teams for the `/` search |
| `GET /api/seasons` | seasons with data, newest first |
