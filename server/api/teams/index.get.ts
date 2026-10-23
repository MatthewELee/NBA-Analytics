import type { ApiResponse, TeamStanding } from '~/types/api'

/** GET /api/teams?season=2026-27 — every team with its record, by conference and seed. */
export default defineEventHandler(async (event): Promise<ApiResponse<TeamStanding[]>> => {
  const sql = useDb(event)
  const season = seasonParam(event)

  const rows = await sql`
    SELECT t.id, t.abbr, t.city, t.name, t.color_primary, t.logo_url, t.conference, t.division,
           coalesce(s.wins, 0) AS wins, coalesce(s.losses, 0) AS losses, s.conf_rank, s.games_back,
           s.streak, s.last_ten, s.net_rating
    FROM teams t
    LEFT JOIN team_seasons s ON s.team_id = t.id AND s.season = ${season} AND s.season_type = 'Regular Season'
    ORDER BY t.conference NULLS LAST, s.conf_rank NULLS LAST, t.city`

  const data = rows.map((r): TeamStanding => ({
    id: r.id,
    abbr: r.abbr,
    city: r.city,
    name: r.name,
    colorPrimary: r.colorPrimary,
    logoUrl: r.logoUrl,
    conference: r.conference,
    division: r.division,
    wins: r.wins,
    losses: r.losses,
    confRank: r.confRank,
    gamesBack: r.gamesBack,
    streak: r.streak,
    lastTen: r.lastTen,
    netRating: r.netRating,
  }))

  cacheFor(event, 900)
  return { data, meta: await meta(event, ['standings'], season) }
})
