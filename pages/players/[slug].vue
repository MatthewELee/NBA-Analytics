<script setup lang="ts">
import type { Column } from '~/components/StatTable.vue'
import type { Series } from '~/components/charts/LineChart.vue'
import type { ApiResponse, GameLogRow, PlayerDetail, SeasonLine } from '~/types/api'

const route = useRoute()
const slug = computed(() => String(route.params.slug))
const season = computed(() => (typeof route.query.season === 'string' ? route.query.season : undefined))

const { data: player, error } = await useFetch<ApiResponse<PlayerDetail>>(() => `/api/players/${slug.value}`, {
  query: { season },
})
if (error.value || !player.value) {
  throw createError({ statusCode: error.value?.statusCode ?? 404, statusMessage: 'Player not found', fatal: true })
}

const p = computed(() => player.value!.data)
const seasonLabel = computed(() => (player.value!.meta.season ?? '').replace('-', '–'))

const [{ data: games }, { data: career }] = await Promise.all([
  useFetch<ApiResponse<GameLogRow[]>>(() => `/api/players/${slug.value}/games`, { query: { season } }),
  useFetch<ApiResponse<SeasonLine[]>>(() => `/api/players/${slug.value}/career`),
])

useHead({ title: () => p.value.fullName })

/* ---- Header facts ---------------------------------------------------------- */

const facts = computed(() => {
  const d = p.value
  const out: { label: string; value: string }[] = [
    { label: 'Height', value: height(d.height) },
    { label: 'Weight', value: d.weightLb ? `${d.weightLb} lb` : '–' },
    { label: 'Age', value: String(ageFrom(d.birthdate) ?? d.season?.age ?? '–') },
    {
      label: 'Draft',
      value: d.draft ? `${d.draft.year} · R${d.draft.round ?? '–'} · #${d.draft.number ?? '–'}` : 'Undrafted',
    },
    { label: 'Seasons', value: d.fromYear ? `${d.fromYear}–${d.isActive ? 'now' : d.toYear}` : '–' },
  ]
  if (d.college) out.push({ label: 'College', value: d.college })
  else if (d.country) out.push({ label: 'From', value: d.country })
  return out
})

const teamColor = computed(() => (p.value.team?.colorPrimary ? `#${p.value.team.colorPrimary}` : undefined))

/* ---- Season line -------------------------------------------------------------- */

const line = computed(() => p.value.season)
const strip = computed(() => {
  const s = line.value
  if (!s) return []
  return [
    { label: 'GP', title: 'Games played', value: String(s.gp) },
    { label: 'MIN', title: 'Minutes per game', value: num(s.minPg) },
    { label: 'STL', title: 'Steals per game', value: num(s.stlPg) },
    { label: 'BLK', title: 'Blocks per game', value: num(s.blkPg) },
    { label: 'FG%', title: 'Field goal percentage', value: pct(s.fgPct) },
    { label: '3P%', title: 'Three-point percentage', value: pct(s.fg3Pct) },
    { label: 'FT%', title: 'Free throw percentage', value: pct(s.ftPct) },
    { label: 'TS%', title: 'True shooting percentage', value: pct(s.tsPct) },
    { label: 'USG%', title: 'Usage rate', value: pct(s.usgPct) },
    { label: 'NET', title: 'Net rating (points per 100 possessions)', value: signed(s.netRating) },
    { label: 'PIE', title: 'Player impact estimate', value: pct(s.pie) },
  ]
})

/* ---- Game log ----------------------------------------------------------------- */

type Range = 5 | 10 | 0
const range = ref<Range>(10)
const rangeOptions: { value: Range; label: string }[] = [
  { value: 5, label: 'Last 5' },
  { value: 10, label: 'Last 10' },
  { value: 0, label: 'Season' },
]
const logRows = computed(() => {
  const all = games.value?.data ?? []
  return range.value ? all.slice(0, range.value) : all
})
const seasonHigh = computed(() => Math.max(0, ...(games.value?.data ?? []).map((g) => g.pts ?? 0)))

