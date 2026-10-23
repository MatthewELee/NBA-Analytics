<script setup lang="ts">
const props = defineProps<{
  source: string
  asOf: Date | string
}>()

const stamp = computed(() => {
  const d = typeof props.asOf === 'string' ? new Date(props.asOf) : props.asOf
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    timeZoneName: 'short',
  }).format(d)
})
</script>

<template>
  <p class="source label">
    Source: {{ source }} <span aria-hidden="true">·</span> As of
    <time :datetime="new Date(asOf).toISOString()">{{ stamp }}</time>
  </p>
</template>

<style scoped>
.source {
  padding-top: var(--space-2);
  border-top: var(--rule-hair) solid var(--color-rule-faint);
  font-size: var(--text-2xs);
}
</style>
