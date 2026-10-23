<script setup lang="ts">
const sections = [
  { to: '/players', label: 'Players' },
  { to: '/teams', label: 'Teams' },
  { to: '/compare', label: 'Compare' },
  { to: '/ledger', label: 'The Ledger' },
  { to: '/styleguide', label: 'Styleguide' },
]

const today = useState("bk-today", () => new Intl.DateTimeFormat('en-US', {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
  year: 'numeric',
}).format(new Date()))
</script>

<template>
  <header class="masthead page">
    <div class="masthead__top">
      <p class="kicker">{{ today }}</p>
      <p class="kicker masthead__season">2026–27 Season</p>
      <EditionToggle />
    </div>
    <hr class="rule rule--double" />
    <NuxtLink to="/" class="masthead__name display">Baller Knowledge</NuxtLink>
    <hr class="rule" />
    <nav aria-label="Sections">
      <ul class="masthead__nav">
        <li v-for="s in sections" :key="s.to">
          <NuxtLink :to="s.to" class="kicker">{{ s.label }}</NuxtLink>
        </li>
      </ul>
    </nav>
    <hr class="rule rule--heavy" />
  </header>
</template>

<style scoped>
.masthead {
  padding-top: var(--space-4);
}

.masthead__top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  padding-bottom: var(--space-3);
}

.masthead__season {
  margin-inline-start: auto;
}

.masthead__name {
  display: block;
  padding-block: var(--space-3) var(--space-2);
  font-size: var(--text-4xl);
  text-decoration: none;
  white-space: nowrap;
}

.masthead__name:hover {
  color: var(--color-spot);
}

.masthead__nav {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2) var(--space-6);
  padding: var(--space-3) 0;
  list-style: none;
}

.masthead__nav a {
  text-decoration-color: transparent;
}

.masthead__nav a:hover,
.masthead__nav a.router-link-active {
  text-decoration-color: var(--color-spot);
  text-decoration-thickness: 2px;
}

@media (max-width: 640px) {
  .masthead__season {
    display: none;
  }

  .masthead__name {
    font-size: clamp(2.25rem, 11.5vw, 5rem);
  }
}
</style>
