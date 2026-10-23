<script setup lang="ts">
import type { Column } from '~/components/StatTable.vue'
import type { Series } from '~/components/charts/LineChart.vue'

useHead({ title: 'Styleguide' })

const { edition } = useEdition()

/* ---- 02 Color ------------------------------------------------------------ */

const swatches = [
  { token: '--color-paper', name: 'Paper', role: 'Page background' },
  { token: '--color-paper-alt', name: 'Paper, pressed', role: 'Row hover, insets' },
  { token: '--color-ink', name: 'Ink', role: 'Text, rules, chart lines' },
  { token: '--color-ink-muted', name: 'Ink, muted', role: 'Labels, axes, captions' },
  { token: '--color-rule-faint', name: 'Rule, faint', role: 'Row dividers, gridlines' },
  { token: '--color-spot', name: 'Hardwood', role: 'The one thing that matters' },
  { token: '--color-spot-text', name: 'Hardwood, text', role: 'Spot color at small sizes' },
  { token: '--color-secondary', name: 'Slate', role: 'Muted second series' },
]

const measured = ref<Record<string, { hex: string; ratio: number | null }>>({})

function measure() {
  const style = getComputedStyle(document.documentElement)
  const probe = document.createElement('span')
  document.body.appendChild(probe)
  const resolve = (token: string) => {
    probe.style.color = `var(${token})`
    return getComputedStyle(probe).color
  }
  const paper = resolve('--color-paper')
  const out: typeof measured.value = {}
  for (const s of swatches) {
    const value = resolve(s.token)
    out[s.token] = { hex: toHex(value), ratio: s.token === '--color-paper' ? null : contrastRatio(value, paper) }
  }
  probe.remove()
  void style
  measured.value = out
}

onMounted(() => {
  measure()
  // Wait a frame after an edition change so the new tokens are applied.
  watch(edition, () => requestAnimationFrame(measure))
})

function grade(r: number | null | undefined) {
  if (r == null) return ''
  if (r >= 7) return 'AAA'
  if (r >= 4.5) return 'AA'
  if (r >= 3) return 'AA large'
  return 'Decorative'
}

/* ---- 05 Table: specimen game log (fictional) ----------------------------- */

const columns: Column[] = [
  { key: 'date', label: 'Date', sortable: true },
  { key: 'opp', label: 'Opp', title: 'Opponent' },
  { key: 'res', label: 'W/L', title: 'Result' },
  { key: 'min', label: 'Min', title: 'Minutes', numeric: true, sortable: true },
  { key: 'pts', label: 'Pts', title: 'Points', numeric: true, sortable: true },
  { key: 'reb', label: 'Reb', title: 'Rebounds', numeric: true, sortable: true },
  { key: 'ast', label: 'Ast', title: 'Assists', numeric: true, sortable: true },
  { key: 'fg', label: 'FG%', title: 'Field goal percentage', numeric: true, decimals: 1, sortable: true },
  { key: 'tp', label: '3P%', title: 'Three-point percentage', numeric: true, decimals: 1, sortable: true },
  { key: 'pm', label: '+/−', title: 'Plus-minus', numeric: true, sortable: true },
]

const rows = [
  { date: '2026-10-21', opp: 'vs HAR', res: 'W 118–104', min: 36, pts: 41, reb: 7, ast: 9, fg: 56.5, tp: 45.5, pm: 14 },
  { date: '2026-10-19', opp: '@ PRT', res: 'L 99–107', min: 38, pts: 22, reb: 5, ast: 11, fg: 40.9, tp: 28.6, pm: -6 },
  { date: '2026-10-17', opp: 'vs SLT', res: 'W 125–111', min: 33, pts: 30, reb: 8, ast: 6, fg: 52.2, tp: 40.0, pm: 11 },
  { date: '2026-10-15', opp: '@ MER', res: 'W 102–98', min: 40, pts: 27, reb: 12, ast: 4, fg: 45.0, tp: 33.3, pm: 3 },
  { date: '2026-10-13', opp: 'vs CAP', res: 'L 110–115', min: 37, pts: 35, reb: 6, ast: 8, fg: 50.0, tp: 37.5, pm: -2 },
  { date: '2026-10-11', opp: '@ BAY', res: 'W 121–93', min: 28, pts: 19, reb: 4, ast: 10, fg: 61.5, tp: 50.0, pm: 22 },
]

