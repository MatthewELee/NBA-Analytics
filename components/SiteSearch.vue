<script setup lang="ts">
import type { ApiResponse, SearchResults } from '~/types/api'

/**
 * Site-wide search for players and teams. Opens with the "/" key from anywhere (unless you're
 * typing in a field) or with the masthead button. Arrow keys move, Enter opens, Escape closes.
 */
interface Hit {
  key: string
  to: string
  name: string
  meta: string
  kind: 'Player' | 'Team'
  color?: string | null
}

const dialog = ref<HTMLDialogElement | null>(null)
const input = ref<HTMLInputElement | null>(null)
const q = ref('')
const hits = ref<Hit[]>([])
const active = ref(0)
const searched = ref(false)
const listId = useId()

function open() {
  if (!dialog.value || dialog.value.open) return
  dialog.value.showModal()
  nextTick(() => input.value?.select())
}
function close() {
  dialog.value?.close()
}

function isTyping(el: EventTarget | null) {
  if (!(el instanceof HTMLElement)) return false
  return el.isContentEditable || ['INPUT', 'TEXTAREA', 'SELECT'].includes(el.tagName)
}
function onGlobalKey(e: KeyboardEvent) {
  if (e.key === '/' && !e.metaKey && !e.ctrlKey && !e.altKey && !isTyping(e.target)) {
    e.preventDefault()
    open()
  }
}
onMounted(() => window.addEventListener('keydown', onGlobalKey))
onBeforeUnmount(() => window.removeEventListener('keydown', onGlobalKey))

let timer: ReturnType<typeof setTimeout> | undefined
let seq = 0
watch(q, (value) => {
  clearTimeout(timer)
  const term = value.trim()
  if (term.length < 2) {
    hits.value = []
    searched.value = false
    return
  }
  timer = setTimeout(async () => {
    const mine = ++seq
    try {
      const res = await $fetch<ApiResponse<SearchResults>>('/api/search', { query: { q: term } })
      if (mine !== seq) return
      hits.value = [
        ...res.data.teams.map(
          (t): Hit => ({ key: `t${t.id}`, to: `/teams/${t.abbr}`, name: `${t.city} ${t.name}`, meta: t.abbr, kind: 'Team', color: t.colorPrimary }),
        ),
        ...res.data.players.map(
          (p): Hit => ({
            key: `p${p.id}`,
            to: `/players/${p.slug}`,
            name: p.fullName,
            meta: [p.team?.abbr ?? (p.isActive ? 'Free agent' : 'Retired'), p.position].filter(Boolean).join(' · '),
            kind: 'Player',
          }),
        ),
      ]
      active.value = 0
      searched.value = true
    } catch {
      hits.value = []
    }
  }, 150)
})

function go(hit: Hit | undefined) {
  if (!hit) return
  close()
  q.value = ''
  navigateTo(hit.to)
}

function onKey(e: KeyboardEvent) {
  if (e.key === 'ArrowDown') {
    e.preventDefault()
    active.value = Math.min(active.value + 1, hits.value.length - 1)
  } else if (e.key === 'ArrowUp') {
    e.preventDefault()
    active.value = Math.max(active.value - 1, 0)
  } else if (e.key === 'Enter') {
    e.preventDefault()
    go(hits.value[active.value])
  }
}

// Clicking the backdrop (the dialog element itself, outside the panel) closes it.
function onDialogClick(e: MouseEvent) {
  if (e.target === dialog.value) close()
}

defineExpose({ open })
</script>

