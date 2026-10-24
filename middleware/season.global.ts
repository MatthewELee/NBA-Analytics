/**
 * Keeps a picked season while browsing: links don't carry ?season=, so it's copied from the
 * page being left. Picking the current season in the masthead removes it.
 */
export default defineNuxtRouteMiddleware((to, from) => {
  const season = from.query.season
  if (typeof season !== 'string' || to.query.season !== undefined || to.path === from.path) return
  return navigateTo({ path: to.path, query: { ...to.query, season }, hash: to.hash }, { replace: true })
})
