import type { ApiResponse, GameLogRow } from '~/types/api'

/** GET /api/players/:slug/games?season=2026-27&last=10 — game log, newest first. */
export default defineEventHandler(async (event): Promise<ApiResponse<GameLogRow[]>> => {
  const sql = useDb(event)
  const slug = getRouterParam(event, 'slug') ?? ''
  const season = seasonParam(event)
  const last = intParam(event, 'last', 0, 0, 200)

  const [p] = await sql`SELECT id FROM players WHERE slug = ${slug} OR id::text = ${slug} LIMIT 1`
  if (!p) notFound('Player')

  const rows = await sql`
    SELECT game_id, game_date, matchup, wl, min, pts, reb, ast, stl, blk, tov,
           fgm, fga, fg3m, fg3a, ftm, fta, plus_minus
    FROM player_games
    WHERE player_id = ${p.id} AND season = ${season}
    ORDER BY game_date DESC
    ${last ? sql`LIMIT ${last}` : sql``}`

  const data = rows.map((r): GameLogRow => {
    const home = r.matchup.includes(' vs. ')
    return {
      gameId: r.gameId,
      date: r.gameDate,
      matchup: r.matchup,
      opponent: r.matchup.split(home ? ' vs. ' : ' @ ')[1] ?? '',
      home,
      wl: r.wl,
      min: r.min,
      pts: r.pts,
      reb: r.reb,
      ast: r.ast,
      stl: r.stl,
      blk: r.blk,
      tov: r.tov,
      fgm: r.fgm,
      fga: r.fga,
      fg3m: r.fg3m,
      fg3a: r.fg3a,
      ftm: r.ftm,
      fta: r.fta,
      plusMinus: r.plusMinus,
    }
  })

  cacheFor(event, 600)
  return { data, meta: await meta(event, ['gamelogs'], season) }
})
