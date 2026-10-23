import type { ApiResponse, LeaderRow, LeaderStat } from '~/types/api'

const STATS: Record<LeaderStat, string> = {
  pts: 'pts_pg',
  reb: 'reb_pg',
  ast: 'ast_pg',
  ts: 'ts_pct',
}

/**
 * GET /api/leaders?stat=pts&season=2026-27&limit=10
 * Qualifiers must have played 70% of the most games anyone has played this season
 * (and, for TS%, average at least 10 shot attempts).
 */
export default defineEventHandler(async (event): Promise<ApiResponse<LeaderRow[]>> => {
  const sql = useDb(event)
  const stat = String(getQuery(event).stat ?? 'pts') as LeaderStat
  if (!(stat in STATS)) {
    throw createError({ statusCode: 400, statusMessage: `stat must be one of ${Object.keys(STATS).join(', ')}` })
  }
  const season = seasonParam(event)
  const limit = intParam(event, 'limit', 10, 1, 50)
  const col = STATS[stat]

  const rows = await sql`
    WITH qual AS (
      SELECT max(gp) * 0.7 AS min_gp FROM player_seasons
      WHERE season = ${season} AND season_type = 'Regular Season' AND team_id = 0)
    SELECT a.${sql(col)} AS value, a.gp,
           p.id, p.slug, p.full_name, p.position, p.headshot_url, p.is_active,
           t.id AS team_id, t.abbr AS team_abbr, t.name AS team_name
    FROM player_season_averages a
    JOIN players p ON p.id = a.player_id
    LEFT JOIN teams t ON t.id = p.team_id, qual
    WHERE a.season = ${season} AND a.season_type = 'Regular Season' AND a.team_id = 0
      AND a.gp >= qual.min_gp AND a.${sql(col)} IS NOT NULL
      ${stat === 'ts' ? sql`AND (a.fga + 0.44 * a.fta) / NULLIF(a.gp, 0) >= 10` : sql``}
    ORDER BY value DESC
    LIMIT ${limit}`

  const data = rows.map((r, i): LeaderRow => ({ rank: i + 1, player: playerRef(r), value: r.value, gp: r.gp }))
  cacheFor(event, 1800)
  return { data, meta: await meta(event, ['player_stats'], season) }
})
