-- Baller Knowledge schema, v1.
-- Written by the Python ingest job (ingest/), read by Nuxt server routes (server/).
-- Seasons are stored as the NBA's label, e.g. '2026-27'.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Every ingest task logs a run here. Server routes read the latest success as "as of".
CREATE TABLE ingest_runs (
  id           bigserial PRIMARY KEY,
  task         text        NOT NULL,
  source       text        NOT NULL,
  season       text,
  started_at   timestamptz NOT NULL DEFAULT now(),
  finished_at  timestamptz,
  ok           boolean,
  rows_written integer,
  error        text
);
CREATE INDEX ingest_runs_task_idx ON ingest_runs (task, finished_at DESC) WHERE ok;

CREATE TABLE teams (
  id              integer PRIMARY KEY,          -- NBA.com team id
  abbr            text    NOT NULL UNIQUE,      -- NBA.com abbreviation, e.g. 'GSW'
  city            text    NOT NULL,
  name            text    NOT NULL,             -- nickname, e.g. 'Warriors'
  full_name       text    NOT NULL,
  conference      text,
  division        text,
  espn_id         text,
  color_primary   text,                         -- hex without '#', from ESPN
  color_secondary text,
  logo_url        text,
  updated_at      timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE players (
  id            integer PRIMARY KEY,            -- NBA.com person id
  slug          text    NOT NULL UNIQUE,        -- 'stephen-curry'
  first_name    text    NOT NULL,
  last_name     text    NOT NULL,
  full_name     text    NOT NULL,
  team_id       integer REFERENCES teams (id),
  jersey        text,
  position      text,
  height        text,                           -- '6-2'
  weight_lb     integer,
  birthdate     date,
  country       text,
  college       text,
  draft_year    integer,
  draft_round   integer,
  draft_number  integer,
  from_year     integer,
  to_year       integer,
  is_active     boolean NOT NULL DEFAULT false,
  headshot_url  text,
  bdl_id        integer,                        -- balldontlie id, for the fallback source
  updated_at    timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX players_name_trgm ON players USING gin (full_name gin_trgm_ops);
CREATE INDEX players_team_idx ON players (team_id) WHERE is_active;

-- One row per player per season. team_id = 0 is the season total across every team the
-- player played for (what the league dashboard returns); team_abbr is the team they
-- finished the season with. Per-team splits can be added later with real team ids.
CREATE TABLE player_seasons (
  player_id   integer NOT NULL REFERENCES players (id),
  season      text    NOT NULL,
  season_type text    NOT NULL DEFAULT 'Regular Season',
  team_id     integer NOT NULL DEFAULT 0,
  team_abbr   text,
  age         numeric(4,1),
  gp          integer NOT NULL DEFAULT 0,
  gs          integer,
  min         numeric(8,1),
  pts         integer, reb integer, oreb integer, dreb integer, ast integer,
  stl         integer, blk integer, tov integer, pf integer,
  fgm         integer, fga integer, fg3m integer, fg3a integer, ftm integer, fta integer,
  plus_minus  integer,
  -- advanced
  ts_pct      numeric(5,3),
  efg_pct     numeric(5,3),
  usg_pct     numeric(5,3),
  off_rating  numeric(6,1),
  def_rating  numeric(6,1),
  net_rating  numeric(6,1),
  pie         numeric(5,3),
  pace        numeric(6,2),
  updated_at  timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (player_id, season, season_type, team_id)
);
CREATE INDEX player_seasons_season_idx ON player_seasons (season, season_type);

CREATE TABLE games (
  id             text PRIMARY KEY,              -- NBA.com game id, e.g. '0022600123'
  season         text NOT NULL,
  season_type    text NOT NULL DEFAULT 'Regular Season',
  game_date      date NOT NULL,
  tipoff         timestamptz,
  home_team_id   integer NOT NULL REFERENCES teams (id),
  away_team_id   integer NOT NULL REFERENCES teams (id),
  home_score     integer,
  away_score     integer,
  status         text NOT NULL DEFAULT 'scheduled',  -- scheduled | live | final | postponed
  status_detail  text,                           -- 'Q3 4:12', 'Final/OT'
  espn_id        text UNIQUE,
  updated_at     timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX games_date_idx ON games (game_date);
CREATE INDEX games_home_idx ON games (home_team_id, game_date);
CREATE INDEX games_away_idx ON games (away_team_id, game_date);

-- Box score line for one player in one game.
CREATE TABLE player_games (
  player_id   integer NOT NULL REFERENCES players (id),
  game_id     text    NOT NULL,
  season      text    NOT NULL,
  season_type text    NOT NULL DEFAULT 'Regular Season',
  game_date   date    NOT NULL,
  team_id     integer NOT NULL REFERENCES teams (id),
  matchup     text    NOT NULL,                 -- 'GSW vs. LAL' or 'GSW @ LAL'
  wl          char(1),
  min         numeric(5,1),
  pts integer, reb integer, oreb integer, dreb integer, ast integer,
  stl integer, blk integer, tov integer, pf integer,
  fgm integer, fga integer, fg3m integer, fg3a integer, ftm integer, fta integer,
  plus_minus  integer,
  PRIMARY KEY (player_id, game_id)
);
CREATE INDEX player_games_player_date_idx ON player_games (player_id, game_date DESC);
CREATE INDEX player_games_game_idx ON player_games (game_id);

-- Team line for one game (points for and against, used for the season chart).
CREATE TABLE team_games (
  team_id     integer NOT NULL REFERENCES teams (id),
  game_id     text    NOT NULL,
  season      text    NOT NULL,
  season_type text    NOT NULL DEFAULT 'Regular Season',
  game_date   date    NOT NULL,
  matchup     text    NOT NULL,
  wl          char(1),
  pts         integer,
  opp_pts     integer,
  plus_minus  integer,
  PRIMARY KEY (team_id, game_id)
);
CREATE INDEX team_games_team_date_idx ON team_games (team_id, game_date DESC);

CREATE TABLE team_seasons (
  team_id      integer NOT NULL REFERENCES teams (id),
  season       text    NOT NULL,
  season_type  text    NOT NULL DEFAULT 'Regular Season',
  wins         integer NOT NULL DEFAULT 0,
  losses       integer NOT NULL DEFAULT 0,
  conf_rank    integer,
  div_rank     integer,
  league_rank  integer,
  games_back   numeric(4,1),
  streak       text,
  last_ten     text,
  home_record  text,
  road_record  text,
  pts_pg       numeric(5,1),
  opp_pts_pg   numeric(5,1),
  off_rating   numeric(6,1),
  def_rating   numeric(6,1),
  net_rating   numeric(6,1),
  pace         numeric(6,2),
  updated_at   timestamptz NOT NULL DEFAULT now(),
  PRIMARY KEY (team_id, season, season_type)
);

CREATE TABLE awards (
  id           bigserial PRIMARY KEY,
  player_id    integer NOT NULL REFERENCES players (id),
  award        text    NOT NULL,                -- 'NBA Most Valuable Player', 'All-NBA'
  season       text    NOT NULL,
  team_label   text,                            -- 'All-NBA 1st Team' etc. ('1', '2', '3' from source)
  month        text,
  week         text,
  conference   text,
  description  text,
  source       text    NOT NULL,
  UNIQUE NULLS NOT DISTINCT (player_id, award, season, team_label, month, week)
);
CREATE INDEX awards_player_idx ON awards (player_id);

CREATE TABLE news (
  id           text PRIMARY KEY,                -- ESPN article id
  headline     text NOT NULL,
  description  text,
  url          text NOT NULL,
  image_url    text,
  published_at timestamptz NOT NULL,
  byline       text,
  player_ids   integer[] NOT NULL DEFAULT '{}', -- NBA.com ids matched from ESPN categories
  team_ids     integer[] NOT NULL DEFAULT '{}',
  source       text NOT NULL DEFAULT 'ESPN',
  fetched_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX news_published_idx ON news (published_at DESC);
CREATE INDEX news_players_idx ON news USING gin (player_ids);
CREATE INDEX news_teams_idx ON news USING gin (team_ids);

-- The Ledger: records, milestones and awards. Filled by the milestone detector in step 4.
CREATE TABLE ledger_items (
  id           bigserial PRIMARY KEY,
  kind         text    NOT NULL CHECK (kind IN ('record', 'milestone', 'award')),
  headline     text    NOT NULL,
  detail       text,
  player_id    integer REFERENCES players (id),
  team_id      integer REFERENCES teams (id),
  stat         text,
  value        numeric,
  threshold    numeric,
  occurred_on  date    NOT NULL,
  source       text    NOT NULL,
  source_url   text,
  dedupe_key   text    NOT NULL UNIQUE,         -- e.g. 'milestone:201939:pts:25000'
  created_at   timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX ledger_items_date_idx ON ledger_items (occurred_on DESC, id DESC);
CREATE INDEX ledger_items_player_idx ON ledger_items (player_id);

-- Per-game view of player_seasons, used by most read paths.
CREATE VIEW player_season_averages AS
SELECT
  ps.*,
  round(ps.min / NULLIF(ps.gp, 0), 1)                    AS min_pg,
  round(ps.pts::numeric / NULLIF(ps.gp, 0), 1)           AS pts_pg,
  round(ps.reb::numeric / NULLIF(ps.gp, 0), 1)           AS reb_pg,
  round(ps.ast::numeric / NULLIF(ps.gp, 0), 1)           AS ast_pg,
  round(ps.stl::numeric / NULLIF(ps.gp, 0), 1)           AS stl_pg,
  round(ps.blk::numeric / NULLIF(ps.gp, 0), 1)           AS blk_pg,
  round(ps.tov::numeric / NULLIF(ps.gp, 0), 1)           AS tov_pg,
  round(ps.fg3m::numeric / NULLIF(ps.gp, 0), 1)          AS fg3m_pg,
  round(ps.fgm::numeric / NULLIF(ps.fga, 0), 3)          AS fg_pct,
  round(ps.fg3m::numeric / NULLIF(ps.fg3a, 0), 3)        AS fg3_pct,
  round(ps.ftm::numeric / NULLIF(ps.fta, 0), 3)          AS ft_pct
FROM player_seasons ps;
