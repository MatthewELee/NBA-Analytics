<script setup lang="ts">
import type { NuxtError } from '#app'

const props = defineProps<{ error: NuxtError }>()
const missing = computed(() => props.error.statusCode === 404)

useHead({ title: missing.value ? 'Not yet printed' : 'Error' })
</script>

<template>
  <NuxtLayout>
    <section class="err">
      <p class="kicker err__code num">{{ error.statusCode }}</p>
      <h1 class="display err__head">{{ missing ? 'Not yet printed.' : 'Stop the presses.' }}</h1>
      <p class="lede">
        {{ missing ? 'This page is not in the program yet. It is on the build list.' : error.message }}
      </p>
      <p><button type="button" class="kicker err__back" @click="clearError({ redirect: '/' })">Back to the front page</button></p>
    </section>
  </NuxtLayout>
</template>

<style scoped>
.err {
  display: grid;
  gap: var(--space-5);
  padding-block: var(--space-8);
}

.err__code {
  color: var(--color-spot-text);
}

.err__head {
  font-size: var(--text-4xl);
}

.err__back {
  padding: 0;
  background: none;
  border: 0;
  cursor: pointer;
  text-decoration: underline;
  text-underline-offset: 0.25em;
}

.err__back:hover {
  text-decoration-color: var(--color-spot);
  text-decoration-thickness: 2px;
}
</style>
