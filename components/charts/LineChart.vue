<script setup lang="ts">
import { curveMonotoneX, extent, line, max, min, scaleLinear } from 'd3'

export interface Point {
  x: number
  y: number
}

export interface Series {
  id: string
  label: string
  points: Point[]
  /** The one series that matters gets the spot color. Everything else stays ink. */
  emphasis?: boolean
}

const props = withDefaults(
  defineProps<{
    series: Series[]
    title: string
    xLabel: string
    yLabel: string
    height?: number
    yDecimals?: number
    formatX?: (x: number) => string
  }>(),
  { height: 340, yDecimals: 1, formatX: (x: number) => String(x) },
)

const wrap = ref<HTMLElement | null>(null)
const width = ref(720)

onMounted(() => {
  if (!wrap.value) return
  const ro = new ResizeObserver(([entry]) => {
    if (entry) width.value = Math.max(280, Math.round(entry.contentRect.width))
  })
  ro.observe(wrap.value)
  onBeforeUnmount(() => ro.disconnect())
})

// Right margin leaves room for direct labels at the end of each line.
const margin = computed(() => ({ top: 16, right: 140, bottom: 36, left: 40 }))
const innerW = computed(() => width.value - margin.value.left - margin.value.right)
const innerH = computed(() => props.height - margin.value.top - margin.value.bottom)

const all = computed(() => props.series.flatMap((s) => s.points))

const x = computed(() => {
  const [lo, hi] = extent(all.value, (p) => p.x) as [number, number]
  return scaleLinear().domain([lo, hi]).range([0, innerW.value])
})

const y = computed(() => {
  const lo = min(all.value, (p) => p.y) ?? 0
  const hi = max(all.value, (p) => p.y) ?? 1
  const pad = (hi - lo) * 0.08 || 1
  // Stats that can't go negative floor at zero; differentials and ratings keep their sign.
  return scaleLinear()
    .domain([lo >= 0 ? Math.max(0, lo - pad) : lo - pad, hi + pad])
    .nice(5)
    .range([innerH.value, 0])
})

const path = computed(() =>
  line<Point>()
    .x((p) => x.value(p.x))
    .y((p) => y.value(p.y))
    .curve(curveMonotoneX),
)

const xTicks = computed(() => {
  const [lo, hi] = x.value.domain() as [number, number]
  const count = Math.min(hi - lo, width.value < 480 ? 4 : 8)
  return x.value.ticks(count).filter((t) => Number.isInteger(t))
})
const yTicks = computed(() => y.value.ticks(5))

// Emphasized series draws last so it sits on top.
const ordered = computed(() => [...props.series].sort((a, b) => Number(!!a.emphasis) - Number(!!b.emphasis)))

// Direct labels at each line's last point, nudged apart so they never overlap.
const labels = computed(() => {
  const gap = 15
  const items = props.series
    .map((s) => {
      const last = s.points[s.points.length - 1]!
      return { id: s.id, label: s.label, emphasis: !!s.emphasis, value: last.y, x: x.value(last.x), y: y.value(last.y) }
    })
    .sort((a, b) => a.y - b.y)
  for (let i = 1; i < items.length; i++) {
    const prev = items[i - 1]!
    const cur = items[i]!
    if (cur.y - prev.y < gap) cur.y = prev.y + gap
  }
  return items
})

// Draw-on animation: each line strokes in once on first view.
// Lines are visible by default (server render, no JS, reduced motion); the client arms
// the animation only when it can play it.
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

const xs = computed(() => Array.from(new Set(all.value.map((p) => p.x))).sort((a, b) => a - b))
const showTable = ref(false)
const tableId = useId()
</script>