/* ---- 06 Chart: specimen career arc (fictional) --------------------------- */

const arc = (start: number, ys: number[]) => ys.map((y, i) => ({ x: start + i, y }))

const series: Series[] = [
  { id: 'okafor', label: 'J. Okafor-Reyes', emphasis: true, points: arc(2017, [11.2, 15.8, 19.4, 22.1, 24.9, 26.3, 25.7, 28.4, 30.1, 31.6]) },
  { id: 'lindqvist', label: 'M. Lindqvist', points: arc(2015, [8.4, 12.6, 17.9, 21.3, 23.0, 22.4, 24.8, 23.1, 20.6, 19.2, 17.5, 16.8]) },
  { id: 'baptiste', label: 'D. Baptiste', points: arc(2019, [14.1, 18.0, 17.2, 20.5, 22.9, 21.8, 24.0, 23.4]) },
]

const seasonLabel = (y: number) => `’${String(y).slice(2)}`

/* ---- Motion ------------------------------------------------------------- */

const motionRoot = ref<HTMLElement | null>(null)
useReveal(motionRoot, 60)

const asOf = useState('bk-styleguide-asof', () => new Date().toISOString())
</script>

<template>
  <article class="sg">
    <header class="sg__intro grid">
      <p class="kicker sg__intro-kicker">Section 00 / House style</p>
      <h1 class="display sg__title">The<br />Style<br /><span class="spot">Guide</span></h1>
      <div class="sg__intro-text">
        <p class="lede">
          Baller Knowledge is a printed program for the NBA. The page is paper and the content is ink. Type
          does most of the work, rules hold the grid, and one spot color marks the number that matters.
        </p>
        <p class="label">Every value on this page comes from <code>assets/styles/tokens.css</code>.</p>
      </div>
    </header>

    <!-- 01 TYPE ---------------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-type">
      <header class="sg__rail">
        <p class="kicker spot-text">01</p>
        <h2 id="sg-type" class="display sg__h2">Type</h2>
        <p class="label">Three faces, three jobs.</p>
      </header>
      <div class="sg__body">
        <div class="specimen">
          <p class="label specimen__meta">Display · Big Shoulders Display 900 · --font-display</p>
          <p class="display specimen__display">Forty-one and nine</p>
        </div>
        <div class="specimen specimen--split">
          <div>
            <p class="label specimen__meta">Body · Newsreader · --font-body</p>
            <p class="specimen__body">
              He took the inbound at the left elbow with four seconds on the clock, turned once, and let it go
              over two defenders. The building went quiet before it went loud. It was his third forty-point
              night in a week, and the first time anyone in the league had done that since the spring.
            </p>
            <p class="specimen__body"><em>Italic, for asides and the occasional editorial voice.</em></p>
          </div>
          <div>
            <p class="label specimen__meta">Numbers · IBM Plex Mono · --font-mono, tabular</p>
            <ol class="specimen__nums num">
              <li><span>1</span><span>J. Okafor-Reyes</span><span>31.6</span></li>
              <li><span>2</span><span>D. Baptiste</span><span>24.0</span></li>
              <li><span>3</span><span>M. Lindqvist</span><span>19.2</span></li>
              <li><span>4</span><span>T. Abernathy</span><span>18.7</span></li>
              <li><span>10</span><span>K. Mwangi-Hart</span><span>11.1</span></li>
            </ol>
          </div>
        </div>
        <table class="scale">
          <caption class="visually-hidden">Type scale</caption>
          <tbody>
            <tr v-for="t in ['mega', '4xl', '3xl', '2xl', 'xl']" :key="t">
              <th scope="row" class="label">--text-{{ t }}</th>
              <td><span class="display" :style="{ fontSize: `var(--text-${t})` }">Ledger</span></td>
            </tr>
            <tr v-for="t in ['lg', 'base', 'sm', 'xs', '2xs']" :key="t">
              <th scope="row" class="label">--text-{{ t }}</th>
              <td><span :style="{ fontSize: `var(--text-${t})` }">Points, rebounds and assists per game</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <!-- 02 COLOR --------------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-color">
      <header class="sg__rail">
        <p class="kicker spot-text">02</p>
        <h2 id="sg-color" class="display sg__h2">Color</h2>
        <p class="label">
          Flat only. Now showing the <ClientOnly fallback="current">{{ edition }}</ClientOnly> edition; switch it at
          the top of the page. Ratios are measured against paper.
        </p>
      </header>
      <div class="sg__body">
        <ul class="swatches">
          <li v-for="s in swatches" :key="s.token" class="swatch">
            <span class="swatch__chip" :style="{ background: `var(${s.token})` }" />
            <span class="swatch__name">{{ s.name }}</span>
            <span class="label swatch__role">{{ s.role }}</span>
            <code class="num swatch__token">{{ s.token }}</code>
            <span class="num swatch__hex">{{ measured[s.token]?.hex ?? '—' }}</span>
            <span class="num swatch__ratio">
              <template v-if="measured[s.token]?.ratio">
                {{ measured[s.token]!.ratio!.toFixed(2) }}:1 <span class="label">{{ grade(measured[s.token]!.ratio) }}</span>
              </template>
              <template v-else>&nbsp;</template>
            </span>
          </li>
        </ul>
        <div class="team-accent">
          <p class="label">Team colors: a small flat accent, never a background behind text.</p>
          <p class="team-accent__row">
            <span class="team-accent__bar" style="--team: #1d428a" aria-hidden="true" />
            <span class="display team-accent__name">Harbor City</span>
            <span class="num label">HAR · 31–12 · 1st West</span>
          </p>
        </div>
      </div>
    </section>

    <!-- 03 RULES & GRID -------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-rules">
      <header class="sg__rail">
        <p class="kicker spot-text">03</p>
        <h2 id="sg-rules" class="display sg__h2">Rules &amp; grid</h2>
        <p class="label">Depth comes from rules and contrast. No shadows, no rounded cards.</p>
      </header>
      <div class="sg__body">
        <dl class="rules">
          <div><dt class="label">Hairline · 1px</dt><dd><hr class="rule" /></dd></div>
          <div><dt class="label">Faint hairline</dt><dd><hr class="rule rule--faint" /></dd></div>
          <div><dt class="label">Heavy · 3px</dt><dd><hr class="rule rule--heavy" /></dd></div>
          <div><dt class="label">Double · masthead</dt><dd><hr class="rule rule--double" /></dd></div>
        </dl>
        <div class="gridshow" aria-hidden="true">
          <span v-for="n in 12" :key="n" class="num">{{ n }}</span>
        </div>
        <p class="label">12 columns, fluid gutter, wide margins. Big numbers may break out of the grid.</p>
      </div>
    </section>

    <!-- 04 NUMBERS ------------------------------------------------------- -->
    <section class="sg__section grid sg__section--numbers" aria-labelledby="sg-numbers">
      <header class="sg__rail">
        <p class="kicker spot-text">04</p>
        <h2 id="sg-numbers" class="display sg__h2">The big number</h2>
        <p class="label">One stat, one number, set huge. Ticks up the first time it scrolls into view.</p>
      </header>
      <div class="sg__body numbers">
        <BigNumber :value="41" label="Points, Oct 21 vs Harbor City" spot />
        <div class="numbers__side">
          <BigNumber :value="56.5" :decimals="1" suffix="%" label="Field goal pct" />
          <p class="specimen__body">
            A featured stat story pairs one big number with a sentence of context and a single chart. Nothing
            else competes for attention.
          </p>
        </div>
      </div>
    </section>

    <!-- 05 TABLE --------------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-table">
      <header class="sg__rail">
        <p class="kicker spot-text">05</p>
        <h2 id="sg-table" class="display sg__h2">Box score</h2>
        <p class="label">
          Mono, tabular figures, numbers right-aligned. Sort any stat column by clicking or pressing Enter on
          its header.
        </p>
      </header>
      <div class="sg__body">
        <h3 class="kicker sg__h3">Game log · J. Okafor-Reyes · Last 6</h3>
        <StatTable
          :columns="columns"
          :rows="rows"
          caption="Specimen game log for a fictional player, last six games"
          :highlight="(r) => r.pts >= 40"
          :initial-sort="{ key: 'date', dir: 'desc' }"
        />
        <SourceLine source="Specimen data, fictional players" :as-of="asOf" />
      </div>
    </section>

    <!-- 06 CHART --------------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-chart">
      <header class="sg__rail">
        <p class="kicker spot-text">06</p>
        <h2 id="sg-chart" class="display sg__h2">Charts</h2>
        <p class="label">
          Drawn, not generated. Thin ink lines, direct labels instead of a legend, the spot color for the one
          series that matters. Every chart has a data table behind it.
        </p>
      </header>
      <div class="sg__body">
        <h3 class="kicker sg__h3">Career arc · points per game</h3>
        <ChartsLineChart
          :series="series"
          title="Career points per game, three fictional players"
          x-label="Season"
          y-label="Points per game"
          :format-x="seasonLabel"
        />
        <SourceLine source="Specimen data, fictional players" :as-of="asOf" />
      </div>
    </section>

    <!-- 07 TEXTURE ------------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-texture">
      <header class="sg__rail">
        <p class="kicker spot-text">07</p>
        <h2 id="sg-texture" class="display sg__h2">Texture</h2>
        <p class="label">Halftone, court lines and paper grain. Subtle, flat, and never under body text.</p>
      </header>
      <div class="sg__body textures">
        <figure class="texture">
          <div class="texture__plate halftone" />
          <figcaption class="label">Halftone · spot</figcaption>
        </figure>
        <figure class="texture">
          <div class="texture__plate halftone--ink texture__plate--ink" />
          <figcaption class="label">Halftone · ink</figcaption>
        </figure>
        <figure class="texture texture--court">
          <CourtLines class="texture__court" />
          <figcaption class="label">Court lines · half court, to scale</figcaption>
        </figure>
      </div>
    </section>

    <!-- 08 MOTION -------------------------------------------------------- -->
    <section class="sg__section grid" aria-labelledby="sg-motion">
      <header class="sg__rail">
        <p class="kicker spot-text">08</p>
        <h2 id="sg-motion" class="display sg__h2">Motion</h2>
        <p class="label">Small and deliberate. All of it turns off with reduced motion.</p>
      </header>
      <div ref="motionRoot" class="sg__body">
        <ul class="motion">
          <li class="reveal"><span class="num">01</span> Numbers tick up on first view.</li>
          <li class="reveal"><span class="num">02</span> Rows slide in, a few at a time.</li>
          <li class="reveal"><span class="num">03</span> Chart lines draw on once.</li>
          <li class="reveal"><span class="num">04</span> <a href="#sg-motion">Links thicken their underline on hover.</a></li>
        </ul>
      </div>
    </section>
  </article>
