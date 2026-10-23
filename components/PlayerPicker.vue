<script setup lang="ts">
import type { ApiResponse, PlayerRef } from '~/types/api'

/** Search-as-you-type player box (ARIA combobox). Emits the chosen player. */
const props = withDefaults(defineProps<{ exclude?: number[]; placeholder?: string; label?: string }>(), {
  exclude: () => [],
  placeholder: 'Add a player',
  label: 'Search players',
})
const emit = defineEmits<{ select: [player: PlayerRef] }>()

const q = ref('')
const results = ref<PlayerRef[]>([])
const open = ref(false)
const active = ref(0)
const listId = useId()
const input = ref<HTMLInputElement | null>(null)

let timer: ReturnType<typeof setTimeout> | undefined
let seq = 0
watch(q, (value) => {
  clearTimeout(timer)
  const term = value.trim()
  if (term.length < 2) {
    results.value = []
    open.value = false
    return
  }
  timer = setTimeout(async () => {
    const mine = ++seq
    try {
      const res = await $fetch<ApiResponse<PlayerRef[]>>('/api/players', { query: { q: term, limit: 8, all: 1 } })
      if (mine !== seq) return
      results.value = res.data.filter((p) => !props.exclude.includes(p.id))
      active.value = 0
      open.value = true
    } catch {
      results.value = []
    }
  }, 180)
})

function choose(p: PlayerRef | undefined) {
  if (!p) return
  emit('select', p)
  q.value = ''
  results.value = []
  open.value = false
  input.value?.focus()
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    open.value = results.value.length > 0
    active.value = Math.min(active.value + 1, results.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    active.value = Math.max(active.value - 1, 0)
  } else if (e.key === 'Enter') {
    if (open.value) {
      e.preventDefault()
      choose(results.value[active.value])
    }
  } else if (e.key === 'Escape') {
    open.value = false
  }
}
</script>

<template>
  <div class="picker">
    <label class="visually-hidden" :for="`${listId}-input`">{{ label }}</label>
    <input
      :id="`${listId}-input`"
      ref="input"
      v-model="q"
      type="search"
      class="picker__input"
      role="combobox"
      autocomplete="off"
      spellcheck="false"
      :placeholder="placeholder"
      :aria-expanded="open"
      :aria-controls="listId"
      :aria-activedescendant="open && results.length ? `${listId}-${active}` : undefined"
      @keydown="onKey"
      @blur="open = false"
      @focus="open = results.length > 0"
    />
    <ul v-show="open" :id="listId" role="listbox" class="picker__list">
      <li
        v-for="(p, i) in results"
        :id="`${listId}-${i}`"
        :key="p.id"
        role="option"
        :aria-selected="i === active"
        class="picker__opt"
        @mousedown.prevent="choose(p)"
        @mouseenter="active = i"
      >
        <span>{{ p.fullName }}</span>
        <span class="label">{{ p.team?.abbr ?? (p.isActive ? 'FA' : 'Retired') }}<template v-if="p.position"> · {{ p.position }}</template></span>
      </li>
      <li v-if="!results.length" class="picker__none label" role="option" aria-disabled="true">No players found</li>
    </ul>
  </div>
</template>

<style scoped>
.picker {
  position: relative;
}

.picker__input {
  width: 100%;
  padding: var(--space-3) 0;
  background: transparent;
  border: 0;
  border-bottom: var(--rule-heavy) solid var(--color-rule);
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-weight: var(--weight-display-light);
  font-size: var(--text-xl);
  text-transform: uppercase;
}

.picker__input::placeholder {
  color: var(--color-ink-muted);
}

.picker__input:focus-visible {
  outline: none;
  border-bottom-color: var(--color-spot);
}

.picker__list {
  position: absolute;
  z-index: 5;
  left: 0;
  right: 0;
  margin: 0;
  padding: 0;
  list-style: none;
  background: var(--color-paper);
  border: var(--rule-hair) solid var(--color-rule);
  border-top: 0;
}

.picker__opt,
.picker__none {
  display: flex;
  justify-content: space-between;
  gap: var(--space-3);
  padding: var(--space-2) var(--space-3);
  border-top: var(--rule-hair) solid var(--color-rule-faint);
}

.picker__opt {
  cursor: pointer;
}

.picker__opt[aria-selected='true'] {
  background: var(--color-ink);
  color: var(--color-paper);
}

.picker__opt[aria-selected='true'] .label {
  color: inherit;
}
</style>
