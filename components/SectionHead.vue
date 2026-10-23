<script setup lang="ts">
/** A section heading: kicker number, display title, and an optional control on the right. */
defineProps<{ title: string; kicker?: string; id?: string }>()
</script>

<template>
  <header class="sh">
    <div>
      <p v-if="kicker" class="kicker sh__kicker">{{ kicker }}</p>
      <h2 :id="id" class="display sh__title">{{ title }}</h2>
    </div>
    <div v-if="$slots.default" class="sh__aside"><slot /></div>
  </header>
</template>

<style scoped>
.sh {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: space-between;
  gap: var(--space-3) var(--space-5);
  padding-top: var(--space-3);
  margin-bottom: var(--space-4);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.sh__kicker {
  color: var(--color-spot-text);
  margin-bottom: var(--space-1);
}

.sh__aside {
  min-width: 0;
  max-width: 100%;
}

.sh__title {
  font-size: var(--text-2xl);
}
</style>
