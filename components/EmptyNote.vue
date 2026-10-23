<template>
  <p class="empty label"><slot /></p>
</template>

<style scoped>
.empty {
  padding: var(--space-4) 0;
  border-top: var(--rule-hair) solid var(--color-rule-faint);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}
</style>
