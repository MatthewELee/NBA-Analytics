export type Edition = 'day' | 'night'

/**
 * The reader's chosen edition. `null` means "follow the system setting".
 * Stored in a cookie so the server renders the right edition with no flash.
 */
export function useEdition() {
  const choice = useCookie<Edition | null>('bk-edition', {
    default: () => null,
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
  })

  const systemPrefersNight = useState('bk-system-night', () => false)

  if (import.meta.client) {
    onMounted(() => {
      const mq = window.matchMedia('(prefers-color-scheme: dark)')
      systemPrefersNight.value = mq.matches
      mq.addEventListener('change', (e) => (systemPrefersNight.value = e.matches))
    })
  }

  const edition = computed<Edition>(() => choice.value ?? (systemPrefersNight.value ? 'night' : 'day'))

  function set(next: Edition) {
    choice.value = next
  }

  function toggle() {
    set(edition.value === 'night' ? 'day' : 'night')
  }

  return { choice, edition, set, toggle }
}