<template>
  <button type="button" class="trigger kicker" aria-haspopup="dialog" @click="open">
    Search <kbd class="trigger__key">/</kbd>
  </button>
  <dialog ref="dialog" class="search" aria-label="Search players and teams" @click="onDialogClick">
    <div class="search__panel">
      <div class="search__bar">
        <label class="visually-hidden" :for="`${listId}-input`">Search players and teams</label>
        <input
          :id="`${listId}-input`"
          ref="input"
          v-model="q"
          type="search"
          class="search__input"
          role="combobox"
          autocomplete="off"
          spellcheck="false"
          placeholder="Player or team"
          aria-expanded="true"
          :aria-controls="listId"
          :aria-activedescendant="hits.length ? `${listId}-${active}` : undefined"
          @keydown="onKey"
        />
        <button type="button" class="search__close label" @click="close">Esc</button>
      </div>
      <ul :id="listId" role="listbox" class="search__list" aria-label="Results">
        <li
          v-for="(h, i) in hits"
          :id="`${listId}-${i}`"
          :key="h.key"
          role="option"
          :aria-selected="i === active"
          class="search__opt"
          @click="go(h)"
          @mouseenter="active = i"
        >
          <span class="label search__kind">{{ h.kind }}</span>
          <span class="search__name">
            <span v-if="h.kind === 'Team'" class="search__chip" :style="h.color ? { background: `#${h.color}` } : undefined" aria-hidden="true" />
            {{ h.name }}
          </span>
          <span class="label search__meta">{{ h.meta }}</span>
        </li>
      </ul>
      <p v-if="searched && !hits.length" class="search__note label" role="status">Nothing matches “{{ q.trim() }}”.</p>
      <p v-else-if="!searched" class="search__note label">Type two letters or more. Arrow keys move, Enter opens.</p>
    </div>
  </dialog>
</template>

<style scoped>
.trigger {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-1) var(--space-2);
  background: none;
  border: var(--rule-hair) solid var(--color-rule);
  color: var(--color-ink);
  cursor: pointer;
}

.trigger:hover {
  border-color: var(--color-spot);
}

.trigger__key {
  font-family: var(--font-mono);
  padding-inline: 0.4em;
  border: var(--rule-hair) solid var(--color-rule-faint);
}

.search {
  width: min(44rem, calc(100vw - 2 * var(--page-margin)));
  max-width: none;
  margin: 12vh auto auto;
  padding: 0;
  border: var(--rule-heavy) solid var(--color-rule);
  border-radius: var(--radius);
  background: var(--color-paper);
  color: var(--color-ink);
}

/* Flat dimming only: no blur. */
.search::backdrop {
  background: var(--color-scrim);
}

.search__panel {
  padding: var(--space-4) var(--space-5) var(--space-5);
}

.search__bar {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  border-bottom: var(--rule-heavy) solid var(--color-rule);
}

.search__input {
  flex: 1;
  min-width: 0;
  padding: var(--space-3) 0;
  background: transparent;
  border: 0;
  border-radius: var(--radius);
  font-family: var(--font-display);
  font-weight: var(--weight-display);
  font-size: var(--text-2xl);
  text-transform: uppercase;
}

.search__input:focus-visible {
  outline: none;
}

.search__bar:focus-within {
  border-bottom-color: var(--color-spot);
}

.search__close {
  padding: var(--space-1) var(--space-2);
  background: none;
  border: var(--rule-hair) solid var(--color-rule-faint);
  cursor: pointer;
}

.search__list {
  list-style: none;
  padding: 0;
  margin: 0;
  max-height: 55vh;
  overflow-y: auto;
}

.search__opt {
  display: grid;
  grid-template-columns: 4.5rem minmax(0, 1fr) auto;
  align-items: baseline;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
  cursor: pointer;
}

.search__opt[aria-selected='true'] {
  background: var(--color-ink);
  color: var(--color-paper);
}

.search__opt[aria-selected='true'] .label {
  color: inherit;
}

.search__name {
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  font-size: var(--text-lg);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.search__chip {
  flex: none;
  width: 4px;
  height: 1em;
  background: var(--color-rule);
}

.search__note {
  padding-top: var(--space-3);
}

@media (max-width: 640px) {
  .search {
    margin-top: var(--space-4);
  }

  .search__opt {
    grid-template-columns: minmax(0, 1fr) auto;
  }

  .search__kind {
    display: none;
  }
}
</style>
