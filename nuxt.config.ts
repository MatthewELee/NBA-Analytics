// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2026-10-01',
  devtools: { enabled: false },
  typescript: { strict: true },

  runtimeConfig: {
    // Set with NUXT_DATABASE_URL. On Cloudflare, a Hyperdrive binding named HYPERDRIVE wins.
    databaseUrl: '',
  },

  css: [
    '@fontsource/big-shoulders-display/700',
    '@fontsource/big-shoulders-display/900',
    '@fontsource-variable/newsreader/opsz',
    '@fontsource-variable/newsreader/opsz-italic',
    '@fontsource/ibm-plex-mono/400',
    '@fontsource/ibm-plex-mono/500',
    '@fontsource/ibm-plex-mono/600',
    '~/assets/styles/tokens.css',
    '~/assets/styles/base.css',
  ],

  app: {
    head: {
      htmlAttrs: { lang: 'en' },
      titleTemplate: '%s · Baller Knowledge',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
        { name: 'description', content: 'NBA players, teams, comparisons, records and awards, set in print.' },
      ],
      link: [{ rel: 'icon', type: 'image/svg+xml', href: '/favicon.svg' }],
    },
  },
})
