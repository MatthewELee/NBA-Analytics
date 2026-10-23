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

The house style lives at [`/styleguide`](http://localhost:3000/styleguide). All colors, type sizes and rules are tokens in `assets/styles/tokens.css`.

## Status

- [x] Step 1: foundation, tokens, fonts, Day and Night editions, styleguide
- [ ] Step 2: ingest job, Postgres schema, server routes
- [ ] Step 3: player, team and compare pages
- [ ] Step 4: home, the Ledger, search, deploy