</template>

<style scoped>
.sg__intro {
  padding-block: var(--space-7) var(--space-8);
  row-gap: var(--space-5);
  align-items: end;
}

.sg__intro-kicker {
  grid-column: 1 / -1;
}

.sg__title {
  grid-column: 1 / span 7;
  font-size: var(--text-mega);
  line-height: 0.78;
}

.sg__intro-text {
  grid-column: 8 / -1;
  display: grid;
  gap: var(--space-4);
  padding-top: var(--space-3);
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.spot-text {
  color: var(--color-spot-text);
}

code {
  font-family: var(--font-mono);
  font-size: 0.95em;
}

.sg__section {
  padding-block: var(--space-6) var(--space-8);
  border-top: var(--rule-hair) solid var(--color-rule);
  row-gap: var(--space-5);
}

.sg__rail {
  grid-column: 1 / span 3;
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
  align-self: start;
  position: sticky;
  top: var(--space-4);
}

.sg__h2 {
  font-size: var(--text-2xl);
}

.sg__h3 {
  margin-bottom: var(--space-3);
}

.sg__body {
  grid-column: 4 / -1;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: var(--space-6);
  min-width: 0;
}

/* Type */
.specimen__meta {
  margin-bottom: var(--space-2);
}

.specimen__display {
  font-size: var(--text-4xl);
}

.specimen--split {
  display: grid;
  grid-template-columns: 3fr 2fr;
  gap: var(--grid-gutter);
}

.specimen__body {
  max-width: var(--measure);
}

.specimen__body + .specimen__body {
  margin-top: var(--space-3);
}

.specimen__nums {
  list-style: none;
  padding: 0;
  border-top: var(--rule-heavy) solid var(--color-rule);
  font-size: var(--text-sm);
}

.specimen__nums li {
  display: grid;
  grid-template-columns: 2.5ch 1fr auto;
  gap: var(--space-3);
  padding-block: var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.specimen__nums li:first-child span:last-child {
  color: var(--color-spot-text);
  font-weight: 600;
}

.specimen__nums li span:first-child {
  color: var(--color-ink-muted);
  text-align: right;
}

.scale {
  border-collapse: collapse;
  width: 100%;
}

.scale th,
.scale td {
  padding-block: var(--space-2);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
  text-align: left;
  vertical-align: baseline;
}

.scale th {
  width: 9rem;
  font-weight: 500;
}

.scale td {
  overflow: hidden;
  white-space: nowrap;
  max-width: 0;
  text-overflow: clip;
}

/* Color */
.swatches {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 10rem), 1fr));
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.swatch {
  display: grid;
  gap: var(--space-1);
  padding: var(--space-3) var(--space-3) var(--space-4) 0;
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
}

