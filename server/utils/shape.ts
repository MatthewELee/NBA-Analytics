/* Row-to-response mappers shared by several routes. Rows arrive camelCased from useDb(). */
import type { GameSummary, PlayerRef, SeasonLine } from '~/types/api'

type Row = Record<string, any>

export const SEASON_LINE_COLUMNS = `
  season, season_type, team_abbr, age, gp, min_pg, pts_pg, reb_pg, ast_pg, stl_pg, blk_pg, tov_pg,
  fg3m_pg, fg_pct, fg3_pct, ft_pct, ts_pct, efg_pct, usg_pct, net_rating, pie, pts, reb, ast, stl, blk`

export function seasonLine(r: Row): SeasonLine {
  return {
    season: r.season,
    seasonType: r.seasonType,
    teamAbbr: r.teamAbbr,
    age: r.age,
    gp: r.gp,
    minPg: r.minPg,
    ptsPg: r.ptsPg,
    rebPg: r.rebPg,
    astPg: r.astPg,
    stlPg: r.stlPg,
    blkPg: r.blkPg,
    tovPg: r.tovPg,
    fg3mPg: r.fg3mPg,
    fgPct: r.fgPct,
    fg3Pct: r.fg3Pct,
    ftPct: r.ftPct,
    tsPct: r.tsPct,
    efgPct: r.efgPct,
    usgPct: r.usgPct,
    netRating: r.netRating,
    pie: r.pie,
    totals: { pts: r.pts, reb: r.reb, ast: r.ast, stl: r.stl, blk: r.blk },
  }
}

/** Expects columns id, slug, full_name, position, headshot_url, is_active, team_id, team_abbr, team_name. */
export function playerRef(r: Row): PlayerRef {
  return {
    id: r.id,
    slug: r.slug,
    fullName: r.fullName,
    position: r.position,
    headshotUrl: r.headshotUrl,
    isActive: r.isActive,
    team: r.teamId ? { id: r.teamId, abbr: r.teamAbbr, name: r.teamName } : null,
  }
}

/** SELECT list for games joined to home (h) and away (a) teams. */
export const GAME_COLUMNS = `
  g.id, g.game_date, g.tipoff, g.status, g.status_detail, g.home_score, g.away_score,
  h.id AS home_id, h.abbr AS home_abbr, h.name AS home_name, h.color_primary AS home_color,
  a.id AS away_id, a.abbr AS away_abbr, a.name AS away_name, a.color_primary AS away_color`

export function gameSummary(r: Row): GameSummary {
  return {
    id: r.id,
    date: r.gameDate,
    tipoff: r.tipoff ? new Date(r.tipoff).toISOString() : null,
    status: r.status,
    statusDetail: r.statusDetail,
    home: { id: r.homeId, abbr: r.homeAbbr, name: r.homeName, colorPrimary: r.homeColor, score: r.homeScore },
    away: { id: r.awayId, abbr: r.awayAbbr, name: r.awayName, colorPrimary: r.awayColor, score: r.awayScore },
  }
}
