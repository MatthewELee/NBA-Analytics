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

## Deploy (Cloudflare Pages)

The repo is connected to a Cloudflare Pages project.

- **Build settings:** framework preset Nuxt.js, build command `npm run build`, output directory `dist`. Node comes from `.node-version`.
- **Runtime:** add the `nodejs_compat` compatibility flag (Settings → Runtime) for production and preview.
- **Database:** create a Hyperdrive configuration pointing at the Postgres database, then add a Hyperdrive binding named `HYPERDRIVE` (Settings → Bindings).

To try a production build locally: `NITRO_PRESET=cloudflare_pages npm run build`, then `npx wrangler pages dev dist`.

## Status

- [x] Step 1: foundation, tokens, fonts, Day and Night editions, styleguide
- [x] Step 2: ingest job, Postgres schema, server routes
- [x] Step 3: player, team and compare pages
- [ ] Step 4: home, the Ledger, search, deploy

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
