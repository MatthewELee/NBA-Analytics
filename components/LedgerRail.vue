<script setup lang="ts">
import type { ApiResponse, LedgerPage } from '~/types/api'

/** The five newest Ledger entries, optionally for one player, with a link to the full feed. */
const props = withDefaults(defineProps<{ player?: string; limit?: number; headingId?: string }>(), {
  player: undefined,
  limit: 5,
  headingId: 'ledger-rail-title',
})

const { data } = await useFetch<ApiResponse<LedgerPage>>('/api/ledger', {
  query: { limit: props.limit, player: props.player },
  key: `ledger-rail-${props.player ?? 'all'}-${props.limit}`,
})
const items = computed(() => data.value?.data.items ?? [])
</script>

<template>
  <section class="rail" :aria-labelledby="headingId">
    <SectionHead :id="headingId" title="The Ledger" :kicker="player ? 'Records and honors' : 'Latest'" />
    <LedgerList v-if="items.length" :items="items" compact />
    <EmptyNote v-else>{{ player ? 'Nothing in the Ledger yet.' : 'The Ledger is empty for now.' }}</EmptyNote>
    <p class="rail__more">
      <NuxtLink to="/ledger" class="kicker">All entries</NuxtLink>
    </p>
    <SourceLine v-if="data?.meta.asOf" :source="data.meta.source ?? ''" :as-of="data.meta.asOf" />
  </section>
</template>

<style scoped>
.rail__more {
  padding-block: var(--space-3);
}

.rail__more a {
  text-decoration-color: var(--color-spot);
  text-decoration-thickness: 2px;
}
</style>