.swatch__chip {
  height: 4.5rem;
  margin-bottom: var(--space-2);
  border: var(--rule-hair) solid var(--color-rule);
}

.swatch__name {
  font-family: var(--font-display);
  font-weight: var(--weight-display-light);
  font-size: var(--text-xl);
  text-transform: uppercase;
  line-height: 1;
}

.swatch__token,
.swatch__hex,
.swatch__ratio {
  font-size: var(--text-xs);
}

.swatch__role {
  font-size: var(--text-2xs);
}

.team-accent {
  display: grid;
  gap: var(--space-3);
}

.team-accent__row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--space-3);
}

.team-accent__bar {
  width: var(--space-2);
  height: 2.5rem;
  background: var(--team);
}

.team-accent__name {
  font-size: var(--text-2xl);
}

/* Rules */
.rules {
  display: grid;
  gap: var(--space-4);
}

.rules > div {
  display: grid;
  grid-template-columns: 11rem 1fr;
  align-items: center;
  gap: var(--space-4);
}

.gridshow {
  display: grid;
  grid-template-columns: repeat(12, 1fr);
  gap: var(--grid-gutter);
  height: 6rem;
}

.gridshow span {
  display: flex;
  align-items: flex-end;
  padding: var(--space-1);
  font-size: var(--text-2xs);
  color: var(--color-ink-muted);
  border-left: var(--rule-hair) solid var(--color-rule);
  border-right: var(--rule-hair) solid var(--color-rule-faint);
}