const logColumns: Column[] = [
  { key: 'date', label: 'Date', sortable: true, format: (v: string) => shortDate(v) },
  { key: 'opponent', label: 'Opp', title: 'Opponent', format: (v: string, r: GameLogRow) => `${r.home ? 'vs' : '@'} ${v}` },
  { key: 'wl', label: 'W/L', title: 'Result' },
  { key: 'min', label: 'Min', title: 'Minutes', numeric: true, sortable: true, decimals: 0 },
  { key: 'pts', label: 'Pts', title: 'Points', numeric: true, sortable: true },
  { key: 'reb', label: 'Reb', title: 'Rebounds', numeric: true, sortable: true },
  { key: 'ast', label: 'Ast', title: 'Assists', numeric: true, sortable: true },
  { key: 'stl', label: 'Stl', title: 'Steals', numeric: true, sortable: true },
  { key: 'blk', label: 'Blk', title: 'Blocks', numeric: true, sortable: true },
  { key: 'fgm', label: 'FG', title: 'Field goals made–attempted', numeric: true, format: (_: number, r: GameLogRow) => `${r.fgm ?? '–'}-${r.fga ?? '–'}` },
  { key: 'fg3m', label: '3P', title: 'Threes made–attempted', numeric: true, format: (_: number, r: GameLogRow) => `${r.fg3m ?? '–'}-${r.fg3a ?? '–'}` },
  { key: 'ftm', label: 'FT', title: 'Free throws made–attempted', numeric: true, format: (_: number, r: GameLogRow) => `${r.ftm ?? '–'}-${r.fta ?? '–'}` },
  { key: 'plusMinus', label: '+/−', title: 'Plus-minus', numeric: true, sortable: true, format: (v: number) => signed(v, 0) },
]

/* ---- Career arc ----------------------------------------------------------------- */

type ArcStat = 'ptsPg' | 'rebPg' | 'astPg' | 'tsPct'
const arcStat = ref<ArcStat>('ptsPg')
const arcOptions: { value: ArcStat; label: string }[] = [
  { value: 'ptsPg', label: 'Points' },
  { value: 'rebPg', label: 'Rebounds' },
  { value: 'astPg', label: 'Assists' },
  { value: 'tsPct', label: 'TS%' },
]
const arcLabel = computed(() => ({ ptsPg: 'Points per game', rebPg: 'Rebounds per game', astPg: 'Assists per game', tsPct: 'True shooting %' })[arcStat.value])
const arcSeries = computed<Series[]>(() => {
  const points = (career.value?.data ?? [])
    .filter((s) => s[arcStat.value] !== null)
    .map((s) => ({ x: Number(s.season.slice(0, 4)), y: arcStat.value === 'tsPct' ? s.tsPct! * 100 : (s[arcStat.value] as number) }))
  return points.length ? [{ id: 'player', label: p.value.lastName, points, emphasis: true }] : []
})

/* ---- Accolades ------------------------------------------------------------------- */

const accolades = computed(() => groupAccolades(p.value.awards))
</script>

