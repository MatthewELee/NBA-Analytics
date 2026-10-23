<template>
  <footer class="footer page">
    <hr class="rule rule--double" />
    <div class="footer__row">
      <p class="kicker">Baller Knowledge</p>
      <p class="label">Stats: NBA.com via nba_api, balldontlie. News and awards: ESPN.</p>
      <p class="label">Not affiliated with the NBA.</p>
    </div>
  </footer>
</template>

<style scoped>
.footer {
  margin-top: var(--space-9);
  padding-bottom: var(--space-6);
}

.footer__row {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: var(--space-3) var(--space-6);
  padding-top: var(--space-4);
}
</style>
