<script setup lang="ts">
import type { LedgerItem, LedgerKind } from '~/types/api'

/**
 * Ledger entries as a ruled list. `compact` is the rail version: headline, date and kind only.
 * The feed version adds the detail line and the source for each entry.
 */
const props = defineProps<{ items: LedgerItem[]; compact?: boolean; hidePlayer?: boolean }>()

const KIND_LABEL: Record<LedgerKind, string> = { record: 'Record', milestone: 'Milestone', award: 'Award' }

const root = ref<HTMLElement | null>(null)
useReveal(root, 30)

function sourceHost(url: string) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}
</script>

<template>
  <ol ref="root" class="ledger" :class="{ 'ledger--compact': props.compact }">
    <li v-for="item in items" :key="item.id" class="ledger__item reveal" :data-kind="item.kind">
      <p class="ledger__meta label">
        <span class="ledger__kind">{{ KIND_LABEL[item.kind] }}</span>
        <time :datetime="item.date">{{ shortDate(item.date) }}</time>
      </p>
      <p class="ledger__head">
        <NuxtLink v-if="item.player && !hidePlayer" :to="`/players/${item.player.slug}`">{{ item.headline }}</NuxtLink>
        <template v-else>{{ item.headline }}</template>
      </p>
      <template v-if="!compact">
        <p v-if="item.detail" class="ledger__detail">{{ item.detail }}</p>
        <p class="ledger__source label">
          <NuxtLink v-if="item.team" :to="`/teams/${item.team.abbr}`">{{ item.team.name }}</NuxtLink>
          <span v-if="item.team" aria-hidden="true"> · </span>
          Source:
          <a v-if="item.sourceUrl" :href="item.sourceUrl" rel="noopener" target="_blank">
            {{ item.source }}<span class="visually-hidden"> ({{ sourceHost(item.sourceUrl) }}, opens in a new tab)</span>
          </a>
          <template v-else>{{ item.source }}</template>
        </p>
      </template>
    </li>
  </ol>
</template>

<style scoped>
.ledger {
  list-style: none;
  padding: 0;
}

.ledger__item {
  display: grid;
  grid-template-columns: 9rem minmax(0, 1fr);
  grid-template-areas:
    'meta head'
    'meta detail'
    'meta source';
  column-gap: var(--space-5);
  padding-block: var(--space-4);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.ledger__meta {
  grid-area: meta;
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.ledger__kind {
  color: var(--color-ink);
}

.ledger__item[data-kind='record'] .ledger__kind {
  color: var(--color-spot-text);
}

.ledger__head {
  grid-area: head;
  font-family: var(--font-display);
  font-weight: var(--weight-display);
  font-size: var(--text-xl);
  line-height: var(--leading-tight);
  text-transform: uppercase;
}

.ledger__head a {
  text-decoration-color: transparent;
}

.ledger__head a:hover {
  text-decoration-color: var(--color-spot);
}

.ledger__detail {
  grid-area: detail;
  margin-top: var(--space-2);
  max-width: 60ch;
}

.ledger__source {
  grid-area: source;
  margin-top: var(--space-2);
}

/* Rail: kind and date on one line above the headline. */
.ledger--compact .ledger__item {
  grid-template-columns: minmax(0, 1fr);
  grid-template-areas:
    'meta'
    'head';
  padding-block: var(--space-3);
}

.ledger--compact .ledger__meta {
  flex-direction: row;
  justify-content: space-between;
  margin-bottom: var(--space-1);
}

.ledger--compact .ledger__head {
  font-family: var(--font-body);
  font-weight: 400;
  font-size: var(--text-base);
  line-height: var(--leading-snug);
  text-transform: none;
}

@media (max-width: 640px) {
  .ledger__item {
    grid-template-columns: minmax(0, 1fr);
    grid-template-areas:
      'meta'
      'head'
      'detail'
      'source';
  }

  .ledger__meta {
    flex-direction: row;
    justify-content: space-between;
    margin-bottom: var(--space-2);
  }
}
</style>
