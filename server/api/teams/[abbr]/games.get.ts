import type { ApiResponse, TeamGamePoint } from '~/types/api'

/** GET /api/teams/:abbr/games?season=2026-27 — every result in order, with running point differential. */
export default defineEventHandler(async (event): Promise<ApiResponse<TeamGamePoint[]>> => {
  const sql = useDb(event)
  const abbr = (getRouterParam(event, 'abbr') ?? '').toUpperCase()
  const season = seasonParam(event)

  const [t] = await sql`SELECT id FROM teams WHERE abbr = ${abbr}`
  if (!t) notFound('Team')

  const rows = await sql`
    SELECT game_id, game_date, matchup, wl, pts, opp_pts, plus_minus,
           sum(coalesce(plus_minus, 0)) OVER (ORDER BY game_date, game_id) AS cumulative
    FROM team_games
    WHERE team_id = ${t.id} AND season = ${season} AND season_type = 'Regular Season'
    ORDER BY game_date, game_id`

  const data = rows.map((r): TeamGamePoint => ({
    gameId: r.gameId,
    date: r.gameDate,
    matchup: r.matchup,
    wl: r.wl,
    pts: r.pts,
    oppPts: r.oppPts,
    plusMinus: r.plusMinus,
    cumulative: r.cumulative,
  }))

  cacheFor(event, 900)
  return { data, meta: await meta(event, ['gamelogs'], season) }
})
