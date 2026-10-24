# Baller Knowledge

An NBA analytics site and portfolio piece. People come here to look up players, compare them side by side, check team stats, and keep up with records and awards. It should feel like a printed sports almanac crossed with a gallery poster. It should not look like another SaaS dashboard.

## Repo
- Repo: `MatthewELee/NBA-Analytics`. Rebuild it from scratch. The current contents are an untouched Vue/Vite starter plus Bootstrap, and all of it gets replaced, including the nested `NBA Analytics/` folder.
- This file belongs at the repo root as `CLAUDE.md`.

## Build plan
1. **Foundation.** Clear out the old starter and set up a fresh Nuxt 3 + TypeScript project at the repo root. Add the design tokens, fonts, both editions (light and dark), and a `/styleguide` page that shows type, color, rules, a table, and a chart, so the look is approved before any feature work.
2. **Data.** Write the Python ingest job in `ingest/` (nba_api, with balldontlie as a fallback, and ESPN for news, awards, and the scoreboard), set up the Postgres schema, schedule the job, and add Nuxt server routes that serve player, team, and news data.
3. **Core pages.** Build the player page, the team page, and Compare.
4. **Home, the Ledger, and launch.** Build the milestone detection, the Ledger feed, the Home page, and global search, then deploy to Cloudflare.

## Site content

### Home: "Tonight"
- A scoreboard strip with today's games (live or final scores, plus tip-off times for upcoming games).
- League leaders in points, rebounds, assists, and true shooting, shown as a ranked typographic list instead of a stack of cards.
- The Ledger rail (see below), showing its 5 newest items.
- One featured stat story: one stat, one big number, and one chart, chosen each day (for example, "Most 40-point games this season").

### Player page `/players/[slug]`
- A header with the player's name in large display type, plus team, position, height, age, and draft info.
- A season line: per-game stats and a few advanced ones (TS%, usage, PER or BPM if the data supports it).
- A game log table that can be sorted and filtered by last 5, last 10, or the full season.
- Career arc: a chart of a chosen stat over the player's seasons.
- A shot chart drawn on court lines (only if the data source has shot locations).
- Accolades: All-Star, All-NBA, MVP, and other awards, plus any records held.

### Compare `/compare?p=a,b[,c]`
- Room for up to 3 players, searched and added inline.
- Mirrored bar rows (a "tale of the tape") for per-game stats, advanced stats, and accolades.
- A per-season overlay chart with a stat picker.
- Settings live in the URL so a comparison can be shared as a link.

### Team page `/teams/[abbr]`
- Record, standing, and offensive, defensive, and net ratings, plus pace.
- The roster with key stats for each player.
- Recent results and the schedule ahead.
- A season chart showing net rating or point differential over time.

### The Ledger `/ledger` (records and accolades)
- A feed of records broken, milestones reached (for example, "passes 20,000 career points"), and awards (Player of the Week or Month, MVP, and so on).
- Each item links to the player or team and carries a date and source.
- It also appears as a side rail on Home and on player pages.

### Global
- Search for players and teams from any page, opened with the `/` key.
- Season selector (default is the current season).
- A light theme (the "Day edition") and a dark one (the "Night edition").

## Design direction

**Concept: the printed program.** Think of a 1970s arena program, a newspaper box score, and a Swiss-style poster put together. The page is paper and the content is ink.

### Do
- Use flat color only, from a small palette:
  - Day edition: off-white newsprint background (`#F2EEE3`), ink (`#141414`), one spot color for emphasis, either hardwood orange (`#D9531E`) or court red, and one muted secondary.
  - Night edition: near-black background (`#121212`), bone-colored text (`#E9E4D8`), and the same spot color.
- Use team colors only as small flat accents on team and player pages, never as backgrounds behind text.
- Build layout on a strict grid with visible hairline rules (1px lines) and generous margins. Mix in asymmetric, editorial compositions. Big numbers are allowed to break the grid.
- Type does most of the visual work:
  - Display: a heavy condensed sans such as Big Shoulders Display or Anton, set very large and tightly spaced.
  - Body: a serif with character such as Newsreader or Source Serif 4.
  - Numbers: a monospace with tabular figures such as IBM Plex Mono or JetBrains Mono. Every stat column uses tabular numbers.
- Allowed textures: halftone dots, court-line drawings, and paper grain. Keep each one subtle and flat, as SVG or CSS patterns.
- Charts should look drawn, not like widget output: thin ink lines, direct labels instead of legends, the spot color for the one series that matters, no chart junk.
- Use small, deliberate motion: numbers ticking up on first view, rows sliding in, underlines on hover. Respect `prefers-reduced-motion`.

### Don't (the "AI design" tells to avoid)
- No gradients of any kind, including gradient text, mesh backgrounds, and glow effects.
- No glassmorphism, backdrop blur, or neon accents.
- No purple-to-blue palettes, and no default Tailwind or shadcn look.
- No grids of soft rounded cards with drop shadows. Corners are square or nearly square, and depth comes from rules and contrast, not shadows.
- No emoji as icons, and no generic icon packs scattered around for decoration.
- No Inter, Roboto, or system font as the main typeface.
- No centered hero section with a headline, a subhead, and two buttons.
- No stock photos and no AI-generated imagery. Use real headshots and team logos from the API or CDN, or use typography instead.

## Tech stack

- **Framework:** Nuxt 3 (Vue 3) with TypeScript. This keeps the Vue start from the original repo and adds file-based routing, SSR for shareable and SEO-friendly player pages, and server routes.
- **Styling:** hand-written CSS with design tokens as CSS custom properties, using Vue scoped styles. No Bootstrap and no utility framework. The look is the point of the project.
- **Charts:** D3, or Observable Plot built on D3, rendered to SVG, so every chart can be styled to match the design.
- **Data:**
  - Stats come from the `nba_api` Python package (it wraps stats.nba.com) or the balldontlie API. stats.nba.com often blocks cloud IP addresses, so the site never calls it live. A scheduled ingest job pulls the data and writes it to the database.
  - News, awards, and the scoreboard come from ESPN's public site API (`site.api.espn.com/apis/site/v2/sports/basketball/nba/...`), which has news and scoreboard endpoints.
  - Ledger milestones are computed by our own ingest job, by checking career totals against round-number thresholds and known records.
- **Storage:** Postgres hosted on Neon or Supabase (free tier). Nuxt server routes read from it and cache responses. On Cloudflare, server routes connect through Hyperdrive with postgres.js, opening one small client per request (`server/utils/db.ts`, closed in `server/plugins/db.ts`).
- **Ingest:** a Python script in `ingest/`, run on a schedule (GitHub Actions cron or a small worker).
- **Hosting:** a Cloudflare Worker (`ball-knowledge`, Workers Builds) connected to the repo. Nitro detects the Workers build and uses its `cloudflare-module` preset (build command `npm run build`, deploy command `npx wrangler deploy`). `wrangler.jsonc` holds the Worker name, the `nodejs_compat` flag and the Hyperdrive binding `HYPERDRIVE`; bindings go there, since each deploy replaces any set only in the dashboard. Not Vercel: the old Vercel project linked to the repo can be disconnected.

## Conventions
- Keep design tokens in `assets/styles/tokens.css`. Never hard-code colors or font sizes in components.
- Every stat table uses tabular figures and aligns numbers to the right.
- Show the source and an "as of" timestamp on every data view.
- Accessibility: WCAG AA contrast in both editions, full keyboard support for search and compare, and charts that come with a text or table alternative.
