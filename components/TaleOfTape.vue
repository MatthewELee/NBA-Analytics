<script setup lang="ts">
/**
 * Bar rows comparing players stat by stat. Two players mirror each other around the
 * label; one or three players get a bar each. The leader in each row is in the spot color.
 */
export interface TapeRow {
  label: string
  title?: string
  values: (number | null)[]
  format: (v: number | null) => string
}
export interface TapeGroup {
  title: string
  rows: TapeRow[]
}

const props = defineProps<{ groups: TapeGroup[]; names: string[] }>()
const mirrored = computed(() => props.names.length === 2)

const root = ref<HTMLElement | null>(null)
useReveal(root, 25)

function scale(row: TapeRow) {
  const vals = row.values.map((v) => v ?? 0)
  const max = Math.max(...vals.map(Math.abs))
  const best = Math.max(...vals)
  return row.values.map((v) => ({
    width: max > 0 ? Math.max(0.5, (Math.abs(v ?? 0) / max) * 100) : 0,
    lead: v !== null && vals.filter((x) => x === best).length === 1 && v === best,
    text: row.format(v),
  }))
}
</script>

<template>
  <div ref="root" class="tape" :class="{ 'tape--mirror': mirrored }" :style="{ '--n': names.length }">
    <div class="tape__names" aria-hidden="true">
      <span v-for="(n, i) in names" :key="n + i" class="kicker">{{ n }}</span>
    </div>
    <section v-for="g in groups" :key="g.title" class="tape__group">
      <h3 class="label tape__title">{{ g.title }}</h3>
      <table class="tape__table">
        <caption class="visually-hidden">{{ g.title }}: {{ names.join(', ') }}</caption>
        <thead class="visually-hidden">
          <tr>
            <th scope="col">Stat</th>
            <th v-for="(n, i) in names" :key="n + i" scope="col">{{ n }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in g.rows" :key="r.label" class="tape__row reveal">
            <th scope="row" class="tape__label kicker" :title="r.title">{{ r.label }}</th>
            <td v-for="(cell, i) in scale(r)" :key="i" class="tape__cell" :class="{ 'is-lead': cell.lead }">
              <span class="tape__bar" :style="{ width: `${cell.width}%` }" aria-hidden="true" />
              <span class="tape__value num">{{ cell.text }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
  </div>
</template>

<style scoped>
.tape__names {
  display: grid;
  grid-template-columns: 7rem repeat(var(--n), minmax(0, 1fr));
  gap: var(--space-4);
  padding-bottom: var(--space-2);
}

.tape__names::before {
  content: '';
}

.tape--mirror .tape__names {
  grid-template-columns: 1fr 7rem 1fr;
}

.tape--mirror .tape__names::before {
  display: none;
}

.tape--mirror .tape__names span:first-child {
  text-align: right;
}

.tape--mirror .tape__names span:last-child {
  grid-column: 3;
}

.tape__group {
  border-top: var(--rule-heavy) solid var(--color-rule);
  padding-top: var(--space-2);
  margin-bottom: var(--space-5);
}

.tape__title {
  margin-bottom: var(--space-1);
}

.tape__table {
  width: 100%;
  border-collapse: collapse;
}

.tape__row {
  display: grid;
  grid-template-columns: 7rem repeat(var(--n), minmax(0, 1fr));
  gap: var(--space-4);
  align-items: center;
  padding-block: var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.tape--mirror .tape__row {
  grid-template-columns: 1fr 7rem 1fr;
}

.tape__label {
  text-align: left;
  font-weight: 500;
}

.tape--mirror .tape__label {
  grid-column: 2;
  grid-row: 1;
  text-align: center;
}

.tape__cell {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  min-width: 0;
}

.tape--mirror .tape__cell:nth-child(2) {
  grid-column: 1;
  grid-row: 1;
  flex-direction: row-reverse;
}

.tape--mirror .tape__cell:nth-child(3) {
  grid-column: 3;
}

.tape__bar {
  display: block;
  height: 0.75rem;
  max-width: calc(100% - 4.5rem);
  background: var(--color-ink);
  opacity: 0.85;
  transition: width var(--duration-slow) var(--ease-out);
}

.tape__value {
  flex: none;
  font-size: var(--text-sm);
}

.tape__cell.is-lead .tape__bar {
  background: var(--color-spot);
  opacity: 1;
}

.tape__cell.is-lead .tape__value {
  color: var(--color-spot-text);
  font-weight: 600;
}

@media (max-width: 640px) {
  .tape__row,
  .tape__names {
    grid-template-columns: 4.5rem repeat(var(--n), minmax(0, 1fr));
    gap: var(--space-2);
  }

  .tape--mirror .tape__row,
  .tape--mirror .tape__names {
    grid-template-columns: 1fr 4.5rem 1fr;
  }

  .tape__bar {
    max-width: calc(100% - 3.5rem);
  }
}
</style>
