<script setup lang="ts">
import type { PlayerRef } from '~/types/api'

useHead({ title: 'Players' })

const season = useSeason()

function go(p: PlayerRef) {
  navigateTo(`/players/${p.slug}`)
}
</script>

<template>
  <article class="players">
    <header class="intro grid">
      <div class="intro__head">
        <p class="kicker spot-text">Players</p>
        <h1 class="display intro__title">Look someone up</h1>
      </div>
      <div class="intro__search">
        <PlayerPicker placeholder="Search any player" label="Search players" @select="go" />
      </div>
    </header>

    <LeaderBoards :season="season" :limit="5" />
  </article>
</template>

<style scoped>
.intro {
  padding-block: var(--space-6) var(--space-7);
  row-gap: var(--space-5);
  align-items: end;
}

.intro__head {
  grid-column: 1 / span 7;
}

.intro__search {
  grid-column: 8 / -1;
}

.spot-text {
  color: var(--color-spot-text);
}

.intro__title {
  font-size: var(--text-4xl);
}

@media (max-width: 960px) {
  .intro__head,
  .intro__search {
    grid-column: 1 / -1;
  }
}
</style>
