<script setup lang="ts" generic="Row extends Record<string, any>">
export interface Column {
  key: string
  label: string
  /** Full name for screen readers and the header tooltip, e.g. "Points" for PTS. */
  title?: string
  numeric?: boolean
  decimals?: number
  sortable?: boolean
  /** Custom text for a cell. For markup, use the `cell-<key>` slot instead. */
  format?: (value: any, row: any) => string
}

const props = withDefaults(
  defineProps<{
    columns: Column[]
    rows: Row[]
    caption: string
    /** Row key used to highlight one row in the spot color. */
    highlight?: (row: Row) => boolean
    initialSort?: { key: string; dir: 'asc' | 'desc' }
    rowKey?: (row: Row, index: number) => string | number
  }>(),
  { highlight: () => false, initialSort: undefined, rowKey: (_: Row, i: number) => i },
)

const sortKey = ref(props.initialSort?.key ?? '')
const sortDir = ref<'asc' | 'desc'>(props.initialSort?.dir ?? 'desc')

const sorted = computed(() => {
  if (!sortKey.value) return props.rows
  const k = sortKey.value
  const dir = sortDir.value === 'asc' ? 1 : -1
  return [...props.rows].sort((a, b) => {
    const av = a[k]
    const bv = b[k]
    if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
    return String(av).localeCompare(String(bv)) * dir
  })
})

function sortBy(col: Column) {
  if (!col.sortable) return
  if (sortKey.value === col.key) {
    sortDir.value = sortDir.value === 'desc' ? 'asc' : 'desc'
  } else {
    sortKey.value = col.key
    sortDir.value = col.numeric ? 'desc' : 'asc'
  }
}

function ariaSort(col: Column) {
  if (sortKey.value !== col.key) return col.sortable ? 'none' : undefined
  return sortDir.value === 'asc' ? 'ascending' : 'descending'
}

function format(col: Column, row: Row) {
  const v = row[col.key]
  if (col.format) return col.format(v, row)
  if (v === null || v === undefined) return '–'
  if (typeof v === 'number' && col.decimals !== undefined) return v.toFixed(col.decimals)
  return v
}

const root = ref<HTMLElement | null>(null)
useReveal(root, 30)
</script>

<template>
  <div ref="root" class="table-wrap">
    <table class="stats">
      <caption class="visually-hidden">{{ caption }}</caption>
      <thead>
        <tr>
          <th
            v-for="col in columns"
            :key="col.key"
            scope="col"
            :class="{ num: col.numeric }"
            :aria-sort="ariaSort(col)"
            :title="col.title"
          >
            <button v-if="col.sortable" type="button" class="sort" @click="sortBy(col)">
              <span>{{ col.label }}</span>
              <span class="sort__mark" aria-hidden="true">
                {{ sortKey === col.key ? (sortDir === 'desc' ? '▼' : '▲') : '' }}
              </span>
              <span v-if="col.title" class="visually-hidden">({{ col.title }})</span>
            </button>
            <template v-else>{{ col.label }}</template>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(row, i) in sorted" :key="rowKey(row, i)" class="reveal" :class="{ 'is-highlight': highlight(row) }">
          <td v-for="col in columns" :key="col.key" :class="{ num: col.numeric }">
            <slot :name="`cell-${col.key}`" :row="row" :value="row[col.key]">{{ format(col, row) }}</slot>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrap {
  position: relative; /* keeps visually-hidden header text inside the scroll box */
  min-width: 0;
  max-width: 100%;
  overflow-x: auto;
  border-top: var(--rule-heavy) solid var(--color-rule);
  border-bottom: var(--rule-hair) solid var(--color-rule);
}

.stats {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  font-variant-numeric: tabular-nums lining-nums;
}

th,
td {
  padding: var(--space-2) var(--space-3);
  text-align: left;
  white-space: nowrap;
}

th {
  font-size: var(--text-2xs);
  font-weight: 600;
  letter-spacing: var(--tracking-caps);
  text-transform: uppercase;
  color: var(--color-ink-muted);
  border-bottom: var(--rule-hair) solid var(--color-rule);
  vertical-align: bottom;
}

th.num,
td.num {
  text-align: right;
}

th.num .sort {
  flex-direction: row-reverse;
}

td {
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

tbody tr:last-child td {
  border-bottom: 0;
}

tbody tr:hover td {
  background: var(--color-paper-alt);
}

tr.is-highlight td {
  color: var(--color-spot-text);
  font-weight: 600;
}

.sort {
  display: inline-flex;
  align-items: baseline;
  gap: var(--space-1);
  padding: 0;
  background: none;
  border: 0;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  color: inherit;
  cursor: pointer;
}

.sort:hover span:first-child {
  text-decoration: underline;
  text-decoration-color: var(--color-spot);
  text-decoration-thickness: 2px;
  text-underline-offset: 0.3em;
}

[aria-sort='ascending'],
[aria-sort='descending'] {
  color: var(--color-ink);
}

.sort__mark {
  display: inline-block;
  width: 0.8em;
  font-size: 0.75em;
  color: var(--color-spot-text);
}
</style>
