<script setup lang="ts">
import type { Column } from '~/components/StatTable.vue'
import type { Series } from '~/components/charts/LineChart.vue'
import type { ApiResponse, GameSummary, RosterRow, TeamDetail, TeamGamePoint } from '~/types/api'

const route = useRoute()
const abbr = computed(() => String(route.params.abbr).toUpperCase())
const season = useSeason()

const { data: team, error } = await useFetch<ApiResponse<TeamDetail>>(() => `/api/teams/${abbr.value}`, {
  query: { season },
})
if (error.value || !team.value) {
  throw createError({ statusCode: error.value?.statusCode ?? 404, statusMessage: 'Team not found', fatal: true })
}
const { data: games } = await useFetch<ApiResponse<TeamGamePoint[]>>(() => `/api/teams/${abbr.value}/games`, {
  query: { season },
})

const t = computed(() => team.value!.data)
const seasonLabel = computed(() => (team.value!.meta.season ?? '').replace('-', '–'))
const teamColor = computed(() => (t.value.colorPrimary ? `#${t.value.colorPrimary}` : undefined))

useHead({ title: () => t.value.fullName })

/* ---- Ratings --------------------------------------------------------------- */

const ratings = computed(() => [
  { label: 'Off rating', title: 'Points scored per 100 possessions', value: num(t.value.offRating) },
  { label: 'Def rating', title: 'Points allowed per 100 possessions', value: num(t.value.defRating) },
  { label: 'Net rating', title: 'Offensive minus defensive rating', value: signed(t.value.netRating), spot: true },
  { label: 'Pace', title: 'Possessions per 48 minutes', value: num(t.value.pace) },
  { label: 'Points', title: 'Points per game', value: num(t.value.ptsPg) },
  { label: 'Allowed', title: 'Opponent points per game', value: num(t.value.oppPtsPg) },
])

const standing = computed(() => {
  const parts: string[] = []
  if (t.value.confRank) parts.push(`${ordinal(t.value.confRank)} in the ${t.value.conference ?? 'conference'}`)
  if (t.value.gamesBack) parts.push(`${num(t.value.gamesBack)} GB`)
  if (t.value.streak) parts.push(t.value.streak.replace(/\s+/, ''))
  return parts.join(' · ')
})

/* ---- Point differential chart ------------------------------------------------ */

const diffSeries = computed<Series[]>(() => {
  const pts = (games.value?.data ?? []).map((g, i) => ({ x: i + 1, y: g.cumulative }))
  return pts.length > 1 ? [{ id: 'diff', label: t.value.abbr, points: pts, emphasis: true }] : []
})

/* ---- Roster -------------------------------------------------------------------- */

type RosterTableRow = { slug: string; name: string; jersey: string; position: string } & Omit<RosterRow, 'player'>
const rosterRows = computed<RosterTableRow[]>(() =>
  t.value.roster.map((r) => ({
    slug: r.player.slug,
    name: r.player.fullName,
    jersey: r.player.jersey ?? '',
    position: r.player.position ?? '',
    gp: r.gp,
    minPg: r.minPg,
    ptsPg: r.ptsPg,
    rebPg: r.rebPg,
    astPg: r.astPg,
    tsPct: r.tsPct,
  })),
)
const rosterColumns: Column[] = [
  { key: 'jersey', label: '#', title: 'Jersey' },
  { key: 'name', label: 'Player', sortable: true },
  { key: 'position', label: 'Pos', title: 'Position' },
  { key: 'gp', label: 'GP', title: 'Games played', numeric: true, sortable: true },
  { key: 'minPg', label: 'Min', title: 'Minutes per game', numeric: true, sortable: true, decimals: 1 },
  { key: 'ptsPg', label: 'Pts', title: 'Points per game', numeric: true, sortable: true, decimals: 1 },
  { key: 'rebPg', label: 'Reb', title: 'Rebounds per game', numeric: true, sortable: true, decimals: 1 },
  { key: 'astPg', label: 'Ast', title: 'Assists per game', numeric: true, sortable: true, decimals: 1 },
  { key: 'tsPct', label: 'TS%', title: 'True shooting percentage', numeric: true, sortable: true, format: (v: number | null) => pct(v) },
]
const topScorer = computed(() => Math.max(0, ...rosterRows.value.map((r) => r.ptsPg ?? 0)))

