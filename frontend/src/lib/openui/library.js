import { h } from 'vue'
import {
  Callout,
  CodeBlock,
  Diagram,
  Markdown,
  Prose,
  Steps,
  StepsItem,
  slugify,
} from 'elastic-ui'
import { createParser } from '@openuidev/vue-lang'
import { buildLibrary, ROOT } from './catalog.js'

// The page catalogue drawn with elastic-ui. Every renderer gets the parsed `props` and a
// `renderNode` for its children; both are declared so Vue does not pass them on as attributes.
// Props can be partial while a page streams, so each one reads them defensively.

const declared = ['props', 'renderNode']

function renderer(render) {
  return { props: declared, setup: (p) => () => render(p.props ?? {}, p.renderNode) }
}

// A Markdown block that flows in the page's own Prose instead of opening a second article.
const markdown = (source) => h(Markdown, { source: source ?? '', class: 'contents' })

const DEFAULT_ARTIFACT_HEIGHT = 360

const renderers = {
  Page: renderer((props, renderNode) => h(Prose, null, () => renderNode(props.blocks ?? []))),

  Heading: renderer(({ text = '', level }) =>
    h(level === 3 ? 'h3' : 'h2', { id: slugify(text) }, text),
  ),

  Text: renderer(({ markdown: source }) => markdown(source)),

  CodeBlock: renderer(({ code = '', language, title }) =>
    h(CodeBlock, { code, language, title }),
  ),

  Callout: renderer(({ type = 'note', text, title }) =>
    h(Callout, { type, title }, () => markdown(text)),
  ),

  Steps: renderer(({ items }, renderNode) =>
    h(Steps, { static: true }, () => renderNode(items ?? [])),
  ),

  StepItem: renderer(({ title, text }) => h(StepsItem, { title }, () => markdown(text))),

  // Drawn as an image, so the SVG cannot run scripts or reach the page.
  Diagram: renderer(({ label = '', svg = '', caption }) =>
    h(Diagram, { label, caption }, () =>
      h('img', {
        src: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(svg)}`,
        alt: '',
        class: 'block h-auto w-full',
      }),
    ),
  ),

  // The escape hatch: the model's own HTML in a sandboxed iframe. Scripts run, but without
  // `allow-same-origin` the frame has no access to the app, its cookies or its storage.
  Artifact: renderer(({ title = '', html = '', height }) =>
    h('iframe', {
      title,
      srcdoc: html,
      sandbox: 'allow-scripts',
      referrerpolicy: 'no-referrer',
      loading: 'lazy',
      class: 'block w-full rounded-md border-0 bg-bg-subtle',
      style: { height: `${Number(height) > 0 ? Number(height) : DEFAULT_ARTIFACT_HEIGHT}px` },
    }),
  ),
}

export const pageLibrary = buildLibrary(renderers)

const parser = createParser(pageLibrary.toJSONSchema(), ROOT)

/**
 * Whether `source` is a page the renderer can draw: it parses, and its root is a Page.
 * The parser never throws and renders what it can, so a source with no usable root is
 * what counts as a failure here, and the page falls back to its Markdown.
 */
export function canRender(source) {
  if (!source?.trim()) return false
  try {
    const result = parser.parse(source)
    return result?.root?.typeName === ROOT
  } catch {
    return false
  }
}