<template>
  <article class="player" :style="teamColor ? { '--team': teamColor } : undefined">
    <!-- Header -->
    <header class="hero grid">
      <div class="hero__text">
        <p class="kicker hero__kicker">
          <NuxtLink v-if="p.team" :to="`/teams/${p.team.abbr}`">{{ p.team.city }} {{ p.team.name }}</NuxtLink>
          <span v-else>Free agent</span>
          <span v-if="p.position"> · {{ p.position }}</span>
          <span v-if="p.jersey"> · #{{ p.jersey }}</span>
          <span v-if="!p.isActive"> · Retired</span>
        </p>
        <h1 class="display hero__name">
          <span class="hero__first">{{ p.firstName }}</span>
          <span class="hero__last">{{ p.lastName }}</span>
        </h1>
        <dl class="facts">
          <div v-for="f in facts" :key="f.label">
            <dt class="label">{{ f.label }}</dt>
            <dd class="mono">{{ f.value }}</dd>
          </div>
        </dl>
      </div>
      <div class="hero__photo">
        <span v-if="teamColor" class="hero__accent" aria-hidden="true" />
        <PlayerHeadshot :src="p.headshotUrl" :name="p.fullName" size="lg" />
      </div>
    </header>

    <!-- Season line -->
    <section class="season" aria-labelledby="season-title">
      <SectionHead id="season-title" :title="`${seasonLabel} season`" kicker="Per game" />
      <template v-if="line">
        <div class="season__big">
          <BigNumber :value="line.ptsPg ?? 0" :decimals="1" label="Points" spot />
          <BigNumber :value="line.rebPg ?? 0" :decimals="1" label="Rebounds" />
          <BigNumber :value="line.astPg ?? 0" :decimals="1" label="Assists" />
        </div>
        <dl class="strip num">
          <div v-for="s in strip" :key="s.label" :title="s.title">
            <dt class="label">{{ s.label }}</dt>
            <dd>{{ s.value }}</dd>
          </div>
        </dl>
      </template>
      <EmptyNote v-else>No games played this season yet.</EmptyNote>
      <SourceLine v-if="player!.meta.asOf" :source="player!.meta.source ?? ''" :as-of="player!.meta.asOf" />
    </section>

    <div class="body grid">
      <div class="body__main">
        <!-- Game log -->
        <section aria-labelledby="log-title">
          <SectionHead id="log-title" title="Game log" kicker="Box scores">
            <SegmentedControl v-model="range" :options="rangeOptions" label="Games to show" />
          </SectionHead>
          <StatTable
            v-if="logRows.length"
            :columns="logColumns"
            :rows="logRows"
            :row-key="(r) => r.gameId"
            :caption="`${p.fullName} game log`"
            :highlight="(r) => seasonHigh > 0 && r.pts === seasonHigh"
          />
          <EmptyNote v-else>No games logged this season yet.</EmptyNote>
          <SourceLine v-if="games?.meta.asOf" :source="games.meta.source ?? ''" :as-of="games.meta.asOf" />
        </section>

        <!-- Career arc -->
        <section aria-labelledby="arc-title">
          <SectionHead id="arc-title" title="Career arc" kicker="By season">
            <SegmentedControl v-model="arcStat" :options="arcOptions" label="Stat to chart" />
          </SectionHead>
          <ChartsLineChart
            v-if="arcSeries.length && arcSeries[0]!.points.length > 1"
            :series="arcSeries"
            :title="`${p.fullName}, ${arcLabel.toLowerCase()} by season`"
            x-label="Season"
            :y-label="arcLabel"
            :format-x="(x: number) => `’${String(x).slice(2)}`"
          />
          <EmptyNote v-else>Not enough seasons to chart yet.</EmptyNote>
          <SourceLine v-if="career?.meta.asOf" :source="career.meta.source ?? ''" :as-of="career.meta.asOf" />
        </section>

        <!-- Accolades -->
        <section aria-labelledby="acc-title">
          <SectionHead id="acc-title" title="Accolades" kicker="Honors" />
          <ul v-if="accolades.length" class="accolades">
            <li v-for="a in accolades" :key="a.label">
              <span class="display accolades__count num">{{ a.count }}<span class="accolades__x">×</span></span>
              <span class="accolades__label">{{ a.label }}</span>
              <span class="label accolades__seasons">{{ a.seasons.join(', ') }}</span>
            </li>
          </ul>
          <EmptyNote v-else>No major awards on record.</EmptyNote>
        </section>
      </div>

      <!-- News rail -->
      <aside class="body__rail" aria-labelledby="news-title">
        <SectionHead id="news-title" title="In the news" kicker="ESPN" />
        <ol v-if="p.news.length" class="news">
          <li v-for="n in p.news" :key="n.id">
            <a :href="n.url" rel="noopener" target="_blank" class="news__head">{{ n.headline }}</a>
            <p class="label"><time :datetime="n.publishedAt">{{ new Date(n.publishedAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) }}</time> · {{ n.source }}</p>
          </li>
        </ol>
        <EmptyNote v-else>No recent stories.</EmptyNote>
        <p class="rail__note label">The Ledger of records and milestones will run here.</p>
      </aside>
    </div>
  </article>
