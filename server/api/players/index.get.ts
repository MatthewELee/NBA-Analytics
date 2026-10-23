import type { ApiResponse, PlayerRef } from '~/types/api'

/** GET /api/players?q=curry&limit=10&all=1 — search by name. Active players only unless all=1. */
export default defineEventHandler(async (event): Promise<ApiResponse<PlayerRef[]>> => {
  const sql = useDb(event)
  const q = String(getQuery(event).q ?? '').trim().slice(0, 60)
  const limit = intParam(event, 'limit', 20, 1, 100)
  const includeRetired = getQuery(event).all === '1'

  const rows = q
    ? await sql`
        SELECT p.id, p.slug, p.full_name, p.position, p.headshot_url, p.is_active,
               t.id AS team_id, t.abbr AS team_abbr, t.name AS team_name
        FROM players p LEFT JOIN teams t ON t.id = p.team_id
        WHERE (p.full_name ILIKE ${'%' + q + '%'} OR p.full_name % ${q})
          AND (${includeRetired} OR p.is_active)
        ORDER BY p.is_active DESC,
                 (p.full_name ILIKE ${q + '%'} OR p.last_name ILIKE ${q + '%'}) DESC,
                 similarity(p.full_name, ${q}) DESC, p.full_name
        LIMIT ${limit}`
    : await sql`
        SELECT p.id, p.slug, p.full_name, p.position, p.headshot_url, p.is_active,
               t.id AS team_id, t.abbr AS team_abbr, t.name AS team_name
        FROM players p LEFT JOIN teams t ON t.id = p.team_id
        WHERE p.is_active
        ORDER BY p.last_name, p.first_name
        LIMIT ${limit}`

  cacheFor(event, q ? 300 : 3600)
  return { data: rows.map(playerRef), meta: await meta(event, ['players']) }
})
