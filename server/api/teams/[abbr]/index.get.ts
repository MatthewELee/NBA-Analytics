import type { ApiResponse, RosterRow, TeamDetail } from '~/types/api'

/** GET /api/teams/:abbr?season=2026-27 — record, ratings, roster, recent results and schedule. */
export default defineEventHandler(async (event): Promise<ApiResponse<TeamDetail>> => {
  const sql = useDb(event)
  const abbr = (getRouterParam(event, 'abbr') ?? '').toUpperCase()
  const season = seasonParam(event)

  const [t] = await sql`
    SELECT t.*, s.wins, s.losses, s.conf_rank, s.div_rank, s.games_back, s.streak, s.last_ten,
           s.home_record, s.road_record, s.pts_pg, s.opp_pts_pg, s.off_rating, s.def_rating,
           s.net_rating, s.pace
    FROM teams t
    LEFT JOIN team_seasons s ON s.team_id = t.id AND s.season = ${season} AND s.season_type = 'Regular Season'
    WHERE t.abbr = ${abbr}`
  if (!t) notFound('Team')

  const [roster, recent, upcoming] = await Promise.all([
    sql`
      SELECT p.id, p.slug, p.full_name, p.position, p.headshot_url, p.jersey,
             coalesce(a.gp, 0) AS gp, a.min_pg, a.pts_pg, a.reb_pg, a.ast_pg, a.ts_pct
      FROM players p
      LEFT JOIN player_season_averages a
        ON a.player_id = p.id AND a.season = ${season} AND a.season_type = 'Regular Season' AND a.team_id = 0
      WHERE p.team_id = ${t.id} AND p.is_active
      ORDER BY a.min_pg DESC NULLS LAST, p.last_name`,
    sql`
      SELECT ${sql.unsafe(GAME_COLUMNS)}
      FROM games g JOIN teams h ON h.id = g.home_team_id JOIN teams a ON a.id = g.away_team_id
      WHERE ${t.id} IN (g.home_team_id, g.away_team_id) AND g.status = 'final' AND g.season = ${season}
      ORDER BY g.game_date DESC LIMIT 10`,
    sql`
      SELECT ${sql.unsafe(GAME_COLUMNS)}
      FROM games g JOIN teams h ON h.id = g.home_team_id JOIN teams a ON a.id = g.away_team_id
      WHERE ${t.id} IN (g.home_team_id, g.away_team_id) AND g.status IN ('scheduled', 'live')
        AND g.game_date >= (now() AT TIME ZONE 'America/New_York')::date - 1
      ORDER BY g.game_date, g.tipoff LIMIT 10`,
  ])

  const data: TeamDetail = {
    id: t.id,
    abbr: t.abbr,
    city: t.city,
    name: t.name,
    fullName: t.fullName,
    colorPrimary: t.colorPrimary,
    colorSecondary: t.colorSecondary,
    logoUrl: t.logoUrl,
    conference: t.conference,
    division: t.division,
    wins: t.wins ?? 0,
    losses: t.losses ?? 0,
    confRank: t.confRank,
    divRank: t.divRank,
    gamesBack: t.gamesBack,
    streak: t.streak,
    lastTen: t.lastTen,
    homeRecord: t.homeRecord,
    roadRecord: t.roadRecord,
    ptsPg: t.ptsPg,
    oppPtsPg: t.oppPtsPg,
    offRating: t.offRating,
    defRating: t.defRating,
    netRating: t.netRating,
    pace: t.pace,
    roster: roster.map((r): RosterRow => ({
      player: { id: r.id, slug: r.slug, fullName: r.fullName, position: r.position, headshotUrl: r.headshotUrl, jersey: r.jersey },
      gp: r.gp,
      minPg: r.minPg,
      ptsPg: r.ptsPg,
      rebPg: r.rebPg,
      astPg: r.astPg,
      tsPct: r.tsPct,
    })),
    recent: recent.map(gameSummary),
    upcoming: upcoming.map(gameSummary),
  }

  cacheFor(event, 600)
  return { data, meta: await meta(event, ['standings', 'gamelogs', 'schedule', 'scoreboard'], season) }
})