</template>

<style scoped>
.player {
  padding-bottom: var(--space-8);
}

/* Header */
.hero {
  padding-block: var(--space-6) var(--space-7);
  row-gap: var(--space-5);
  align-items: end;
}

.hero__text {
  grid-column: 1 / span 8;
  min-width: 0;
}

.hero__kicker {
  margin-bottom: var(--space-3);
}

.hero__kicker a {
  text-decoration-color: var(--team, var(--color-spot));
  text-decoration-thickness: 2px;
}

.hero__name {
  display: flex;
  flex-direction: column;
  overflow-wrap: anywhere;
}

.hero__first {
  font-size: var(--text-2xl);
  font-weight: var(--weight-display-light);
}

.hero__last {
  font-size: var(--text-4xl);
  line-height: 0.82;
}

.facts {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-3) var(--space-6);
  margin-top: var(--space-5);
  padding-top: var(--space-3);
  border-top: var(--rule-hair) solid var(--color-rule);
}

.facts dd {
  font-size: var(--text-sm);
}

.hero__photo {
  grid-column: 9 / -1;
  position: relative;
  padding-left: var(--space-3);
}

.hero__accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: var(--space-2);
  background: var(--team);
}

/* Season line */
.season {
  margin-bottom: var(--space-8);
}

.season__big {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-5) var(--space-8);
  margin-bottom: var(--space-5);
}

.season__big :deep(.big__value) {
  font-size: var(--text-4xl);
}

.strip {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(5.5rem, 1fr));
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.strip > div {
  padding: var(--space-2) var(--space-3) var(--space-3) 0;
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.strip dd {
  font-size: var(--text-lg);
  font-weight: 500;
}

/* Body */
.body {
  row-gap: var(--space-8);
}

.body__main {
  grid-column: 1 / span 8;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-8);
  min-width: 0;
}

.body__rail {
  grid-column: 9 / -1;
  align-self: start;
  position: sticky;
  top: var(--space-4);
}

.accolades {
  list-style: none;
  padding: 0;
}

.accolades li {
  display: grid;
  grid-template-columns: 5rem 1fr;
  grid-template-areas: 'count label' 'count seasons';
  column-gap: var(--space-4);
  padding-block: var(--space-3);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.accolades__count {
  grid-area: count;
  font-size: var(--text-2xl);
  text-align: right;
  color: var(--color-ink);
}

.accolades li:first-child .accolades__count {
  color: var(--color-spot);
}

.accolades__x {
  font-size: 0.5em;
  margin-left: 0.05em;
}

.accolades__label {
  grid-area: label;
  font-size: var(--text-lg);
  align-self: end;
}

.accolades__seasons {
  grid-area: seasons;
}

.news {
  list-style: none;
  padding: 0;
}

.news li {
  padding-block: var(--space-3);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.news__head {
  display: block;
  margin-bottom: var(--space-1);
  font-size: var(--text-base);
  line-height: var(--leading-snug);
  text-decoration-color: transparent;
}

.news__head:hover {
  text-decoration-color: var(--color-spot);
}

.rail__note {
  margin-top: var(--space-5);
}

@media (max-width: 960px) {
  .hero__text,
  .hero__photo,
  .body__main,
  .body__rail {
    grid-column: 1 / -1;
  }

  .hero__photo {
    max-width: 22rem;
  }

  .body__rail {
    position: static;
  }
}
</style>
