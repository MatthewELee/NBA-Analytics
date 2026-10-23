<script setup lang="ts">
import type { ApiResponse, TeamStanding } from '~/types/api'

useHead({ title: 'Teams' })

const route = useRoute()
const season = computed(() => (typeof route.query.season === 'string' ? route.query.season : undefined))
const { data } = await useFetch<ApiResponse<TeamStanding[]>>('/api/teams', { query: { season } })

const conferences = computed(() => {
  const all = data.value?.data ?? []
  const names = [...new Set(all.map((t) => t.conference ?? 'Unassigned'))]
  return names.map((name) => ({ name, teams: all.filter((t) => (t.conference ?? 'Unassigned') === name) }))
})
const seasonLabel = computed(() => (data.value?.meta.season ?? '').replace('-', '–'))
</script>

<template>
  <article class="teams">
    <header class="intro">
      <p class="kicker spot-text">{{ seasonLabel }} standings</p>
      <h1 class="display intro__title">Teams</h1>
    </header>
    <div class="confs grid">
      <section v-for="c in conferences" :key="c.name" class="conf" :aria-labelledby="`conf-${c.name}`">
        <SectionHead :id="`conf-${c.name}`" :title="c.name" kicker="Conference" />
        <div class="standings-wrap">
        <table class="standings">
          <caption class="visually-hidden">{{ c.name }} standings</caption>
          <thead>
            <tr>
              <th scope="col" class="num">#</th>
              <th scope="col">Team</th>
              <th scope="col" class="num">W</th>
              <th scope="col" class="num">L</th>
              <th scope="col" class="num" title="Games back">GB</th>
              <th scope="col" class="num" title="Net rating">Net</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="t in c.teams" :key="t.id" :class="{ 'is-cut': t.confRank === 6 || t.confRank === 10 }">
              <td class="num rank">{{ t.confRank ?? '–' }}</td>
              <th scope="row">
                <NuxtLink :to="`/teams/${t.abbr}`" class="team-link">
                  <span class="chip" :style="t.colorPrimary ? { background: `#${t.colorPrimary}` } : undefined" aria-hidden="true" />
                  <span class="team-link__city">{{ t.city }}</span> <b>{{ t.name }}</b>
                </NuxtLink>
              </th>
              <td class="num">{{ t.wins }}</td>
              <td class="num">{{ t.losses }}</td>
              <td class="num">{{ t.gamesBack ? num(t.gamesBack) : '–' }}</td>
              <td class="num">{{ signed(t.netRating) }}</td>
            </tr>
          </tbody>
        </table>
        </div>
      </section>
    </div>
    <SourceLine v-if="data?.meta.asOf" :source="data.meta.source ?? ''" :as-of="data.meta.asOf" />
  </article>
</template>

<style scoped>
.intro {
  padding-block: var(--space-6) var(--space-7);
}

.spot-text {
  color: var(--color-spot-text);
}

.intro__title {
  font-size: var(--text-4xl);
}

.confs {
  row-gap: var(--space-7);
}

.conf {
  grid-column: span 6;
  min-width: 0;
}

.standings-wrap {
  position: relative;
  overflow-x: auto;
}

.standings {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums;
}

th,
td {
  padding: var(--space-2) var(--space-2);
  text-align: left;
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
  font-weight: 400;
}

thead th {
  font-size: var(--text-2xs);
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
  color: var(--color-ink-muted);
  border-bottom-color: var(--color-rule);
}

.num {
  text-align: right;
}

.rank {
  width: 2.5rem;
  color: var(--color-ink-muted);
}

/* Play-in and lottery lines. */
tr.is-cut td,
tr.is-cut th {
  border-bottom: var(--rule-hair) solid var(--color-rule);
}

.team-link {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-family: var(--font-body);
  font-size: var(--text-base);
  text-decoration-color: transparent;
}

.team-link:hover {
  text-decoration-color: var(--color-spot);
}

.team-link b {
  font-weight: 600;
}

.chip {
  width: 4px;
  height: 1.1em;
  background: var(--color-rule-faint);
}

@media (max-width: 960px) {
  .conf {
    grid-column: 1 / -1;
  }
}

@media (max-width: 520px) {
  .team-link__city {
    display: none;
  }
}
</style>
