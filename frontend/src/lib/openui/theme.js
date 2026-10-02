import { onBeforeUnmount, onMounted, ref } from 'vue'
import tokens from 'elastic-ui/tokens.css?raw'

// The app's look for what a page draws outside the app's own DOM: a Diagram's SVG (an image)
// and an Artifact (a sandboxed iframe). Neither can read the page's CSS, so they get the
// elastic-ui tokens as they stand in the current theme, resolved to plain values, and the
// library's diagram classes, as one stylesheet.

const NAMES = [
  ...new Set([...tokens.matchAll(/^\s*(--(?:color|font|radius)-[a-z0-9-]+)\s*:/gm)].map((m) => m[1])),
]

// The library's diagram utilities (tokens.css, USAGE 10) as plain CSS, for the SVG and the iframe.
const DIAGRAM = `
.diagram-part { fill: color-mix(in oklab, var(--diagram-color, var(--color-accent)) 14%, var(--color-bg)); stroke: none; rx: var(--radius-md); ry: var(--radius-md); }
.diagram-label { fill: color-mix(in oklab, var(--diagram-color, var(--color-accent)) 75%, var(--color-fg)); font-size: 13px; font-weight: 600; }
.diagram-text { fill: var(--color-fg-secondary); font-size: 12px; }
.diagram-line { fill: none; stroke: var(--color-border-strong); stroke-width: 1; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }
.diagram-quiet { fill: none; stroke: var(--color-fg-faint); stroke-width: 1; stroke-dasharray: 4 4; stroke-linecap: round; vector-effect: non-scaling-stroke; }
.diagram-emphasis { fill: none; stroke: var(--diagram-color, var(--color-accent)); stroke-width: 2.75; stroke-linecap: round; stroke-linejoin: round; vector-effect: non-scaling-stroke; }
.diagram-grid { fill: none; stroke: var(--color-border); stroke-width: 0.75; stroke-dasharray: 2 6; vector-effect: non-scaling-stroke; }
.diagram-area { display: flex; flex-direction: column; gap: 0.75rem; padding: 0.9rem 1rem 1rem; border-radius: var(--radius-xl); background: color-mix(in oklab, var(--diagram-color, var(--color-accent)) 10%, var(--color-bg)); color: color-mix(in oklab, var(--diagram-color, var(--color-accent)) 75%, var(--color-fg)); }
.diagram-chip { display: inline-flex; align-items: center; gap: 0.4em; padding: 0.45em 0.75em; border-radius: var(--radius-md); background: color-mix(in oklab, var(--diagram-color, var(--color-accent)) 14%, var(--color-bg)); color: color-mix(in oklab, var(--diagram-color, var(--color-accent)) 75%, var(--color-fg)); font-size: 0.875rem; font-weight: 600; }
`

// Plain elements in the app's type and controls, so a piece looks native without a class.
const BASE = `
html, body { margin: 0; background: var(--color-bg-subtle); color: var(--color-fg); font-family: var(--font-sans); font-size: 14px; line-height: 1.5; }
body { padding: 16px; box-sizing: border-box; }
*, *::before, *::after { box-sizing: border-box; }
code, pre, kbd { font-family: var(--font-mono); font-size: 0.8125em; }
button { font: inherit; font-weight: 500; border: 0; border-radius: var(--radius-md); padding: 0.4rem 0.8rem; background: var(--color-accent); color: var(--color-accent-fg); cursor: pointer; }
button:hover { background: var(--color-accent-hover); }
button:disabled { opacity: 0.5; cursor: default; }
input, select, textarea { font: inherit; color: inherit; background: var(--color-bg); border: 1px solid var(--color-border); border-radius: var(--radius-md); padding: 0.35rem 0.6rem; }
input[type="range"], input[type="checkbox"], input[type="radio"] { accent-color: var(--color-accent); padding: 0; }
`

function isDark() {
  const forced = document.documentElement.dataset.theme
  if (forced === 'dark' || forced === 'light') return forced === 'dark'
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

/** The tokens as `--name: value;` declarations, resolved in the current theme. */
function variables() {
  const style = getComputedStyle(document.documentElement)
  // Colours hold both themes in light-dark(): read through an element, they come out resolved.
  const probe = document.createElement('span')
  probe.style.display = 'none'
  document.body.append(probe)
  const out = NAMES.map((name) => {
    let value = style.getPropertyValue(name).trim()
    if (name.startsWith('--color-')) {
      probe.style.color = `var(${name})`
      value = getComputedStyle(probe).color
    }
    return value ? `${name}: ${value};` : ''
  })
  probe.remove()
  return out.join(' ')
}

function build() {
  const dark = isDark()
  const vars = variables()
  return {
    dark,
    // For an Artifact's document.
    html: `:root { ${vars} color-scheme: ${dark ? 'dark' : 'light'}; }${BASE}${DIAGRAM}`,
    // For a Diagram's SVG, whose root is the <svg>.
    svg: `:root { ${vars} color: var(--color-fg); font-family: var(--font-sans); }${DIAGRAM}`,
  }
}

/** The theme's stylesheets, rebuilt when the theme changes (ThemeToggle or the system). */
export function useThemeCss() {
  const css = ref(null)
  let observer
  let media
  const update = () => requestAnimationFrame(() => (css.value = build()))
  onMounted(() => {
    css.value = build()
    observer = new MutationObserver(update)
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
    media = window.matchMedia('(prefers-color-scheme: dark)')
    media.addEventListener('change', update)
  })
  onBeforeUnmount(() => {
    observer?.disconnect()
    media?.removeEventListener('change', update)
  })
  return css
}

// No network from an Artifact: only its own inline code and data URLs.
const CSP =
  "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data: blob:; font-src data:; media-src data: blob:"

/** An Artifact's document with the theme and the no-network policy first in its head. */
export function themedDocument(html, css) {
  const head = `<meta http-equiv="Content-Security-Policy" content="${CSP}"><style>${css}</style>`
  if (/<head[^>]*>/i.test(html)) return html.replace(/<head[^>]*>/i, (tag) => tag + head)
  if (/<html[^>]*>/i.test(html)) return html.replace(/<html[^>]*>/i, (tag) => `${tag}<head>${head}</head>`)
  return `<!doctype html><html><head>${head}</head><body>${html}</body></html>`
}

/** An SVG with the theme's stylesheet just inside its root element. */
export function themedSvg(svg, css) {
  return svg.replace(/<svg\b[^>]*>/i, (tag) => `${tag}<style>${css}</style>`)
}
