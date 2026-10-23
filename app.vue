<script setup lang="ts">
const { choice } = useEdition()

useHead({
  htmlAttrs: {
    'data-edition': computed(() => choice.value ?? undefined),
  },
})
</script>

<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
