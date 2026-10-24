<script setup lang="ts">
import type { RankBar } from '~/components/charts/RankBars.vue'
import type { ApiResponse, GameSummary, Story } from '~/types/api'

useHead({ title: 'Tonight' })

const season = useSeason()

const [{ data: slate }, { data: story }] = await Promise.all([
  useFetch<ApiResponse<GameSummary[]>>('/api/scoreboard', { key: 'home-scoreboard' }),
  useFetch<ApiResponse<Story | null>>('/api/story', { query: { season }, key: 'home-story' }),
])

const games = computed(() => slate.value?.data ?? [])
const live = computed(() => games.value.filter((g) => g.status === 'live').length)
const slateDate = computed(() => {
  const d = games.value[0]?.date ?? new Date().toLocaleDateString('en-CA', { timeZone: 'America/New_York' })
  const [y, m, day] = d.split('-').map(Number)
  return new Date(Date.UTC(y!, m! - 1, day!)).toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
    timeZone: 'UTC',
  })
})

function status(g: GameSummary) {
  if (g.status === 'live') return g.statusDetail ?? 'Live'
  if (g.status === 'final') return g.statusDetail ?? 'Final'
  if (g.status === 'postponed') return 'Postponed'
  return tipoffTime(g.tipoff)
}
function leads(g: GameSummary, side: 'home' | 'away') {
  const other = side === 'home' ? 'away' : 'home'
  return g.status !== 'scheduled' && (g[side].score ?? 0) > (g[other].score ?? 0)
}

const s = computed(() => story.value?.data ?? null)
const leader = computed(() => s.value?.rows[0] ?? null)
const tied = computed(() => !!leader.value && s.value?.rows[1]?.value === leader.value.value)
const bars = computed<RankBar[]>(() =>
  (s.value?.rows ?? []).map((r) => ({
    id: r.player.id,
    label: r.player.fullName,
    sublabel: r.player.teamAbbr ?? undefined,
    value: r.value,
  })),
)
</script>

<template>
  <article class="tonight">
    <!-- Scoreboard strip -->
    <section class="slate" aria-labelledby="slate-title">
      <header class="slate__head">
        <h1 id="slate-title" class="kicker slate__title">Tonight</h1>
        <p class="kicker">{{ slateDate }}</p>
        <p class="label slate__count">
          {{ games.length }} {{ games.length === 1 ? 'game' : 'games' }}<template v-if="live"> · {{ live }} live</template>
        </p>
      </header>
      <ol v-if="games.length" class="slate__games">
        <li v-for="g in games" :key="g.id" class="game" :class="`game--${g.status}`">
          <p class="game__status label">
            <b v-if="g.status === 'live'" class="game__live">Live</b>
            {{ status(g) }}
          </p>
          <p v-for="side in (['away', 'home'] as const)" :key="side" class="game__team" :class="{ 'is-ahead': leads(g, side) }">
            <span class="game__chip" :style="g[side].colorPrimary ? { background: `#${g[side].colorPrimary}` } : undefined" aria-hidden="true" />
            <NuxtLink :to="`/teams/${g[side].abbr}`" class="game__abbr">{{ g[side].abbr }}</NuxtLink>
            <span class="num game__score">{{ g[side].score ?? '' }}</span>
          </p>
        </li>
      </ol>
      <EmptyNote v-else>No games on the slate today.</EmptyNote>
      <SourceLine v-if="slate?.meta.asOf" :source="slate.meta.source ?? ''" :as-of="slate.meta.asOf" />
    </section>

    <div class="front grid">
      <!-- Stat of the day -->
      <section v-if="s && leader" class="story" aria-labelledby="story-title">
        <p class="kicker story__kicker">Stat of the day · {{ s.kicker }}</p>
        <h2 id="story-title" class="display story__title">{{ s.title }}</h2>
        <div class="story__lead">
          <BigNumber :value="leader.value" :label="s.unit" spot />
          <p class="story__who">
            <NuxtLink :to="`/players/${leader.player.slug}`" class="display story__name">{{ leader.player.fullName }}</NuxtLink>
            <span class="label">{{ leader.player.teamAbbr }} · {{ tied ? 'tied for the league lead' : 'leads the league' }}</span>
          </p>
        </div>
        <ChartsRankBars :bars="bars" :title="`${s.title}, ${(story?.meta.season ?? '').replace('-', '–')}`" :value-label="s.unit" />
        <SourceLine v-if="story?.meta.asOf" :source="story.meta.source ?? ''" :as-of="story.meta.asOf" />
      </section>
      <section v-else class="story" aria-labelledby="story-title">
        <p class="kicker story__kicker">Stat of the day</p>
        <h2 id="story-title" class="display story__title">Check back after a few games</h2>
        <EmptyNote>There isn't enough of the season played yet to rank anyone.</EmptyNote>
      </section>

      <aside class="front__rail">
        <LedgerRail heading-id="home-ledger-title" />
      </aside>
    </div>

    <LeaderBoards class="leaders" :season="season" :columns="4" heading-id="home-leaders-title" />
  </article>
