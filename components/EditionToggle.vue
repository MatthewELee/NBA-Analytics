<script setup lang="ts">
const { edition, toggle } = useEdition()
const next = computed(() => (edition.value === 'night' ? 'Day' : 'Night'))
</script>

<template>
  <button
    type="button"
    class="toggle kicker"
    :aria-label="`Switch to the ${next} edition`"
    @click="toggle"
  >
    <span class="toggle__dot" aria-hidden="true" />
    <ClientOnly fallback="Edition">
      {{ edition === 'night' ? 'Night' : 'Day' }} edition
    </ClientOnly>
  </button>
</template>

<style scoped>
.toggle {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: var(--rule-hair) solid var(--color-rule);
  border-radius: var(--radius);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.toggle:hover {
  background: var(--color-ink);
  color: var(--color-paper);
}

.toggle__dot {
  width: 0.7em;
  height: 0.7em;
  border-radius: 50%;
  background: var(--color-spot);
}
</style>
