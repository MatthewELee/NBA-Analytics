<script setup lang="ts">
import type { Series } from '~/components/charts/LineChart.vue'
import type { TapeGroup } from '~/components/TaleOfTape.vue'
import type { ApiResponse, PlayerDetail, PlayerRef, SeasonLine } from '~/types/api'

useHead({ title: 'Compare' })

const MAX = 3
const route = useRoute()
const router = useRouter()

/* ---- URL state: ?p=slug-a,slug-b&stat=ptsPg ------------------------------------ */

const slugs = computed<string[]>(() =>
  String(route.query.p ?? '')
    .split(',')
    .map((s) => s.trim())
    .filter(Boolean)
    .slice(0, MAX),
)

type ChartStat = 'ptsPg' | 'rebPg' | 'astPg' | 'tsPct' | 'minPg'
const STATS: { value: ChartStat; label: string; long: string }[] = [
  { value: 'ptsPg', label: 'Points', long: 'Points per game' },
  { value: 'rebPg', label: 'Rebounds', long: 'Rebounds per game' },
  { value: 'astPg', label: 'Assists', long: 'Assists per game' },
  { value: 'tsPct', label: 'TS%', long: 'True shooting %' },
  { value: 'minPg', label: 'Minutes', long: 'Minutes per game' },
]
const stat = computed<ChartStat>({
  get: () => (STATS.some((s) => s.value === route.query.stat) ? (route.query.stat as ChartStat) : 'ptsPg'),
  set: (v) => setQuery({ stat: v === 'ptsPg' ? undefined : v }),
})

function setQuery(patch: Record<string, string | undefined>) {
  const query = { ...route.query, ...patch }
  for (const k of Object.keys(query)) if (query[k] === undefined || query[k] === '') delete query[k]
  router.replace({ query })
}

function add(p: PlayerRef) {
  if (slugs.value.length >= MAX || slugs.value.includes(p.slug)) return
  setQuery({ p: [...slugs.value, p.slug].join(',') })
}
function remove(slug: string) {
  setQuery({ p: slugs.value.filter((s) => s !== slug).join(',') || undefined })
}

/* ---- Data ----------------------------------------------------------------------- */

interface Loaded {
  detail: PlayerDetail
  career: SeasonLine[]
  asOf: string | null
  source: string | null
}

const season = useSeason()
const { data: players, status } = await useAsyncData(
  () => `compare:${slugs.value.join(',')}:${season.value ?? ''}`,
  async () => {
    const out: Loaded[] = []
    for (const slug of slugs.value) {
      try {
        const [d, c] = await Promise.all([
          $fetch<ApiResponse<PlayerDetail>>(`/api/players/${slug}`, { query: { season: season.value } }),
          $fetch<ApiResponse<SeasonLine[]>>(`/api/players/${slug}/career`),
        ])
        out.push({ detail: d.data, career: c.data, asOf: d.meta.asOf, source: d.meta.source })
      } catch {
        // Unknown slug in a shared link: skip it rather than failing the page.
      }
    }
    return out
  },
  { watch: [slugs, season], default: () => [] as Loaded[] },
)

const list = computed(() => players.value ?? [])
const names = computed(() => list.value.map((p) => p.detail.lastName))
const seasonLabel = computed(() => list.value[0]?.detail.season?.season.replace('-', '–') ?? 'This season')

/* ---- Tale of the tape ----------------------------------------------------------- */

function careerTotal(c: SeasonLine[], key: 'pts' | 'reb' | 'ast') {
  return c.reduce((sum, s) => sum + (s.totals[key] ?? 0), 0)
}

