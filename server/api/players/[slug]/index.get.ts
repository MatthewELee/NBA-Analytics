import type { ApiResponse, PlayerDetail } from '~/types/api'

/** GET /api/players/:slug?season=2026-27 — bio, season line, accolades and recent news. */
export default defineEventHandler(async (event): Promise<ApiResponse<PlayerDetail>> => {
  const sql = useDb(event)
  const slug = getRouterParam(event, 'slug') ?? ''
  const season = seasonParam(event)

  const [p] = await sql`
    SELECT p.*, t.abbr AS team_abbr, t.name AS team_name, t.city AS team_city, t.color_primary AS team_color
    FROM players p LEFT JOIN teams t ON t.id = p.team_id
    WHERE p.slug = ${slug} OR p.id::text = ${slug}
    LIMIT 1`
  if (!p) notFound('Player')

  const [line, awards, news] = await Promise.all([
    sql`SELECT ${sql.unsafe(SEASON_LINE_COLUMNS)} FROM player_season_averages
        WHERE player_id = ${p.id} AND season = ${season} AND season_type = 'Regular Season' AND team_id = 0`,
    sql`SELECT award, season, team_label, month, week FROM awards
        WHERE player_id = ${p.id} ORDER BY season DESC, award`,
    sql`SELECT id, headline, description, url, image_url, published_at, byline, source FROM news
        WHERE ${p.id} = ANY(player_ids) ORDER BY published_at DESC LIMIT 5`,
  ])

  const data: PlayerDetail = {
    id: p.id,
    slug: p.slug,
    fullName: p.fullName,
    firstName: p.firstName,
    lastName: p.lastName,
    position: p.position,
    headshotUrl: p.headshotUrl,
    isActive: p.isActive,
    jersey: p.jersey,
    height: p.height,
    weightLb: p.weightLb,
    birthdate: p.birthdate,
    country: p.country,
    college: p.college,
    draft: p.draftYear ? { year: p.draftYear, round: p.draftRound, number: p.draftNumber } : null,
    fromYear: p.fromYear,
    toYear: p.toYear,
    team: p.teamId
      ? { id: p.teamId, abbr: p.teamAbbr, name: p.teamName, city: p.teamCity, colorPrimary: p.teamColor }
      : null,
    season: line[0] ? seasonLine(line[0]) : null,
    awards: awards.map((a) => ({ award: a.award, season: a.season, teamLabel: a.teamLabel, month: a.month, week: a.week })),
    news: news.map((n) => ({
      id: n.id,
      headline: n.headline,
      description: n.description,
      url: n.url,
      imageUrl: n.imageUrl,
      publishedAt: new Date(n.publishedAt).toISOString(),
      byline: n.byline,
      source: n.source,
    })),
  }

  cacheFor(event, 600)
  return { data, meta: await meta(event, ['player_stats', 'players'], season) }
})
