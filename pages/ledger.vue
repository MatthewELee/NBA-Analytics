<script setup lang="ts">
import type { ApiResponse, LedgerItem, LedgerKind, LedgerPage } from '~/types/api'

useHead({ title: 'The Ledger' })

type Filter = 'all' | LedgerKind
const FILTERS: { value: Filter; label: string }[] = [
  { value: 'all', label: 'Everything' },
  { value: 'record', label: 'Records' },
  { value: 'milestone', label: 'Milestones' },
  { value: 'award', label: 'Awards' },
]
const PAGE = 30

const route = useRoute()
const router = useRouter()
const filter = computed<Filter>({
  get: () => {
    const k = route.query.kind
    return FILTERS.some((f) => f.value === k) ? (k as Filter) : 'all'
  },
  set: (v) => router.replace({ query: { ...route.query, kind: v === 'all' ? undefined : v } }),
})

const { data } = await useFetch<ApiResponse<LedgerPage>>('/api/ledger', {
  query: { limit: PAGE, kind: computed(() => (filter.value === 'all' ? undefined : filter.value)) },
})

// Older pages, fetched with the cursor and appended. Reset when the filter changes.
const more = ref<LedgerItem[]>([])
const next = ref<string | null>(null)
const loading = ref(false)
watch(
  data,
  (d) => {
    more.value = []
    next.value = d?.data.next ?? null
  },
  { immediate: true },
)

async function loadMore() {
  if (!next.value || loading.value) return
  loading.value = true
  try {
    const res = await $fetch<ApiResponse<LedgerPage>>('/api/ledger', {
      query: { limit: PAGE, kind: filter.value === 'all' ? undefined : filter.value, before: next.value },
    })
    more.value.push(...res.data.items)
    next.value = res.data.next
  } finally {
    loading.value = false
  }
}

const items = computed(() => [...(data.value?.data.items ?? []), ...more.value])

/** Entries grouped by month, newest first. */
const months = computed(() => {
  const groups: { key: string; label: string; items: LedgerItem[] }[] = []
  for (const item of items.value) {
    const key = item.date.slice(0, 7)
    let g = groups.at(-1)
    if (!g || g.key !== key) {
      const [y, m] = key.split('-').map(Number)
      const label = new Date(Date.UTC(y!, m! - 1, 1)).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' })
      g = { key, label, items: [] }
      groups.push(g)
    }
    g.items.push(item)
  }
  return groups
})
</script>

<template>
  <article class="ledger-page">
    <header class="intro grid">
      <p class="kicker intro__kicker">Records and accolades</p>
      <h1 class="display intro__title">The<br />Ledger</h1>
      <div class="intro__side">
        <p class="lede">
          Records broken, milestones reached and awards won, entered as they happen. Milestones and records are
          worked out from the box scores each night; awards come from the league.
        </p>
        <SegmentedControl v-model="filter" :options="FILTERS" label="Show" />
      </div>
    </header>

    <div aria-live="polite">
      <section v-for="m in months" :key="m.key" class="month grid" :aria-labelledby="`m-${m.key}`">
        <h2 :id="`m-${m.key}`" class="display month__label">{{ m.label }}</h2>
        <div class="month__list">
          <LedgerList :items="m.items" />
        </div>
      </section>
      <EmptyNote v-if="!items.length" class="month__empty">Nothing in the Ledger yet for this filter.</EmptyNote>
    </div>

    <div class="foot grid">
      <div class="foot__inner">
        <button v-if="next" type="button" class="more kicker" :disabled="loading" @click="loadMore">
          {{ loading ? 'Loading…' : 'Older entries' }}
        </button>
        <SourceLine v-if="data?.meta.asOf" :source="data.meta.source ?? ''" :as-of="data.meta.asOf" />
      </div>
    </div>
  </article>
</template>

<style scoped>
.ledger-page {
  padding-bottom: var(--space-8);
}

.intro {
  padding-block: var(--space-6) var(--space-7);
  row-gap: var(--space-5);
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

.intro__side {
  grid-column: 8 / -1;
  display: grid;
  gap: var(--space-5);
  padding-top: var(--space-3);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.month {
  border-top: var(--rule-heavy) solid var(--color-rule);
  padding-top: var(--space-3);
  margin-bottom: var(--space-6);
}

.month__label {
  grid-column: 1 / span 3;
  font-size: var(--text-2xl);
  align-self: start;
  position: sticky;
  top: var(--space-4);
}

.month__list {
  grid-column: 4 / -1;
  min-width: 0;
}

.month__list :deep(.ledger__item:first-child) {
  padding-top: 0;
}

.month__empty {
  border-top: var(--rule-heavy) solid var(--color-rule);
  padding-top: var(--space-4);
}

.foot__inner {
  grid-column: 4 / -1;
  display: grid;
  gap: var(--space-5);
  justify-items: start;
}

.more {
  padding: var(--space-3) var(--space-5);
  border: var(--rule-hair) solid var(--color-rule);
  background: none;
  color: var(--color-ink);
  cursor: pointer;
}

.more:hover:not(:disabled) {
  background: var(--color-ink);
  color: var(--color-paper);
}

.more:disabled {
  cursor: progress;
}

@media (max-width: 960px) {
  .intro__title,
  .intro__side,
  .month__label,
  .month__list,
  .foot__inner {
    grid-column: 1 / -1;
  }

  .month__label {
    position: static;
    margin-bottom: var(--space-4);
  }
}
</style>
