import type { Ref } from 'vue'

/**
 * Adds `.is-in` to every `.reveal` child of `root` the first time it scrolls into view,
 * staggered by `step` ms. With reduced motion the CSS shows everything immediately.
 */
export function useReveal(root: Ref<HTMLElement | null>, step = 40) {
  onMounted(() => {
    const el = root.value
    if (!el) return
    const items = Array.from(el.querySelectorAll<HTMLElement>('.reveal'))
    if (!('IntersectionObserver' in window)) {
      items.forEach((i) => i.classList.add('is-in'))
      return
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (!entry.isIntersecting) return
          const target = entry.target as HTMLElement
          const index = items.indexOf(target)
          target.style.transitionDelay = `${Math.min(index, 12) * step}ms`
          target.classList.add('is-in')
          io.unobserve(target)
        })
      },
      { rootMargin: '0px 0px -10% 0px' },
    )
    items.forEach((i) => io.observe(i))
    onBeforeUnmount(() => io.disconnect())
  })
}
