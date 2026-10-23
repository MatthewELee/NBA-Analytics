import type { ApiResponse, SeasonLine } from '~/types/api'

/** GET /api/players/:slug/career?type=Playoffs — one line per season, oldest first. */
export default defineEventHandler(async (event): Promise<ApiResponse<SeasonLine[]>> => {
  const sql = useDb(event)
  const slug = getRouterParam(event, 'slug') ?? ''
  const type = getQuery(event).type === 'Playoffs' ? 'Playoffs' : 'Regular Season'

  const [p] = await sql`SELECT id FROM players WHERE slug = ${slug} OR id::text = ${slug} LIMIT 1`
  if (!p) notFound('Player')

  const rows = await sql`
    SELECT ${sql.unsafe(SEASON_LINE_COLUMNS)} FROM player_season_averages
    WHERE player_id = ${p.id} AND season_type = ${type} AND team_id = 0
    ORDER BY season`

  cacheFor(event, 3600)
  return { data: rows.map(seasonLine), meta: await meta(event, ['player_stats']) }
})