const groups = computed<TapeGroup[]>(() => {
  const s = list.value.map((p) => p.detail.season)
  const one = (v: number | null) => num(v)
  const per = (v: number | null) => pct(v)
  const whole = (v: number | null) => (v === null ? '–' : v.toLocaleString('en-US'))
  return [
    {
      title: `${seasonLabel.value} per game`,
      rows: [
        { label: 'Pts', title: 'Points', values: s.map((x) => x?.ptsPg ?? null), format: one },
        { label: 'Reb', title: 'Rebounds', values: s.map((x) => x?.rebPg ?? null), format: one },
        { label: 'Ast', title: 'Assists', values: s.map((x) => x?.astPg ?? null), format: one },
        { label: 'Stl', title: 'Steals', values: s.map((x) => x?.stlPg ?? null), format: one },
        { label: 'Blk', title: 'Blocks', values: s.map((x) => x?.blkPg ?? null), format: one },
        { label: 'Min', title: 'Minutes', values: s.map((x) => x?.minPg ?? null), format: one },
      ],
    },
    {
      title: 'Shooting and impact',
      rows: [
        { label: 'TS%', title: 'True shooting percentage', values: s.map((x) => x?.tsPct ?? null), format: per },
        { label: 'FG%', title: 'Field goal percentage', values: s.map((x) => x?.fgPct ?? null), format: per },
        { label: '3P%', title: 'Three-point percentage', values: s.map((x) => x?.fg3Pct ?? null), format: per },
        { label: 'USG%', title: 'Usage rate', values: s.map((x) => x?.usgPct ?? null), format: per },
        { label: 'Net', title: 'Net rating', values: s.map((x) => x?.netRating ?? null), format: (v) => signed(v) },
      ],
    },
    {
      title: 'Career',
      rows: [
        { label: 'Seasons', values: list.value.map((p) => p.career.length), format: whole },
        { label: 'Points', values: list.value.map((p) => careerTotal(p.career, 'pts')), format: whole },
        { label: 'Rebounds', values: list.value.map((p) => careerTotal(p.career, 'reb')), format: whole },
        { label: 'Assists', values: list.value.map((p) => careerTotal(p.career, 'ast')), format: whole },
      ],
    },
    {
      title: 'Accolades',
      rows: [
        { label: 'MVP', values: list.value.map((p) => countAward(p.detail.awards, 'NBA Most Valuable Player')), format: whole },
        { label: 'All-NBA', values: list.value.map((p) => countAward(p.detail.awards, 'All-NBA')), format: whole },
        { label: 'All-Star', values: list.value.map((p) => countAward(p.detail.awards, 'NBA All-Star')), format: whole },
      ],
    },
  ]
})

/* ---- Overlay chart ------------------------------------------------------------------ */

const chartStat = computed(() => STATS.find((s) => s.value === stat.value)!)
const series = computed<Series[]>(() =>
  list.value
    .map((p, i) => ({
      id: p.detail.slug,
      label: p.detail.lastName,
      emphasis: i === 0,
      points: p.career
        .filter((c) => c[stat.value] !== null)
        .map((c) => ({ x: Number(c.season.slice(0, 4)), y: stat.value === 'tsPct' ? c.tsPct! * 100 : (c[stat.value] as number) })),
    }))
    .filter((s) => s.points.length > 0),
)
const asOf = computed(() => list.value.map((p) => p.asOf).filter(Boolean).sort()[0] ?? null)
const source = computed(() => list.value[0]?.source ?? '')
</script>