/* ---- Results and schedule ---------------------------------------------------------- */

function opponent(g: GameSummary) {
  const home = g.home.id === t.value.id
  return { home, opp: home ? g.away : g.home, us: home ? g.home : g.away }
}
function result(g: GameSummary) {
  const { us, opp } = opponent(g)
  if (us.score === null || opp.score === null) return null
  return { won: us.score > opp.score, score: `${us.score}–${opp.score}` }
}
</script>

<template>
  <article class="team" :style="teamColor ? { '--team': teamColor } : undefined">
    <header class="hero grid">
      <div class="hero__text">
        <p class="kicker">{{ t.conference ?? '' }}<span v-if="t.division"> · {{ t.division }}</span> · {{ seasonLabel }}</p>
        <h1 class="display hero__name">
          <span class="hero__city">{{ t.city }}</span>
          <span class="hero__nick">
            <span v-if="teamColor" class="hero__accent" aria-hidden="true" />{{ t.name }}
          </span>
        </h1>
      </div>
      <div class="hero__record">
        <p class="display record num" :aria-label="`${t.wins} wins, ${t.losses} losses`">
          {{ t.wins }}<span class="record__dash">–</span>{{ t.losses }}
        </p>
        <p class="kicker record__standing">{{ standing || 'No games yet' }}</p>
      </div>
    </header>

    <section aria-labelledby="ratings-title">
      <h2 id="ratings-title" class="visually-hidden">Team ratings</h2>
      <dl class="ratings">
        <div v-for="r in ratings" :key="r.label" :title="r.title" :class="{ 'is-spot': r.spot }">
          <dt class="label">{{ r.label }}</dt>
          <dd class="display num">{{ r.value }}</dd>
        </div>
      </dl>
      <SourceLine v-if="team!.meta.asOf" :source="team!.meta.source ?? ''" :as-of="team!.meta.asOf" />
    </section>

    <div class="body grid">
      <div class="body__main">
        <section aria-labelledby="diff-title">
          <SectionHead id="diff-title" title="Point differential" kicker="Running total, game by game" />
          <ChartsLineChart
            v-if="diffSeries.length"
            :series="diffSeries"
            :title="`${t.fullName} running point differential, ${seasonLabel}`"
            x-label="Game"
            y-label="Point differential"
            :y-decimals="0"
            :format-x="(x: number) => String(x)"
          />
          <EmptyNote v-else>The chart starts after two games.</EmptyNote>
          <SourceLine v-if="games?.meta.asOf" :source="games.meta.source ?? ''" :as-of="games.meta.asOf" />
        </section>

        <section aria-labelledby="roster-title">
          <SectionHead id="roster-title" title="Roster" kicker="Per game" />
          <StatTable
            v-if="rosterRows.length"
            :columns="rosterColumns"
            :rows="rosterRows"
            :row-key="(r) => r.slug"
            :caption="`${t.fullName} roster`"
            :highlight="(r) => topScorer > 0 && r.ptsPg === topScorer"
          >
            <template #cell-name="{ row }">
              <NuxtLink :to="`/players/${row.slug}`" class="roster__link">{{ row.name }}</NuxtLink>
            </template>
          </StatTable>
          <EmptyNote v-else>No roster on file.</EmptyNote>
        </section>
      </div>

      <aside class="body__rail">
        <section aria-labelledby="recent-title">
          <SectionHead id="recent-title" title="Results" kicker="Last 10" />
          <ol v-if="t.recent.length" class="games">
            <li v-for="g in t.recent" :key="g.id">
              <span class="label">{{ shortDate(g.date) }}</span>
              <span>{{ opponent(g).home ? 'vs' : '@' }} {{ opponent(g).opp.abbr }}</span>
              <span class="num games__score" :class="{ 'is-win': result(g)?.won }">
                <b>{{ result(g)?.won ? 'W' : 'L' }}</b> {{ result(g)?.score }}
              </span>
            </li>
          </ol>
          <EmptyNote v-else>No results yet.</EmptyNote>
        </section>

        <section aria-labelledby="next-title">
          <SectionHead id="next-title" title="Schedule" kicker="Next up" />
          <ol v-if="t.upcoming.length" class="games">
            <li v-for="g in t.upcoming" :key="g.id">
              <span class="label">{{ shortDate(g.date) }}</span>
              <span>{{ opponent(g).home ? 'vs' : '@' }} {{ opponent(g).opp.abbr }}</span>
              <span class="num games__score">
                <template v-if="g.status === 'live'"><b class="games__live">Live</b> {{ g.statusDetail }}</template>
                <template v-else>{{ tipoffTime(g.tipoff) }}</template>
              </span>
            </li>
          </ol>
          <EmptyNote v-else>No games scheduled.</EmptyNote>
        </section>
      </aside>
    </div>
  </article>
