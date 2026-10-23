import type { ApiResponse, GameSummary } from '~/types/api'

/** GET /api/scoreboard?date=2026-10-23 — every game on an Eastern-time date (default today). */
export default defineEventHandler(async (event): Promise<ApiResponse<GameSummary[]>> => {
  const sql = useDb(event)
  const raw = getQuery(event).date
  if (raw !== undefined && (typeof raw !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(raw))) {
    throw createError({ statusCode: 400, statusMessage: 'date must look like 2026-10-23' })
  }
  const day = typeof raw === 'string' ? raw : new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })

  const rows = await sql`
    SELECT ${sql.unsafe(GAME_COLUMNS)}
    FROM games g JOIN teams h ON h.id = g.home_team_id JOIN teams a ON a.id = g.away_team_id
    WHERE g.game_date = ${day}
    ORDER BY g.tipoff NULLS LAST, g.id`

  const games = rows.map(gameSummary)
  // Live scores go stale fast; finished or future slates can be cached longer.
  cacheFor(event, games.some((g) => g.status === 'live') ? 30 : 300)
  return { data: games, meta: { ...(await meta(event, ['scoreboard', 'schedule', 'gamelogs'])), season: currentSeason(new Date(`${day}T12:00:00Z`)) } }
})
