import type { Ref } from 'vue'

/**
 * Ticks a number up from 0 to `target` the first time `el` scrolls into view.
 * Server render and reduced motion both show the final value.
 */
export function useCountUp(el: Ref<HTMLElement | null>, target: Ref<number>, duration = 900) {
  const value = ref(target.value)

  onMounted(() => {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce || !el.value || !('IntersectionObserver' in window)) return

    value.value = 0
    const io = new IntersectionObserver(([entry]) => {
      if (!entry?.isIntersecting) return
      io.disconnect()
      const start = performance.now()
      const end = target.value
      const frame = (now: number) => {
        const t = Math.min(1, (now - start) / duration)
        const eased = 1 - Math.pow(1 - t, 3)
        value.value = end * eased
        if (t < 1) requestAnimationFrame(frame)
      }
      requestAnimationFrame(frame)
    })
    io.observe(el.value)
    onBeforeUnmount(() => io.disconnect())
  })

  watch(target, (v) => (value.value = v))

  return value
}
