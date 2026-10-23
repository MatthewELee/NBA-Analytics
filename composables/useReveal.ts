import type { Ref } from 'vue'

/**
 * Adds `.is-in` to every `.reveal` child of `root` the first time it scrolls into view,
 * staggered by `step` ms. Rows added later (filters, new data) are picked up on update.
 * With reduced motion the CSS shows everything immediately.
 */
export function useReveal(root: Ref<HTMLElement | null>, step = 40) {
  let io: IntersectionObserver | null = null
  const seen = new WeakSet<Element>()

  function scan() {
    const el = root.value
    if (!el) return
    const fresh = Array.from(el.querySelectorAll<HTMLElement>('.reveal')).filter((i) => !seen.has(i))
    if (!fresh.length) return
    if (!io) {
      fresh.forEach((i) => i.classList.add('is-in'))
      return
    }
    fresh.forEach((item, index) => {
      seen.add(item)
      item.style.transitionDelay = `${Math.min(index, 12) * step}ms`
      io!.observe(item)
    })
  }

  onMounted(() => {
    if ('IntersectionObserver' in window) {
      io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (!entry.isIntersecting) return
            entry.target.classList.add('is-in')
            io?.unobserve(entry.target)
          })
        },
        { rootMargin: '0px 0px -10% 0px' },
      )
    }
    scan()
  })
  onUpdated(() => nextTick(scan))
  onBeforeUnmount(() => io?.disconnect())
}
