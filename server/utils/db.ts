import postgres from 'postgres'
import type { H3Event } from 'h3'

/*
 * Postgres access for server routes.
 *
 * On Cloudflare Workers the connection string comes from a Hyperdrive binding named
 * HYPERDRIVE, and each request opens (and closes) its own small client; Hyperdrive pools
 * the real connections. Everywhere else (local dev, Node) one client is shared and the
 * URL comes from NUXT_DATABASE_URL.
 */

type Sql = postgres.Sql<Record<string, never>>

const options: postgres.Options<Record<string, postgres.PostgresType>> = {
  // Return numerics and counts as numbers, and dates as 'YYYY-MM-DD' strings.
  types: {
    numeric: { to: 1700, from: [1700], serialize: (x: number) => String(x), parse: (x: string) => Number(x) },
    bigint: { to: 20, from: [20], serialize: (x: number) => String(x), parse: (x: string) => Number(x) },
    date: { to: 1082, from: [1082], serialize: (x: string) => x, parse: (x: string) => x },
  },
  // snake_case columns arrive as camelCase keys.
  transform: postgres.camel,
  fetch_types: false,
  onnotice: () => {},
}

let shared: Sql | null = null

interface HyperdriveBinding {
  connectionString: string
}

export function useDb(event: H3Event): Sql {
  const env = (event.context as { cloudflare?: { env?: Record<string, unknown> } }).cloudflare?.env
  const hyperdrive = env?.HYPERDRIVE as HyperdriveBinding | undefined
  if (hyperdrive?.connectionString) {
    const sql = postgres(hyperdrive.connectionString, { ...options, max: 5 }) as unknown as Sql
    event.waitUntil(sql.end())
    return sql
  }

  const url = useRuntimeConfig(event).databaseUrl
  if (!url) {
    throw createError({ statusCode: 503, statusMessage: 'Database is not configured' })
  }
  shared ??= postgres(url, { ...options, max: 10, idle_timeout: 20 }) as unknown as Sql
  return shared
}