</template>

<style scoped>
.tonight {
  padding-bottom: var(--space-8);
}

/* ---- Scoreboard strip ---------------------------------------------------- */

.slate {
  padding-top: var(--space-4);
}

.slate__head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--space-2) var(--space-5);
  padding-bottom: var(--space-2);
}

.slate__title {
  color: var(--color-spot-text);
}

.slate__count {
  margin-inline-start: auto;
}

.slate__games {
  position: relative;
  display: flex;
  overflow-x: auto;
  list-style: none;
  padding: 0;
  border-top: var(--rule-heavy) solid var(--color-rule);
  border-bottom: var(--rule-hair) solid var(--color-rule);
  scrollbar-width: thin;
}

.game {
  flex: 0 0 11rem;
  padding: var(--space-3) var(--space-4) var(--space-3);
  border-left: var(--rule-hair) solid var(--color-rule-faint);
}

.game:first-child {
  border-left: 0;
  padding-left: 0;
}

.game__status {
  margin-bottom: var(--space-2);
  white-space: nowrap;
}

.game__live {
  color: var(--color-spot-text);
  font-weight: 600;
  margin-right: var(--space-1);
}

.game__team {
  display: grid;
  grid-template-columns: 4px 1fr auto;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-mono);
  font-size: var(--text-base);
  color: var(--color-ink-muted);
}

.game--scheduled .game__team,
.game__team.is-ahead {
  color: var(--color-ink);
}

.game__team.is-ahead .game__score {
  font-weight: 600;
}

.game__chip {
  width: 4px;
  height: 1em;
  background: var(--color-rule);
}

.game__abbr {
  color: inherit;
  text-decoration-color: transparent;
}

.game__abbr:hover {
  text-decoration-color: var(--color-spot);
}

.game__score {
  text-align: right;
}

/* ---- Front: story and rail ------------------------------------------------ */

.front {
  margin-top: var(--space-8);
  row-gap: var(--space-8);
}

.story {
  grid-column: 1 / span 8;
  min-width: 0;
}

.story__kicker {
  color: var(--color-spot-text);
  padding-top: var(--space-3);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.story__title {
  font-size: var(--text-3xl);
  margin-block: var(--space-3) var(--space-6);
  max-width: 14ch;
}

.story__lead {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  gap: var(--space-4) var(--space-7);
  margin-bottom: var(--space-6);
}

.story__who {
  display: grid;
  gap: var(--space-2);
  padding-bottom: var(--space-3);
}

.story__name {
  font-size: var(--text-2xl);
  text-decoration-color: transparent;
}

.story__name:hover {
  text-decoration-color: var(--color-spot);
}

.front__rail {
  grid-column: 9 / -1;
  min-width: 0;
}

.leaders {
  margin-top: var(--space-8);
}

@media (max-width: 960px) {
  .story,
  .front__rail {
    grid-column: 1 / -1;
  }
}
</style>
