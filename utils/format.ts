/* Number formatting for stats. Everything returns a string; missing values become an en dash. */

const DASH = '–'
const MINUS = '−'

export function num(v: number | null | undefined, decimals = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return DASH
  return v.toFixed(decimals).replace('-', MINUS)
}

/** 0.612 -> '61.2' (show the % in the column header). */
export function pct(v: number | null | undefined, decimals = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return DASH
  return (v * 100).toFixed(decimals)
}

/** Shooting split as the box score prints it: 0.612 -> '.612'. */
export function rate(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return DASH
  return v >= 1 ? v.toFixed(3) : v.toFixed(3).replace(/^0/, '')
}

export function signed(v: number | null | undefined, decimals = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return DASH
  if (v === 0) return (0).toFixed(decimals)
  return (v > 0 ? '+' : MINUS) + Math.abs(v).toFixed(decimals)
}

export function ordinal(n: number | null | undefined): string {
  if (!n) return DASH
  const s = ['th', 'st', 'nd', 'rd']
  const v = n % 100
  return n + (s[(v - 20) % 10] ?? s[v] ?? s[0]!)
}

/** '2026-10-21' -> 'Oct 21'. Dates are calendar days, so no time zone shift. */
export function shortDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(Date.UTC(y!, m! - 1, d!)).toLocaleDateString('en-US', { month: 'short', day: 'numeric', timeZone: 'UTC' })
}

export function tipoffTime(iso: string | null): string {
  if (!iso) return 'TBD'
  return new Date(iso).toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', timeZone: 'America/New_York' }) + ' ET'
}

/** Age in whole years from a birthdate. */
export function ageFrom(birthdate: string | null): number | null {
  if (!birthdate) return null
  const b = new Date(birthdate)
  const now = new Date()
  let age = now.getFullYear() - b.getFullYear()
  if (now < new Date(now.getFullYear(), b.getMonth(), b.getDate())) age--
  return age
}

/** '6-4' -> '6′4″' */
export function height(h: string | null): string {
  if (!h) return DASH
  const [ft, inch] = h.split('-')
  return inch !== undefined ? `${ft}′${inch}″` : h
}
