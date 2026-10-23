<script setup lang="ts" generic="T extends string | number">
/** A row of mutually exclusive options, as a radio group. Arrow keys move between them. */
const props = defineProps<{
  options: { value: T; label: string }[]
  label: string
}>()
const model = defineModel<T>({ required: true })

const buttons = ref<HTMLButtonElement[]>([])

function move(delta: number) {
  const i = props.options.findIndex((o) => o.value === model.value)
  const next = (i + delta + props.options.length) % props.options.length
  model.value = props.options[next]!.value
  buttons.value[next]?.focus()
}
</script>

<template>
  <div class="seg" role="radiogroup" :aria-label="label" @keydown.right.prevent="move(1)" @keydown.left.prevent="move(-1)">
    <button
      v-for="o in options"
      :key="String(o.value)"
      ref="buttons"
      type="button"
      role="radio"
      class="seg__opt kicker"
      :aria-checked="o.value === model"
      :tabindex="o.value === model ? 0 : -1"
      @click="model = o.value"
    >
      {{ o.label }}
    </button>
  </div>
</template>

<style scoped>
.seg {
  display: inline-flex;
  max-width: 100%;
  overflow-x: auto;
  border: var(--rule-hair) solid var(--color-rule);
}

.seg__opt {
  flex: none;
  padding: var(--space-2) var(--space-3);
  background: transparent;
  border: 0;
  border-left: var(--rule-hair) solid var(--color-rule);
  cursor: pointer;
  transition: background-color var(--duration-fast) var(--ease-out), color var(--duration-fast) var(--ease-out);
}

.seg__opt:first-child {
  border-left: 0;
}

.seg__opt:hover {
  background: var(--color-paper-alt);
}

.seg__opt[aria-checked='true'] {
  background: var(--color-ink);
  color: var(--color-paper);
}
</style>
