<script setup lang="ts">
import { max, scaleLinear } from 'd3'

export interface RankBar {
  id: string | number
  label: string
  sublabel?: string
  value: number
}

/**
 * Ranked values as thin ink rules ending in a dot, labelled directly. The first bar is the
 * one that matters and takes the spot color. A plain table carries the same numbers for
 * screen readers.
 */
const props = withDefaults(
  defineProps<{ bars: RankBar[]; title: string; valueLabel: string; decimals?: number; rowHeight?: number }>(),
  { decimals: 0, rowHeight: 34 },
)

const wrap = ref<HTMLElement | null>(null)
const width = ref(640)
onMounted(() => {
  if (!wrap.value) return
  const ro = new ResizeObserver(([entry]) => {
    if (entry) width.value = Math.max(280, Math.round(entry.contentRect.width))
  })
  ro.observe(wrap.value)
  onBeforeUnmount(() => ro.disconnect())
})

const narrow = computed(() => width.value < 520)
// Names sit left of the bars on wide screens and above them on narrow ones.
const margin = computed(() => ({ top: 4, right: 56, bottom: 4, left: narrow.value ? 0 : 190 }))
const rowH = computed(() => (narrow.value ? props.rowHeight + 18 : props.rowHeight))
const height = computed(() => props.bars.length * rowH.value + margin.value.top + margin.value.bottom)
const innerW = computed(() => width.value - margin.value.left - margin.value.right)

const x = computed(() =>
  scaleLinear()
    .domain([0, max(props.bars, (b) => b.value) ?? 1])
    .range([0, innerW.value]),
)
const barY = (i: number) => i * rowH.value + (narrow.value ? rowH.value - 10 : rowH.value / 2)

const armed = ref(false)
const drawn = ref(false)
onMounted(() => {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reduce || !wrap.value || !('IntersectionObserver' in window)) return
  armed.value = true
  const io = new IntersectionObserver(([e]) => {
    if (e?.isIntersecting) {
      drawn.value = true
      io.disconnect()
    }
  })
  io.observe(wrap.value)
  onBeforeUnmount(() => io.disconnect())
})
</script>

<template>
  <figure ref="wrap" class="bars" :class="{ 'is-armed': armed, 'is-drawn': drawn }">
    <svg :width="width" :height="height" :viewBox="`0 0 ${width} ${height}`" aria-hidden="true">
      <g :transform="`translate(${margin.left},${margin.top})`">
        <line v-if="!narrow" class="baseline" :y2="bars.length * rowH" />
        <g
          v-for="(b, i) in bars"
          :key="b.id"
          class="bar"
          :class="{ 'bar--spot': i === 0 }"
          :style="{ '--i': i }"
        >
          <text
            class="bar__name"
            :x="narrow ? 0 : -14"
            :y="narrow ? barY(i) - 14 : barY(i)"
            dy="0.32em"
            :text-anchor="narrow ? 'start' : 'end'"
          >
            {{ b.label }}<tspan v-if="b.sublabel" class="bar__sub" dx="8">{{ b.sublabel }}</tspan>
          </text>
          <line class="bar__rule" :y1="barY(i)" :y2="barY(i)" :x2="x(b.value)" />
          <circle class="bar__dot" :cx="x(b.value)" :cy="barY(i)" :r="i === 0 ? 5 : 3.5" />
          <text class="bar__value" :x="x(b.value) + 12" :y="barY(i)" dy="0.32em">{{ b.value.toFixed(decimals) }}</text>
        </g>
      </g>
    </svg>
    <table class="visually-hidden">
      <caption>{{ title }}</caption>
      <thead>
        <tr><th scope="col">Rank</th><th scope="col">Player</th><th scope="col">{{ valueLabel }}</th></tr>
      </thead>
      <tbody>
        <tr v-for="(b, i) in bars" :key="b.id">
          <td>{{ i + 1 }}</td>
          <th scope="row">{{ b.label }}<template v-if="b.sublabel">, {{ b.sublabel }}</template></th>
          <td>{{ b.value.toFixed(decimals) }}</td>
        </tr>
      </tbody>
    </table>
  </figure>
</template>

<style scoped>
.bars {
  width: 100%;
}

svg {
  overflow: visible;
  font-variant-numeric: tabular-nums;
}

.baseline {
  stroke: var(--color-rule);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.bar__name {
  font-family: var(--font-body);
  font-size: var(--text-base);
  fill: var(--color-ink);
}

.bar__sub {
  font-family: var(--font-mono);
  font-size: var(--text-2xs);
  fill: var(--color-ink-muted);
  letter-spacing: var(--tracking-caps);
}

.bar__rule {
  stroke: var(--color-ink);
  stroke-width: 1.25;
}

.bar__dot {
  fill: var(--color-ink);
}

.bar__value {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  fill: var(--color-ink);
}

.bar--spot .bar__rule {
  stroke: var(--color-spot);
  stroke-width: 3;
}

.bar--spot .bar__dot {
  fill: var(--color-spot);
}

.bar--spot .bar__value,
.bar--spot .bar__name {
  fill: var(--color-spot-text);
  font-weight: 600;
}

/* Rules grow from the baseline on first view; the dot and number follow. */
.is-armed .bar__rule {
  transform: scaleX(0);
  transform-box: fill-box;
  transform-origin: left center;
}

.is-armed .bar__dot,
.is-armed .bar__value {
  opacity: 0;
}

.is-armed.is-drawn .bar__rule {
  transform: none;
  transition: transform var(--duration-slow) var(--ease-out);
  transition-delay: calc(var(--i) * 60ms);
}

.is-armed.is-drawn .bar__dot,
.is-armed.is-drawn .bar__value {
  opacity: 1;
  transition: opacity var(--duration-slow) var(--ease-out);
  transition-delay: calc(var(--i) * 60ms + var(--duration-slow) * 0.6);
}
</style>
