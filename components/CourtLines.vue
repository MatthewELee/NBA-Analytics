<script setup lang="ts">
/**
 * NBA half court, drawn in feet (50 wide, 47 deep) with the basket at the top.
 * Used as a texture and, from step 3, as the base for shot charts.
 */
withDefaults(defineProps<{ decorative?: boolean }>(), { decorative: true })
</script>

<template>
  <svg
    class="court"
    viewBox="-1 -1 52 49"
    :aria-hidden="decorative ? 'true' : undefined"
    :role="decorative ? undefined : 'img'"
    :aria-label="decorative ? undefined : 'Half court diagram'"
  >
    <g fill="none">
      <!-- boundary -->
      <rect x="0" y="0" width="50" height="47" />
      <!-- lane (16 ft wide, 19 ft deep) -->
      <rect x="17" y="0" width="16" height="19" />
      <!-- free throw circle -->
      <path d="M 19 19 A 6 6 0 0 0 31 19" />
      <path d="M 19 19 A 6 6 0 0 1 31 19" stroke-dasharray="1 1" />
      <!-- backboard and rim -->
      <line x1="22" y1="4" x2="28" y2="4" />
      <circle cx="25" cy="5.25" r="0.75" />
      <!-- restricted area -->
      <path d="M 21 5.25 A 4 4 0 0 0 29 5.25" />
      <!-- three-point line: corners 22 ft, arc 23.75 ft -->
      <path d="M 3 0 L 3 14 A 23.75 23.75 0 0 0 47 14 L 47 0" />
      <!-- center circle -->
      <path d="M 19 47 A 6 6 0 0 1 31 47" />
      <path d="M 23 47 A 2 2 0 0 1 27 47" />
    </g>
  </svg>
</template>

<style scoped>
.court g {
  stroke: currentColor;
}

.court g > * {
  stroke-width: 1px;
  vector-effect: non-scaling-stroke;
}
</style>
