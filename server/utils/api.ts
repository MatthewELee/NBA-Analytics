import type { H3Event } from 'h3'
import type { ApiMeta } from '~/types/api'

const SEASON_RE = /^\d{4}-\d{2}$/

/** NBA season label for today in Eastern time. Seasons start in October. */
export function currentSeason(now = new Date()): string {
  const et = new Date(now.toLocaleString('en-US', { timeZone: 'America/New_York' }))
  const start = et.getMonth() >= 9 ? et.getFullYear() : et.getFullYear() - 1
  return `${start}-${String(start + 1).slice(2)}`
}

export function seasonParam(event: H3Event): string {
  const raw = getQuery(event).season
  if (raw === undefined || raw === '') return currentSeason()
  if (typeof raw !== 'string' || !SEASON_RE.test(raw)) {
    throw createError({ statusCode: 400, statusMessage: 'season must look like 2026-27' })
  }
  return raw
}

export function intParam(event: H3Event, name: string, fallback: number, min: number, max: number): number {
  const raw = getQuery(event)[name]
  if (raw === undefined || raw === '') return fallback
  const n = Number(raw)
  if (!Number.isInteger(n) || n < min || n > max) {
    throw createError({ statusCode: 400, statusMessage: `${name} must be a whole number from ${min} to ${max}` })
  }
  return n
}

/** Lets the CDN cache a response for `seconds` and serve it stale while it refreshes. */
export function cacheFor(event: H3Event, seconds: number) {
  setResponseHeader(
    event,
    'Cache-Control',
    `public, max-age=${Math.min(seconds, 60)}, s-maxage=${seconds}, stale-while-revalidate=${seconds * 4}`,
  )
}

/** Source and "as of" time: the newest successful ingest run among `tasks`. */
export async function meta(event: H3Event, tasks: string[], season?: string): Promise<ApiMeta> {
  const sql = useDb(event)
  const [run] = await sql<{ source: string; finishedAt: Date }[]>`
    SELECT source, finished_at FROM ingest_runs
    WHERE ok AND task IN ${sql(tasks)}
    ORDER BY finished_at DESC LIMIT 1`
  return {
    source: run?.source ?? null,
    asOf: run ? new Date(run.finishedAt).toISOString() : null,
    ...(season ? { season } : {}),
  }
}

export function notFound(what: string): never {
  throw createError({ statusCode: 404, statusMessage: `${what} not found` })
}
