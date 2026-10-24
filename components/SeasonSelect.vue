<script setup lang="ts">
import type { ApiResponse } from '~/types/api'

/** Picks the season every page shows. The current season leaves the URL clean. */
const route = useRoute()
const picked = useSeason()

const { data } = await useFetch<ApiResponse<string[]>>('/api/seasons', { key: 'seasons' })
const current = computed(() => data.value?.meta.season ?? data.value?.data[0] ?? '')
const seasons = computed(() => data.value?.data ?? [])
const value = computed(() => picked.value ?? current.value)

function label(s: string) {
  return s.replace('-', '–')
}

function pick(e: Event) {
  const s = (e.target as HTMLSelectElement).value
  navigateTo({ path: route.path, query: { ...route.query, season: s === current.value ? undefined : s }, hash: route.hash })
}
</script>

<template>
  <div v-if="seasons.length" class="season">
    <label for="season-select" class="kicker season__label">Season</label>
    <span class="season__box">
      <select id="season-select" class="season__select kicker" :value="value" @change="pick">
        <option v-for="s in seasons" :key="s" :value="s">{{ label(s) }}</option>
      </select>
    </span>
  </div>
</template>

<style scoped>
.season {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
}

.season__label {
  color: var(--color-ink-muted);
}

.season__box {
  position: relative;
  display: inline-flex;
}

/* A drawn caret: two hairlines, no icon font. */
.season__box::after {
  content: '';
  position: absolute;
  right: var(--space-2);
  top: 50%;
  width: 5px;
  height: 5px;
  border-right: var(--rule-hair) solid var(--color-ink);
  border-bottom: var(--rule-hair) solid var(--color-ink);
  transform: translateY(-75%) rotate(45deg);
  pointer-events: none;
}

.season__select {
  appearance: none;
  padding: var(--space-1) var(--space-5) var(--space-1) var(--space-2);
  border: var(--rule-hair) solid var(--color-rule);
  border-radius: var(--radius);
  background: var(--color-paper);
  color: var(--color-ink);
  cursor: pointer;
}

.season__select:hover {
  border-color: var(--color-spot);
}

@media (max-width: 640px) {
  .season__label {
    display: none;
  }
}
</style>