</template>

<style scoped>
.team {
  padding-bottom: var(--space-8);
}

.hero {
  padding-block: var(--space-6) var(--space-6);
  row-gap: var(--space-5);
  align-items: end;
}

.hero__text {
  grid-column: 1 / span 8;
  min-width: 0;
}

.hero__name {
  display: flex;
  flex-direction: column;
  margin-top: var(--space-3);
}

.hero__city {
  font-size: var(--text-2xl);
  font-weight: var(--weight-display-light);
}

.hero__nick {
  display: flex;
  align-items: stretch;
  gap: var(--space-4);
  font-size: var(--text-4xl);
  line-height: 0.82;
  overflow-wrap: anywhere;
}

.hero__accent {
  flex: none;
  width: var(--space-3);
  background: var(--team);
}

.hero__record {
  grid-column: 9 / -1;
  text-align: right;
}

.record {
  font-size: var(--text-4xl);
  line-height: 0.8;
  white-space: nowrap;
}

.record__dash {
  color: var(--color-spot);
}

.record__standing {
  margin-top: var(--space-3);
  padding-top: var(--space-2);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.ratings {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  border-top: var(--rule-heavy) solid var(--color-rule);
  border-bottom: var(--rule-hair) solid var(--color-rule);
}

.ratings > div {
  padding: var(--space-3) var(--space-3) var(--space-4);
  border-left: var(--rule-hair) solid var(--color-rule-faint);
}

.ratings > div:first-child {
  border-left: 0;
  padding-left: 0;
}

.ratings dd {
  font-size: var(--text-2xl);
  margin-top: var(--space-1);
}

.ratings .is-spot dd {
  color: var(--color-spot);
}

.body {
  margin-top: var(--space-8);
  row-gap: var(--space-8);
}

.body__main {
  grid-column: 1 / span 8;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-8);
}

.body__rail {
  grid-column: 9 / -1;
  display: grid;
  gap: var(--space-7);
  align-content: start;
}

.roster__link {
  text-decoration-color: transparent;
}

.roster__link:hover {
  text-decoration-color: var(--color-spot);
}

.games {
  list-style: none;
  padding: 0;
}

.games li {
  display: grid;
  grid-template-columns: 4rem 1fr auto;
  align-items: baseline;
  gap: var(--space-3);
  padding-block: var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
  font-family: var(--font-mono);
  font-size: var(--text-sm);
}

.games__score {
  text-align: right;
}

.games__score b {
  display: inline-block;
  width: 1.2em;
  font-weight: 600;
}

.games__score.is-win b,
.games__live {
  color: var(--color-spot-text);
}

@media (max-width: 960px) {
  .hero__text,
  .hero__record,
  .body__main,
  .body__rail {
    grid-column: 1 / -1;
  }

  .hero__record {
    text-align: left;
  }

  .ratings {
    grid-template-columns: repeat(3, 1fr);
  }

  .ratings > div:nth-child(4) {
    border-left: 0;
    padding-left: 0;
  }
}
</style>
