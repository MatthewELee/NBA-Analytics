import type { ApiResponse, SearchResults } from '~/types/api'

/** GET /api/search?q=gol — players (active first, then retired) and teams, for the "/" search box. */
export default defineEventHandler(async (event): Promise<ApiResponse<SearchResults>> => {
  const sql = useDb(event)
  const q = String(getQuery(event).q ?? '').trim().slice(0, 60)
  if (q.length < 2) {
    return { data: { players: [], teams: [] }, meta: { source: null, asOf: null } }
  }

  const [players, teams] = await Promise.all([
    sql`
      SELECT p.id, p.slug, p.full_name, p.position, p.headshot_url, p.is_active,
             t.id AS team_id, t.abbr AS team_abbr, t.name AS team_name
      FROM players p LEFT JOIN teams t ON t.id = p.team_id
      WHERE p.full_name ILIKE ${'%' + q + '%'} OR p.full_name % ${q}
      ORDER BY p.is_active DESC,
               (p.full_name ILIKE ${q + '%'} OR p.last_name ILIKE ${q + '%'}) DESC,
               similarity(p.full_name, ${q}) DESC, p.full_name
      LIMIT 8`,
    sql`
      SELECT id, abbr, city, name, color_primary FROM teams
      WHERE abbr ILIKE ${q} OR full_name ILIKE ${'%' + q + '%'}
      ORDER BY (abbr ILIKE ${q}) DESC, (name ILIKE ${q + '%'} OR city ILIKE ${q + '%'}) DESC, full_name
      LIMIT 4`,
  ])

  cacheFor(event, 300)
  return {
    data: {
      players: players.map(playerRef),
      teams: teams.map((t) => ({ id: t.id, abbr: t.abbr, city: t.city, name: t.name, colorPrimary: t.colorPrimary })),
    },
    meta: await meta(event, ['players']),
  }
})