/* Numbers: the big one is allowed to break the grid, rising through the section rule. */
.numbers {
  grid-template-columns: auto 1fr;
  align-items: end;
  gap: var(--space-7);
  margin-top: calc(-1 * var(--space-8));
}

.numbers__side {
  display: grid;
  gap: var(--space-5);
}

.numbers__side :deep(.big__value) {
  font-size: var(--text-3xl);
}

/* Texture */
.textures {
  grid-template-columns: repeat(3, 1fr);
}

.texture {
  display: grid;
  gap: var(--space-2);
}

.texture__plate {
  aspect-ratio: 1;
  border: var(--rule-hair) solid var(--color-rule);
}

.texture__plate--ink {
  opacity: 0.35;
}

.texture--court {
  color: var(--color-ink);
}

.texture__court {
  width: 100%;
  aspect-ratio: 52 / 49;
}

/* Motion */
.motion {
  list-style: none;
  padding: 0;
  border-top: var(--rule-heavy) solid var(--color-rule);
}

.motion li {
  display: flex;
  gap: var(--space-4);
  padding-block: var(--space-3);
  border-bottom: var(--rule-hair) solid var(--color-rule-faint);
  font-size: var(--text-lg);
}

.motion .num {
  color: var(--color-spot-text);
  font-size: var(--text-sm);
  padding-top: 0.2em;
}

@media (max-width: 960px) {
  .sg__rail,
  .sg__body,
  .sg__title,
  .sg__intro-text {
    grid-column: 1 / -1;
  }

  .sg__rail {
    position: static;
  }

  .numbers {
    margin-top: 0;
  }
}

@media (max-width: 640px) {
  .specimen--split,
  .numbers,
  .textures {
    grid-template-columns: 1fr;
  }

  .rules > div {
    grid-template-columns: 1fr;
    gap: var(--space-2);
  }

  .gridshow {
    gap: var(--space-1);
  }
}
</style>
