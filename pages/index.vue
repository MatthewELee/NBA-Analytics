<script setup lang="ts">
useHead({ title: 'Tonight' })
</script>

<template>
  <section class="front grid">
    <p class="kicker front__kicker">Tonight</p>
    <h1 class="display front__head">The program<br />is at the <span class="spot">printer</span>.</h1>
    <div class="front__side">
      <p class="lede">
        Scores, league leaders, the Ledger and the stat of the day will run on this page. The house style is
        set first.
      </p>
      <p><NuxtLink to="/styleguide" class="kicker">Read the styleguide</NuxtLink></p>
    </div>
  </section>
</template>

<style scoped>
.front {
  padding-block: var(--space-7) var(--space-9);
  row-gap: var(--space-5);
  align-items: end;
}

.front__kicker {
  grid-column: 1 / -1;
  color: var(--color-spot-text);
}

.front__head {
  grid-column: 1 / span 8;
  font-size: var(--text-4xl);
}

.front__side {
  grid-column: 9 / -1;
  display: grid;
  gap: var(--space-4);
  padding-top: var(--space-3);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

@media (max-width: 960px) {
  .front__head,
  .front__side {
    grid-column: 1 / -1;
  }
}
</style>
