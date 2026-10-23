<script setup lang="ts">
import type { ApiResponse, LeaderRow, LeaderStat, PlayerRef } from '~/types/api'

useHead({ title: 'Players' })

const boards: { stat: LeaderStat; title: string; format: (v: number) => string }[] = [
  { stat: 'pts', title: 'Points', format: (v) => num(v) },
  { stat: 'reb', title: 'Rebounds', format: (v) => num(v) },
  { stat: 'ast', title: 'Assists', format: (v) => num(v) },
  { stat: 'ts', title: 'True shooting %', format: (v) => pct(v) },
]

const { data } = await useAsyncData('leaders', () =>
  Promise.all(boards.map((b) => $fetch<ApiResponse<LeaderRow[]>>('/api/leaders', { query: { stat: b.stat, limit: 5 } }))),
)
const meta = computed(() => data.value?.[0]?.meta)

function go(p: PlayerRef) {
  navigateTo(`/players/${p.slug}`)
}
</script>

<template>
  <article class="players">
    <header class="intro grid">
      <div class="intro__head">
        <p class="kicker spot-text">Players</p>
        <h1 class="display intro__title">Look someone up</h1>
      </div>
      <div class="intro__search">
        <PlayerPicker placeholder="Search any player" label="Search players" @select="go" />
      </div>
    </header>

    <section aria-labelledby="leaders-title">
      <SectionHead id="leaders-title" :title="`League leaders`" :kicker="(meta?.season ?? '').replace('-', '–')" />
      <div class="boards grid">
        <section v-for="(b, i) in boards" :key="b.stat" class="board" :aria-label="`${b.title} leaders`">
          <h3 class="kicker board__title">{{ b.title }}</h3>
          <ol v-if="data?.[i]?.data.length" class="board__list">
            <li v-for="r in data[i]!.data" :key="r.player.id">
              <span class="num board__rank">{{ r.rank }}</span>
              <NuxtLink :to="`/players/${r.player.slug}`" class="board__name">{{ r.player.fullName }}</NuxtLink>
              <span class="label board__team">{{ r.player.team?.abbr }}</span>
              <span class="num board__value">{{ b.format(r.value) }}</span>
            </li>
          </ol>
          <EmptyNote v-else>No qualified players yet.</EmptyNote>
        </section>
      </div>
      <SourceLine v-if="meta?.asOf" :source="meta.source ?? ''" :as-of="meta.asOf" />
    </section>
  </article>
</template>

<style scoped>
.intro {
  padding-block: var(--space-6) var(--space-7);
  row-gap: var(--space-5);
  align-items: end;
}

.intro__head {
  grid-column: 1 / span 7;
}

.intro__search {
  grid-column: 8 / -1;
}

.spot-text {
  color: var(--color-spot-text);
}

.intro__title {
  font-size: var(--text-4xl);
}

.boards {
  row-gap: var(--space-6);
}

.board {
  grid-column: span 6;
  min-width: 0;
}

.board__title {
  padding-bottom: var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule);
}

.board__list {
  list-style: none;
  padding: 0;
}

.board__list li {
  display: grid;
  grid-template-columns: 2rem 1fr auto 4.5rem;
  align-items: baseline;
  gap: var(--space-3);
  padding-block: var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.board__rank {
  color: var(--color-ink-muted);
  text-align: right;
}

.board__name {
  font-size: var(--text-lg);
  text-decoration-color: transparent;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.board__name:hover {
  text-decoration-color: var(--color-spot);
}

.board__value {
  text-align: right;
  font-size: var(--text-lg);
}

.board__list li:first-child .board__value,
.board__list li:first-child .board__name {
  color: var(--color-spot-text);
}

.board__list li:first-child .board__value {
  font-weight: 600;
}

@media (max-width: 960px) {
  .intro__head,
  .intro__search,
  .board {
    grid-column: 1 / -1;
  }
}
</style>
