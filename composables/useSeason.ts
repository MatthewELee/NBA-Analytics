/** The season picked with the masthead selector (?season=2025-26), or undefined for the current one. */
export function useSeason() {
  const route = useRoute()
  return computed(() => {
    const s = route.query.season
    return typeof s === 'string' && /^\d{4}-\d{2}$/.test(s) ? s : undefined
  })
}
