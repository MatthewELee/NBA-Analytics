/** Response shapes of the /api routes. Shared by server routes and pages. */

export interface ApiMeta {
  source: string | null
  /** ISO time of the ingest run the data comes from. */
  asOf: string | null
  season?: string
}

export interface ApiResponse<T> {
  data: T
  meta: ApiMeta
}

export interface TeamRef {
  id: number
  abbr: string
  city: string
  name: string
  colorPrimary: string | null
  logoUrl: string | null
}

export interface PlayerRef {
  id: number
  slug: string
  fullName: string
  position: string | null
  headshotUrl: string | null
  team: Pick<TeamRef, 'id' | 'abbr' | 'name'> | null
  isActive: boolean
}

export interface SeasonLine {
  season: string
  seasonType: string
  teamAbbr: string | null
  age: number | null
  gp: number
  minPg: number | null
  ptsPg: number | null
  rebPg: number | null
  astPg: number | null
  stlPg: number | null
  blkPg: number | null
  tovPg: number | null
  fg3mPg: number | null
  fgPct: number | null
  fg3Pct: number | null
  ftPct: number | null
  tsPct: number | null
  efgPct: number | null
  usgPct: number | null
  netRating: number | null
  pie: number | null
  totals: { pts: number | null; reb: number | null; ast: number | null; stl: number | null; blk: number | null }
}

export interface Award {
  award: string
  season: string
  teamLabel: string | null
  month: string | null
  week: string | null
}

export interface NewsItem {
  id: string
  headline: string
  description: string | null
  url: string
  imageUrl: string | null
  publishedAt: string
  byline: string | null
  source: string
}

export interface PlayerDetail extends PlayerRef {
  firstName: string
  lastName: string
  jersey: string | null
  height: string | null
  weightLb: number | null
  birthdate: string | null
  country: string | null
  college: string | null
  draft: { year: number; round: number | null; number: number | null } | null
  fromYear: number | null
  toYear: number | null
  team: (Pick<TeamRef, 'id' | 'abbr' | 'name'> & { city: string; colorPrimary: string | null }) | null
  season: SeasonLine | null
  awards: Award[]
  news: NewsItem[]
}

export interface GameLogRow {
  gameId: string
  date: string
  matchup: string
  opponent: string
  home: boolean
  wl: 'W' | 'L' | null
  min: number | null
  pts: number | null
  reb: number | null
  ast: number | null
  stl: number | null
  blk: number | null
  tov: number | null
  fgm: number | null
  fga: number | null
  fg3m: number | null
  fg3a: number | null
  ftm: number | null
  fta: number | null
  plusMinus: number | null
}

export interface TeamStanding extends TeamRef {
  conference: string | null
  division: string | null
  wins: number
  losses: number
  confRank: number | null
  gamesBack: number | null
  streak: string | null
  lastTen: string | null
  netRating: number | null
}

export interface GameSummary {
  id: string
  date: string
  tipoff: string | null
  status: 'scheduled' | 'live' | 'final' | 'postponed'
  statusDetail: string | null
  home: Pick<TeamRef, 'id' | 'abbr' | 'name' | 'colorPrimary'> & { score: number | null }
  away: Pick<TeamRef, 'id' | 'abbr' | 'name' | 'colorPrimary'> & { score: number | null }
}

export interface RosterRow {
  player: Pick<PlayerRef, 'id' | 'slug' | 'fullName' | 'position' | 'headshotUrl'> & { jersey: string | null }
  gp: number
  minPg: number | null
  ptsPg: number | null
  rebPg: number | null
  astPg: number | null
  tsPct: number | null
}

export interface TeamDetail extends TeamStanding {
  fullName: string
  colorSecondary: string | null
  homeRecord: string | null
  roadRecord: string | null
  divRank: number | null
  ptsPg: number | null
  oppPtsPg: number | null
  offRating: number | null
  defRating: number | null
  pace: number | null
  roster: RosterRow[]
  recent: GameSummary[]
  upcoming: GameSummary[]
}

export interface TeamGamePoint {
  gameId: string
  date: string
  matchup: string
  wl: 'W' | 'L' | null
  pts: number | null
  oppPts: number | null
  plusMinus: number | null
  /** Running point differential through this game. */
  cumulative: number
}

export type LeaderStat = 'pts' | 'reb' | 'ast' | 'ts'

export interface LeaderRow {
  rank: number
  player: PlayerRef
  value: number
  gp: number
}

export type LedgerKind = 'record' | 'milestone' | 'award'

export interface LedgerItem {
  id: number
  kind: LedgerKind
  headline: string
  detail: string | null
  date: string
  player: Pick<PlayerRef, 'id' | 'slug' | 'fullName'> | null
  team: Pick<TeamRef, 'abbr' | 'name'> | null
  stat: string | null
  value: number | null
  source: string
  sourceUrl: string | null
}

export interface LedgerPage {
  items: LedgerItem[]
  /** Pass as ?before= to get the next page; null on the last page. */
  next: string | null
}

export interface SearchResults {
  players: PlayerRef[]
  teams: Pick<TeamRef, 'id' | 'abbr' | 'city' | 'name' | 'colorPrimary'>[]
}

export interface StoryRow {
  player: Pick<PlayerRef, 'id' | 'slug' | 'fullName'> & { teamAbbr: string | null }
  value: number
}

/** The featured stat of the day: one stat, one number, one chart. */
export interface Story {
  id: string
  kicker: string
  title: string
  /** What the number counts, for the label under it: "40-point games". */
  unit: string
  rows: StoryRow[]
}
