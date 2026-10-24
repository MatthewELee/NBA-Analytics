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

1. Create a free Postgres database (Neon or Supabase) and copy its connection string.
2. In GitHub, add it as the repository secret `DATABASE_URL` (Settings → Secrets and variables → Actions).
3. Run the **Ingest** workflow by hand (Actions → Ingest → Run workflow): `backfill` first (every player and every season since 1996-97; it runs the schema migrations too), then `daily`, then `weekly` for awards. After that the schedule keeps it current.
4. In Cloudflare, create a Hyperdrive configuration with the same connection string and put its id in `wrangler.jsonc` under the `HYPERDRIVE` binding (already done for the live site).

Stats come from stats.nba.com through `nba_api` (no key). NBA.com sometimes blocks cloud servers, GitHub's runners included: if the stats steps fail with timeouts, set an `NBA_API_PROXY` secret, or run `python -m bk_ingest daily` from your own machine with `DATABASE_URL` set. Scores and news come from ESPN's public API (no key). A `BALLDONTLIE_API_KEY` secret is optional and only used as a fallback for scores.

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
