import type { Award } from '~/types/api'

export interface AccoladeGroup {
  label: string
  count: number
  seasons: string[]
}

// Most prestigious first. Anything not listed sorts after, alphabetically.
const ORDER = [
  'NBA Most Valuable Player',
  'NBA Finals Most Valuable Player',
  'NBA Champion',
  'NBA Defensive Player of the Year',
  'NBA Rookie of the Year',
  'NBA Sixth Man of the Year',
  'NBA Most Improved Player',
  'NBA Clutch Player of the Year',
  'All-NBA',
  'All-Defensive Team',
  'All-Rookie Team',
  'NBA All-Star',
  'NBA All-Star Most Valuable Player',
  'NBA Player of the Month',
  'NBA Player of the Week',
]

const SHORT: Record<string, string> = {
  'NBA Most Valuable Player': 'MVP',
  'NBA Finals Most Valuable Player': 'Finals MVP',
  'NBA Champion': 'Champion',
  'NBA Defensive Player of the Year': 'Defensive Player of the Year',
  'NBA Rookie of the Year': 'Rookie of the Year',
  'NBA Sixth Man of the Year': 'Sixth Man of the Year',
  'NBA Most Improved Player': 'Most Improved Player',
  'NBA Clutch Player of the Year': 'Clutch Player of the Year',
  'NBA All-Star': 'All-Star',
  'NBA All-Star Most Valuable Player': 'All-Star Game MVP',
  'NBA Player of the Month': 'Player of the Month',
  'NBA Player of the Week': 'Player of the Week',
}

function label(a: Award): string {
  const base = SHORT[a.award] ?? a.award
  if (a.teamLabel && /^\d$/.test(a.teamLabel)) {
    const n = Number(a.teamLabel)
    return `${base} ${['1st', '2nd', '3rd'][n - 1] ?? `${n}th`} Team`
  }
  return base
}

/** Collapses award rows into "All-Star ×7" style groups, most prestigious first. */
export function groupAccolades(awards: Award[]): AccoladeGroup[] {
  const groups = new Map<string, { group: AccoladeGroup; rank: number }>()
  for (const a of awards) {
    const key = label(a)
    let g = groups.get(key)
    if (!g) {
      const i = ORDER.indexOf(a.award)
      g = { group: { label: key, count: 0, seasons: [] }, rank: (i === -1 ? 100 : i) * 10 + Number(a.teamLabel ?? 0) }
      groups.set(key, g)
    }
    g.group.count++
    if (!g.group.seasons.includes(a.season)) g.group.seasons.push(a.season)
  }
  return [...groups.values()]
    .sort((x, y) => x.rank - y.rank || x.group.label.localeCompare(y.group.label))
    .map((g) => ({ ...g.group, seasons: g.group.seasons.sort() }))
}

/** Count of one award (e.g. 'NBA All-Star'), for Compare. */
export function countAward(awards: Award[], award: string, teamLabel?: string): number {
  return awards.filter((a) => a.award === award && (teamLabel === undefined || a.teamLabel === teamLabel)).length
}
