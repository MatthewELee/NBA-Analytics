import type { ApiResponse, NewsItem } from '~/types/api'

/** GET /api/news?limit=20&player=stephen-curry&team=GSW — latest ESPN headlines. */
export default defineEventHandler(async (event): Promise<ApiResponse<NewsItem[]>> => {
  const sql = useDb(event)
  const limit = intParam(event, 'limit', 20, 1, 100)
  const { player, team } = getQuery(event)

  const rows = await sql`
    SELECT n.id, n.headline, n.description, n.url, n.image_url, n.published_at, n.byline, n.source
    FROM news n
    WHERE true
      ${typeof player === 'string' && player
        ? sql`AND EXISTS (SELECT 1 FROM players p WHERE (p.slug = ${player} OR p.id::text = ${player}) AND p.id = ANY(n.player_ids))`
        : sql``}
      ${typeof team === 'string' && team
        ? sql`AND EXISTS (SELECT 1 FROM teams t WHERE t.abbr = ${team.toUpperCase()} AND t.id = ANY(n.team_ids))`
        : sql``}
    ORDER BY n.published_at DESC
    LIMIT ${limit}`

  const data = rows.map((n): NewsItem => ({
    id: n.id,
    headline: n.headline,
    description: n.description,
    url: n.url,
    imageUrl: n.imageUrl,
    publishedAt: new Date(n.publishedAt).toISOString(),
    byline: n.byline,
    source: n.source,
  }))

  cacheFor(event, 300)
  return { data, meta: await meta(event, ['news']) }
})
