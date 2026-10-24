import type { ApiResponse, LedgerItem, LedgerKind, LedgerPage } from '~/types/api'

const KINDS: LedgerKind[] = ['record', 'milestone', 'award']

/**
 * GET /api/ledger?kind=record&player=slug&team=GSW&limit=20&before=<cursor>
 * Newest first. `before` is the `next` value of the previous page.
 */
export default defineEventHandler(async (event): Promise<ApiResponse<LedgerPage>> => {
  const sql = useDb(event)
  const q = getQuery(event)
  const limit = intParam(event, 'limit', 20, 1, 100)
  const kind = typeof q.kind === 'string' && q.kind ? q.kind : null
  if (kind && !KINDS.includes(kind as LedgerKind)) {
    throw createError({ statusCode: 400, statusMessage: `kind must be one of ${KINDS.join(', ')}` })
  }
  let cursor: { date: string; id: number } | null = null
  if (typeof q.before === 'string' && q.before) {
    const m = /^(\d{4}-\d{2}-\d{2})\.(\d+)$/.exec(q.before)
    if (!m) throw createError({ statusCode: 400, statusMessage: 'before is not a valid cursor' })
    cursor = { date: m[1]!, id: Number(m[2]) }
  }
  const player = typeof q.player === 'string' && q.player ? q.player : null
  const team = typeof q.team === 'string' && q.team ? q.team.toUpperCase() : null

  const rows = await sql`
    SELECT l.id, l.kind, l.headline, l.detail, l.occurred_on, l.stat, l.value, l.source, l.source_url,
           p.id AS player_id, p.slug, p.full_name, t.abbr AS team_abbr, t.name AS team_name
    FROM ledger_items l
    LEFT JOIN players p ON p.id = l.player_id
    LEFT JOIN teams t ON t.id = l.team_id
    WHERE true
      ${kind ? sql`AND l.kind = ${kind}` : sql``}
      ${player ? sql`AND (p.slug = ${player} OR p.id::text = ${player})` : sql``}
      ${team ? sql`AND t.abbr = ${team}` : sql``}
      ${cursor ? sql`AND (l.occurred_on, l.id) < (${cursor.date}::date, ${cursor.id})` : sql``}
    ORDER BY l.occurred_on DESC, l.id DESC
    LIMIT ${limit + 1}`

  const items = rows.slice(0, limit).map(
    (r): LedgerItem => ({
      id: r.id,
      kind: r.kind,
      headline: r.headline,
      detail: r.detail,
      date: r.occurredOn,
      player: r.playerId ? { id: r.playerId, slug: r.slug, fullName: r.fullName } : null,
      team: r.teamAbbr ? { abbr: r.teamAbbr, name: r.teamName } : null,
      stat: r.stat,
      value: r.value,
      source: r.source,
      sourceUrl: r.sourceUrl,
    }),
  )
  const last = items.at(-1)
  const next = rows.length > limit && last ? `${last.date}.${last.id}` : null

  cacheFor(event, 600)
  return { data: { items, next }, meta: await meta(event, ['ledger']) }
})
