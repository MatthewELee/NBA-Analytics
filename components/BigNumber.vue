<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    value: number
    decimals?: number
    label: string
    suffix?: string
    spot?: boolean
  }>(),
  { decimals: 0, suffix: '', spot: false },
)

const el = ref<HTMLElement | null>(null)
const shown = useCountUp(el, toRef(props, 'value'))
const text = computed(() => shown.value.toFixed(props.decimals))
const final = computed(() => props.value.toFixed(props.decimals) + props.suffix)
</script>

<template>
  <figure ref="el" class="big" :class="{ 'big--spot': spot }">
    <span class="big__value display num" aria-hidden="true">{{ text }}<span v-if="suffix" class="big__suffix">{{ suffix }}</span></span>
    <span class="visually-hidden">{{ final }}</span>
    <figcaption class="big__label kicker">{{ label }}</figcaption>
  </figure>
</template>

<style scoped>
.big {
  display: inline-flex;
  flex-direction: column;
}

.big__value {
  font-family: var(--font-display);
  font-size: var(--text-mega);
  line-height: 0.8;
  letter-spacing: -0.02em;
}

.big--spot .big__value {
  color: var(--color-spot);
}

.big__suffix {
  font-size: 0.4em;
  vertical-align: top;
  margin-left: 0.05em;
}

.big__label {
  margin-top: var(--space-3);
  padding-top: var(--space-2);
  border-top: var(--rule-heavy) solid var(--color-rule);
}
</style>
