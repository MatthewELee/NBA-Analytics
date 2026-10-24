import type { ApiResponse } from '~/types/api'

/** GET /api/seasons — season labels with stats loaded, newest first. Always includes the current one. */
export default defineEventHandler(async (event): Promise<ApiResponse<string[]>> => {
  const sql = useDb(event)
  const rows = await sql<{ season: string }[]>`
    SELECT DISTINCT season FROM player_seasons WHERE season_type = 'Regular Season'
    ORDER BY season DESC LIMIT 30`
  const current = currentSeason()
  const seasons = rows.map((r) => r.season)
  if (!seasons.includes(current)) seasons.unshift(current)
  cacheFor(event, 3600)
  return { data: seasons, meta: { source: null, asOf: null, season: current } }
})