<template>
  <article class="compare">
    <header class="intro grid">
      <p class="kicker intro__kicker">Compare</p>
      <h1 class="display intro__title">Tale of<br />the <span class="spot">tape</span></h1>
      <p class="lede intro__lede">
        Up to three players, side by side. The leader in each row is marked in orange. Share the page address to share
        the comparison.
      </p>
    </header>

    <section class="lineup" aria-label="Players being compared">
      <ol class="lineup__list" :style="{ '--n': Math.max(list.length + (list.length < MAX ? 1 : 0), 1) }">
        <li v-for="(p, i) in list" :key="p.detail.slug" class="lineup__card">
          <PlayerHeadshot :src="p.detail.headshotUrl" :name="p.detail.fullName" size="lg" />
          <p class="kicker lineup__meta">
            <span v-if="i === 0" class="spot">●</span>
            {{ p.detail.team?.abbr ?? 'FA' }}<span v-if="p.detail.position"> · {{ p.detail.position }}</span>
          </p>
          <h2 class="display lineup__name">
            <NuxtLink :to="`/players/${p.detail.slug}`">{{ p.detail.fullName }}</NuxtLink>
          </h2>
          <button type="button" class="lineup__remove label" :aria-label="`Remove ${p.detail.fullName}`" @click="remove(p.detail.slug)">
            Remove
          </button>
        </li>
        <li v-if="list.length < MAX" class="lineup__add">
          <PlayerPicker :exclude="list.map((p) => p.detail.id)" :placeholder="list.length ? 'Add another' : 'Add a player'" />
          <p class="label">Type two letters or more. Arrow keys and Enter pick a name.</p>
        </li>
      </ol>
    </section>

    <p v-if="status === 'pending' && !list.length" class="label">Loading…</p>

    <template v-if="list.length">
      <section class="block" aria-labelledby="tape-title">
        <SectionHead id="tape-title" title="Tale of the tape" kicker="Head to head" />
        <TaleOfTape :groups="groups" :names="names" />
        <SourceLine v-if="asOf" :source="source" :as-of="asOf" />
      </section>

      <section class="block" aria-labelledby="overlay-title">
        <SectionHead id="overlay-title" title="Season by season" kicker="Career overlay">
          <SegmentedControl v-model="stat" :options="STATS.map(({ value, label }) => ({ value, label }))" label="Stat to chart" />
        </SectionHead>
        <ChartsLineChart
          v-if="series.some((s) => s.points.length > 1)"
          :series="series"
          :title="`${chartStat.long} by season: ${names.join(', ')}`"
          x-label="Season"
          :y-label="chartStat.long"
          :format-x="(x: number) => `’${String(x).slice(2)}`"
        />
        <EmptyNote v-else>Not enough seasons to chart yet.</EmptyNote>
        <SourceLine v-if="asOf" :source="source" :as-of="asOf" />
      </section>
    </template>
    <EmptyNote v-else-if="status !== 'pending'">Pick a player above to start a comparison.</EmptyNote>
  </article>
</template>

<style scoped>
.compare {
  padding-bottom: var(--space-8);
}

.intro {
  padding-block: var(--space-6) var(--space-7);
  row-gap: var(--space-4);
  align-items: end;
}

.intro__kicker {
  grid-column: 1 / -1;
  color: var(--color-spot-text);
}

.intro__title {
  grid-column: 1 / span 7;
  font-size: var(--text-4xl);
}

.intro__lede {
  grid-column: 8 / -1;
  padding-top: var(--space-3);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.lineup__list {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(var(--n), minmax(0, 1fr));
  gap: var(--grid-gutter);
  border-top: var(--rule-double) double var(--color-rule);
  padding-top: var(--space-5);
}

.lineup__card {
  display: grid;
  gap: var(--space-2);
  align-content: start;
}

.lineup__meta {
  margin-top: var(--space-2);
}

.lineup__name {
  font-size: var(--text-2xl);
}

.lineup__name a {
  text-decoration-color: transparent;
}

.lineup__name a:hover {
  text-decoration-color: var(--color-spot);
}

.lineup__remove {
  justify-self: start;
  padding: 0;
  background: none;
  border: 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 0.25em;
}

.lineup__remove:hover {
  color: var(--color-ink);
  text-decoration-color: var(--color-spot);
}

.lineup__add {
  display: grid;
  gap: var(--space-2);
  align-content: start;
}

.block {
  margin-top: var(--space-8);
}

@media (max-width: 960px) {
  .intro__title,
  .intro__lede {
    grid-column: 1 / -1;
  }
}

@media (max-width: 640px) {
  .lineup__list {
    grid-template-columns: 1fr;
  }

  .lineup__card :deep(.shot) {
    max-width: 12rem;
  }
}
</style>
