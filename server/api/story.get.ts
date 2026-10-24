import type { ApiResponse, Story } from '~/types/api'

/** Each candidate counts something per player from this season's box scores. */
const CANDIDATES: { id: string; kicker: string; title: string; unit: string; expr: string }[] = [
  { id: 'forty', kicker: 'Scoring', title: 'Most 40-point games', unit: '40-point games', expr: 'count(*) FILTER (WHERE g.pts >= 40)' },
  { id: 'thirty', kicker: 'Scoring', title: 'Most 30-point games', unit: '30-point games', expr: 'count(*) FILTER (WHERE g.pts >= 30)' },
  {
    id: 'triple-doubles',
    kicker: 'All-around',
    title: 'Most triple-doubles',
    unit: 'triple-doubles',
    expr: `count(*) FILTER (WHERE (g.pts >= 10)::int + (g.reb >= 10)::int + (g.ast >= 10)::int
                                 + (g.stl >= 10)::int + (g.blk >= 10)::int >= 3)`,
  },
  {
    id: 'double-doubles',
    kicker: 'All-around',
    title: 'Most double-doubles',
    unit: 'double-doubles',
    expr: `count(*) FILTER (WHERE (g.pts >= 10)::int + (g.reb >= 10)::int + (g.ast >= 10)::int
                                 + (g.stl >= 10)::int + (g.blk >= 10)::int >= 2)`,
  },
  { id: 'threes', kicker: 'Shooting', title: 'Most 3-pointers made', unit: '3-pointers', expr: 'sum(g.fg3m)' },
  { id: 'plus-minus', kicker: 'Impact', title: 'Best plus-minus', unit: 'points, plus-minus', expr: 'sum(g.plus_minus)' },
]

/**
 * GET /api/story?season=2026-27&date=2026-10-23 — the featured stat for a day.
 * Rotates through the candidates by day, skipping any with too little to show.
 */
export default defineEventHandler(async (event): Promise<ApiResponse<Story | null>> => {
  const sql = useDb(event)
  const season = seasonParam(event)
  const raw = getQuery(event).date
  const day = typeof raw === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(raw)
    ? raw
    : new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })
  const dayNumber = Math.floor(Date.parse(`${day}T00:00:00Z`) / 86_400_000)

  let story: Story | null = null
  for (let i = 0; i < CANDIDATES.length && !story; i++) {
    const c = CANDIDATES[(dayNumber + i) % CANDIDATES.length]!
    const rows = await sql`
      SELECT p.id, p.slug, p.full_name, t.abbr AS team_abbr, ${sql.unsafe(c.expr)} AS value
      FROM player_games g
      JOIN players p ON p.id = g.player_id
      LEFT JOIN teams t ON t.id = p.team_id
      WHERE g.season = ${season} AND g.season_type = 'Regular Season'
      GROUP BY p.id, p.slug, p.full_name, t.abbr
      HAVING ${sql.unsafe(c.expr)} > 0
      ORDER BY value DESC, p.full_name
      LIMIT 8`
    // A story needs a leader and a field to measure them against.
    if (rows.length >= 3) {
      story = {
        id: c.id,
        kicker: c.kicker,
        title: c.title,
        unit: c.unit,
        rows: rows.map((r) => ({
          player: { id: r.id, slug: r.slug, fullName: r.fullName, teamAbbr: r.teamAbbr },
          value: Number(r.value),
        })),
      }
    }
  }

  cacheFor(event, 1800)
  return { data: story, meta: await meta(event, ['gamelogs'], season) }
})
