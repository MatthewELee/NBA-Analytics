<script setup lang="ts">
import type { ApiResponse, LeaderRow, LeaderStat } from '~/types/api'

/** League leaders as ranked lists: points, rebounds, assists and true shooting. */
const props = withDefaults(defineProps<{ limit?: number; season?: string; columns?: 2 | 4; headingId?: string }>(), {
  limit: 5,
  season: undefined,
  columns: 2,
  headingId: 'leaders-title',
})

const boards: { stat: LeaderStat; title: string; format: (v: number) => string }[] = [
  { stat: 'pts', title: 'Points', format: (v) => num(v) },
  { stat: 'reb', title: 'Rebounds', format: (v) => num(v) },
  { stat: 'ast', title: 'Assists', format: (v) => num(v) },
  { stat: 'ts', title: 'True shooting %', format: (v) => pct(v) },
]

const { data } = await useAsyncData(
  () => `leaders-${props.season ?? 'current'}-${props.limit}`,
  () =>
    Promise.all(
      boards.map((b) =>
        $fetch<ApiResponse<LeaderRow[]>>('/api/leaders', { query: { stat: b.stat, limit: props.limit, season: props.season } }),
      ),
    ),
  { watch: [() => props.season] },
)
const meta = computed(() => data.value?.[0]?.meta)

const root = ref<HTMLElement | null>(null)
useReveal(root, 30)
</script>

<template>
  <section ref="root" :aria-labelledby="headingId">
    <SectionHead :id="headingId" title="League leaders" :kicker="(meta?.season ?? '').replace('-', '–') + ' per game'" />
    <div class="boards grid" :class="`boards--${columns}`">
      <section v-for="(b, i) in boards" :key="b.stat" class="board" :aria-label="`${b.title} leaders`">
        <h3 class="kicker board__title">{{ b.title }}</h3>
        <ol v-if="data?.[i]?.data.length" class="board__list">
          <li v-for="r in data[i]!.data" :key="r.player.id" class="reveal">
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
</template>

<style scoped>
.boards {
  row-gap: var(--space-6);
  margin-bottom: var(--space-4);
}

.board {
  grid-column: span 6;
  min-width: 0;
}

.boards--4 .board {
  grid-column: span 3;
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
  grid-template-columns: 1.5rem minmax(0, 1fr) auto 3.5rem;
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

.boards--4 .board__name {
  font-size: var(--text-base);
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

@media (max-width: 1200px) {
  .boards--4 .board {
    grid-column: span 6;
  }
}

@media (max-width: 960px) {
  .board,
  .boards--4 .board {
    grid-column: 1 / -1;
  }
}
</style>
