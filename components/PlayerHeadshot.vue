<script setup lang="ts">
/** A player's photo, printed in ink. Falls back to initials when the photo is missing. */
const props = withDefaults(defineProps<{ src: string | null; name: string; size?: 'sm' | 'md' | 'lg' }>(), {
  size: 'md',
})

const failed = ref(false)
const initials = computed(() =>
  props.name
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w[0])
    .slice(0, 2)
    .join(''),
)
</script>

<template>
  <figure class="shot" :class="`shot--${size}`">
    <img v-if="src && !failed" :src="src" :alt="name" loading="lazy" @error="failed = true" />
    <span v-else class="shot__initials display" role="img" :aria-label="name">{{ initials }}</span>
  </figure>
</template>

<style scoped>
.shot {
  position: relative;
  aspect-ratio: 1040 / 760;
  overflow: hidden;
  border-bottom: var(--rule-heavy) solid var(--color-rule);
  background: var(--color-paper-alt);
}

.shot--sm {
  width: 4rem;
}

.shot--md {
  width: 10rem;
}

.shot--lg {
  width: 100%;
}

img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: top;
  filter: grayscale(1) contrast(1.1);
  mix-blend-mode: multiply;
}

:root[data-edition='night'] img {
  mix-blend-mode: normal;
  filter: grayscale(1) contrast(1.05) brightness(0.9);
}

@media (prefers-color-scheme: dark) {
  :root:not([data-edition='day']) img {
    mix-blend-mode: normal;
    filter: grayscale(1) contrast(1.05) brightness(0.9);
  }
}

.shot__initials {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-size: 3em;
  color: var(--color-ink-muted);
}

.shot--sm .shot__initials {
  font-size: 1.25rem;
}

.shot--lg .shot__initials {
  font-size: var(--text-3xl);
}
</style>