<template>
  <figure ref="wrap" class="chart" :class="{ 'is-armed': armed, 'is-drawn': drawn }">
    <svg
      :width="width"
      :height="height"
      :viewBox="`0 0 ${width} ${height}`"
      role="img"
      :aria-label="`${title}. Line chart of ${yLabel} by ${xLabel}. A data table follows.`"
    >
      <g :transform="`translate(${margin.left},${margin.top})`">
        <!-- y gridlines: faint hairlines only -->
        <g class="axis axis--y">
          <g v-for="t in yTicks" :key="t" :transform="`translate(0,${y(t)})`">
            <line class="grid" :x2="innerW" />
            <text x="-8" dy="0.32em" text-anchor="end">{{ t }}</text>
          </g>
        </g>
        <!-- baseline, and a zero line when values cross zero -->
        <line class="baseline" :y1="innerH" :y2="innerH" :x2="innerW" />
        <line v-if="y.domain()[0]! < 0" class="baseline" :y1="y(0)" :y2="y(0)" :x2="innerW" />
        <g class="axis axis--x" :transform="`translate(0,${innerH})`">
          <g v-for="t in xTicks" :key="t" :transform="`translate(${x(t)},0)`">
            <line class="tick" y2="5" />
            <text y="20" text-anchor="middle">{{ formatX(t) }}</text>
          </g>
        </g>

        <g v-for="s in ordered" :key="s.id" class="series" :class="{ 'series--spot': s.emphasis }">
          <path class="series__line" :d="path(s.points) ?? ''" pathLength="1" />
          <circle
            class="series__end"
            :cx="x(s.points[s.points.length - 1]!.x)"
            :cy="y(s.points[s.points.length - 1]!.y)"
            r="3.5"
          />
        </g>

        <g class="labels">
          <text
            v-for="l in labels"
            :key="l.id"
            :x="l.x + 10"
            :y="l.y"
            dy="0.32em"
            :class="{ 'label--spot': l.emphasis }"
          >
            <tspan class="label__name">{{ l.label }}</tspan>
            <tspan class="label__value" dx="6">{{ l.value.toFixed(yDecimals) }}</tspan>
          </text>
        </g>
      </g>
    </svg>

    <figcaption class="chart__caption">
      <span class="label">{{ yLabel }} by {{ xLabel.toLowerCase() }}</span>
      <button
        type="button"
        class="chart__toggle label"
        :aria-expanded="showTable"
        :aria-controls="tableId"
        @click="showTable = !showTable"
      >
        {{ showTable ? 'Hide' : 'Show' }} data table
      </button>
    </figcaption>

    <div v-show="showTable" :id="tableId" class="chart__table">
      <table>
        <caption class="visually-hidden">{{ title }}</caption>
        <thead>
          <tr>
            <th scope="col">{{ xLabel }}</th>
            <th v-for="s in series" :key="s.id" scope="col" class="num">{{ s.label }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="xv in xs" :key="xv">
            <th scope="row">{{ formatX(xv) }}</th>
            <td v-for="s in series" :key="s.id" class="num">
              {{ s.points.find((p) => p.x === xv)?.y.toFixed(yDecimals) ?? '—' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </figure>
</template>

<style scoped>
.chart {
  width: 100%;
}

svg {
  overflow: visible;
  font-family: var(--font-mono);
  font-variant-numeric: tabular-nums;
}

.axis text {
  font-size: var(--text-2xs);
  fill: var(--color-ink-muted);
}

.grid {
  stroke: var(--color-rule-faint);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.baseline,
.tick {
  stroke: var(--color-rule);
  stroke-width: 1;
  shape-rendering: crispEdges;
}

.series__line {
  fill: none;
  stroke: var(--color-ink);
  stroke-width: 1.25;
  stroke-linejoin: round;
  stroke-linecap: round;
  opacity: 0.55;
}

.is-armed .series__line {
  stroke-dasharray: 1;
  stroke-dashoffset: 1;
}

.series__end {
  fill: var(--color-ink);
  opacity: 0.55;
}

.series--spot .series__line {
  stroke: var(--color-spot);
  stroke-width: 2.5;
  opacity: 1;
}

.series--spot .series__end {
  fill: var(--color-spot);
  opacity: 1;
}

.is-armed.is-drawn .series__line {
  stroke-dashoffset: 0;
  transition: stroke-dashoffset calc(var(--duration-slow) * 2) var(--ease-out);
}

.labels text {
  font-size: var(--text-xs);
  fill: var(--color-ink-muted);
}

.labels .label--spot {
  fill: var(--color-spot-text);
  font-weight: 600;
}

.label__value {
  fill: inherit;
}

.chart__caption {
  display: flex;
  justify-content: space-between;
  gap: var(--space-4);
  margin-top: var(--space-3);
  padding-top: var(--space-2);
  border-top: var(--rule-hair) solid var(--color-rule-faint);
}

.chart__toggle {
  padding: 0;
  background: none;
  border: 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 0.25em;
}

.chart__toggle:hover {
  color: var(--color-ink);
  text-decoration-color: var(--color-spot);
}

.chart__table {
  margin-top: var(--space-3);
  overflow-x: auto;
}

.chart__table table {
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--text-xs);
  font-variant-numeric: tabular-nums;
}

.chart__table th,
.chart__table td {
  padding: var(--space-1) var(--space-3);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
  text-align: left;
}

.chart__table .num {
  text-align: right;
}
</style>
