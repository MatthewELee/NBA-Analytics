/** Closes the per-request Postgres client that useDb() opens on Cloudflare. */
export default defineNitroPlugin((nitroApp) => {
  nitroApp.hooks.hook('afterResponse', (event) => {
    const db = (event.context as { db?: { end: () => Promise<void> } }).db
    if (db) event.waitUntil(db.end())
  })
})
