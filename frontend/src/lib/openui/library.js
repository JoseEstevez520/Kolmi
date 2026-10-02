import { computed, h, inject, provide } from 'vue'
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
  AgentReplay,
  Callout,
  Card,
  CardDescription,
  CardHeader,
  CardImage,
  CardTitle,
  ChatMessage,
  CodeBlock,
  CodeDiff,
  DescriptionItem,
  DescriptionList,
  Diagram,
  Markdown,
  Prose,
  Steps,
  StepsItem,
  TerminalReplay,
  slugify,
} from 'elastic-ui'
import { ArrowUpRight } from '@lucide/vue'
import { createParser } from '@openuidev/vue-lang'
import { buildLibrary, ROOT } from './catalog.js'
import { COLOR_VALUES } from './colors.js'
import { iconFor } from './icons.js'
import { logoFor } from './logos.js'
import { themedDocument, themedSvg, useThemeCss } from './theme.js'

// The page catalogue drawn with elastic-ui. Every renderer gets the parsed `props` and a
// `renderNode` for its children; both are declared so Vue does not pass them on as attributes.
// Props can be partial while a page streams, so each one reads them defensively.

const declared = ['props', 'renderNode']

function renderer(render) {
  return { props: declared, setup: (p) => () => render(p.props ?? {}, p.renderNode) }
}

// A renderer with a setup of its own (provide/inject, the theme), returning the render function.
function stateful(setup) {
  return { props: declared, setup: (p) => setup(p) }
}

// A Markdown block that flows in the page's own Prose instead of opening a second article.
const markdown = (source) => h(Markdown, { source: source ?? '', class: 'contents' })

// A child component's props, read as data (a session's events, a terminal's entries).
const propsOf = (node) => node?.props ?? {}
const list = (value) => (Array.isArray(value) ? value : [])

const DEFAULT_ARTIFACT_HEIGHT = 360

// -- figures ---------------------------------------------------------------------------------

const LAYOUT = Symbol('figure layout')
const colorStyle = (color) => (COLOR_VALUES[color] ? { '--diagram-color': COLOR_VALUES[color] } : undefined)
const iconNode = (name, size = 'size-4') => {
  const icon = iconFor(name)
  return icon ? h(icon, { class: `${size} shrink-0`, 'stroke-width': 1.5, 'aria-hidden': 'true' }) : null
}

// How a figure's or a group's parts sit: a row turns into a column on a phone.
const OUTER = {
  row: 'flex flex-col items-stretch gap-3 sm:flex-row sm:items-center',
  column: 'flex flex-col items-stretch gap-2',
  grid: 'grid gap-3 sm:grid-cols-2',
}
// Inside an Area, its chips and labels.
const INNER = {
  column: 'flex flex-col items-stretch gap-2',
  row: 'flex flex-wrap gap-1.5',
  grid: 'grid grid-cols-2 gap-x-4 gap-y-2 sm:grid-cols-3',
}
const layoutOf = (value, fallback) => (value === 'row' || value === 'column' || value === 'grid' ? value : fallback)

// -- cards and logos -------------------------------------------------------------------------

function card({ title = '', text, href, image }) {
  const body = h(Card, { size: 'sm', class: href ? 'h-full transition-colors duration-150 group-hover:border-border-strong' : 'h-full' }, () => [
    image ? h(CardImage, { src: image, alt: title, fade: true, class: 'aspect-video' }) : null,
    h(CardHeader, { class: 'gap-1' }, () => [
      h(CardTitle, { as: 'h3', class: 'flex items-center justify-between gap-2' }, () => [
        title,
        href ? h(ArrowUpRight, { class: 'size-4 shrink-0 text-fg-faint transition-colors duration-150 group-hover:text-fg', 'aria-hidden': 'true' }) : null,
      ]),
      text ? h(CardDescription, null, () => text) : null,
    ]),
  ])
  if (!href) return body
  return h(
    'a',
    {
      href,
      target: '_blank',
      rel: 'noopener noreferrer',
      class: 'group block h-full rounded-[var(--radius-xl)] focus-visible:outline-2 focus-visible:outline-accent',
    },
    [body],
  )
}

function logo(icon) {
  return h('svg', { width: 18, height: 18, viewBox: '0 0 24 24', fill: 'currentColor', 'aria-hidden': 'true' }, [
    h('path', { d: icon.path }),
  ])
}

// A table as Markdown, so it is the library's own: as wide as the text, scrolling sideways.
function tableMarkdown(columns, rows) {
  const cell = (value) => String(value ?? '').replace(/\|/g, '\\|').replace(/\n/g, ' ')
  const line = (cells) => `| ${cells.map(cell).join(' | ')} |`
  return [line(columns), line(columns.map(() => '---')), ...rows.map((row) => line(columns.map((_, i) => list(row)[i])))].join('\n')
}

// -- the renderers ---------------------------------------------------------------------------

const renderers = {
  Page: renderer((props, renderNode) => h(Prose, null, () => renderNode(props.blocks ?? []))),

  Heading: renderer(({ text = '', level }) =>
    h(level === 3 ? 'h3' : 'h2', { id: slugify(text) }, text),
  ),

  Text: renderer(({ markdown: source }) => markdown(source)),

  CodeBlock: renderer(({ code = '', language, title }) =>
    h(CodeBlock, { code, language, title }),
  ),

  CodeDiff: renderer(({ before = '', after = '', file }) => h(CodeDiff, { before, after, file })),

  Callout: renderer(({ type = 'note', text, title }) =>
    h(Callout, { type, title }, () => markdown(text)),
  ),

  Steps: renderer(({ items }, renderNode) =>
    h(Steps, { static: true }, () => renderNode(items ?? [])),
  ),

  StepItem: renderer(({ title, text }) => h(StepsItem, { title }, () => markdown(text))),

  Table: renderer(({ columns, rows, caption }) => {
    const cols = list(columns)
    if (!cols.length) return null
    const table = markdown(tableMarkdown(cols, list(rows)))
    return caption ? h('figure', null, [table, h('figcaption', null, caption)]) : table
  }),

  DescriptionList: renderer(({ items }, renderNode) =>
    h(DescriptionList, { divided: true, class: 'not-prose' }, () => renderNode(items ?? [])),
  ),

  DescriptionItem: renderer(({ term, text }) =>
    h(DescriptionItem, { term }, () => h(Markdown, { source: text ?? '', class: 'text-fg-secondary [&_p]:m-0' })),
  ),

  Accordion: renderer(({ items }) =>
    h(Accordion, { type: 'multiple' }, () =>
      list(items).map((item, i) => {
        const { title = '', text } = propsOf(item)
        return h(AccordionItem, { value: String(i), key: i }, () => [
          h(AccordionTrigger, null, () => title),
          h(AccordionContent, null, () => markdown(text)),
        ])
      }),
    ),
  ),
  AccordionItem: renderer(() => null),

  Cards: renderer(({ items }) =>
    h('div', { class: 'not-prose grid gap-4 sm:grid-cols-2' }, list(items).map((item) => card(propsOf(item)))),
  ),
  Card: renderer((props) => card(props)),

  Logos: renderer(({ names }) =>
    h(
      'ul',
      { class: 'not-prose flex flex-wrap gap-2' },
      list(names).map((name) => {
        const icon = logoFor(name)
        return h('li', { class: 'flex items-center gap-2 rounded-[var(--radius-lg)] bg-bg-subtle px-3 py-1.5' }, [
          icon ? logo(icon) : null,
          h('span', { class: 'text-sm text-fg-secondary' }, String(name)),
        ])
      }),
    ),
  ),

  TerminalReplay: renderer(({ entries, title }) => {
    const rows = list(entries)
      .map(propsOf)
      .filter((entry) => entry.command)
      .map(({ command, output, comment }) => ({ command, output, comment }))
    return rows.length ? h(TerminalReplay, { entries: rows, title }) : null
  }),
  TerminalEntry: renderer(() => null),

  AgentReplay: renderer(({ events }) => {
    const out = list(events).flatMap((node) => {
      const p = propsOf(node)
      if (node?.typeName === 'AgentPrompt' && p.text) return [{ kind: 'prompt', text: p.text, note: p.note }]
      if (node?.typeName === 'AgentAnswer' && p.text) {
        return [{ kind: 'answer', text: p.text, note: p.note, code: p.code ? { code: p.code } : undefined }]
      }
      if (node?.typeName === 'AgentStep' && p.running) {
        return [
          {
            kind: 'step',
            running: p.running,
            done: p.done || p.running,
            icon: iconFor(p.icon),
            output: p.output,
            note: p.note,
            permission: p.permission,
            asking: p.permission?.startsWith('ask') ? p.running : undefined,
          },
        ]
      }
      return []
    })
    return out.length ? h(AgentReplay, { events: out }) : null
  }),
  AgentPrompt: renderer(() => null),
  AgentStep: renderer(() => null),
  AgentAnswer: renderer(() => null),

  Chat: renderer(({ messages }, renderNode) =>
    h('div', { class: 'not-prose my-6 flex flex-col gap-6 rounded-[var(--radius-xl)] bg-bg-subtle p-4 sm:p-6' }, renderNode(messages ?? [])),
  ),
  ChatMessage: renderer(({ role, text }) =>
    h(ChatMessage, { role: role === 'user' ? 'user' : 'assistant' }, () =>
      h(Markdown, { source: text ?? '', class: '[&>:first-child]:mt-0 [&>:last-child]:mb-0' }),
    ),
  ),

  // The figure pieces, on elastic-ui's diagram classes. A part knows the layout it sits in,
  // so an arrow points along it and a top-level chip keeps to its own width.
  Figure: stateful((p) => {
    provide(LAYOUT, computed(() => ({ layout: layoutOf(p.props?.layout, 'row'), top: true })))
    return () => {
      const { label = '', parts, layout, caption } = p.props ?? {}
      return h(Diagram, { label, caption, class: 'rounded-[var(--radius-xl)] bg-bg-subtle p-5 sm:p-6' }, () =>
        h('div', { class: OUTER[layoutOf(layout, 'row')] }, p.renderNode(parts ?? [])),
      )
    }
  }),

  Group: stateful((p) => {
    provide(LAYOUT, computed(() => ({ layout: layoutOf(p.props?.layout, 'column'), top: true })))
    return () => h('div', { class: `${OUTER[layoutOf(p.props?.layout, 'column')]} min-w-0 sm:flex-1` }, p.renderNode(p.props?.parts ?? []))
  }),

  Area: stateful((p) => {
    const outer = inject(LAYOUT, null)
    provide(LAYOUT, computed(() => ({ layout: layoutOf(p.props?.layout, 'column'), top: false })))
    return () => {
      const { title = '', parts, color, icon, note, layout } = p.props ?? {}
      const inRow = outer?.value.layout === 'row'
      return h('div', { class: ['diagram-area diagram-in gap-2', inRow && 'min-w-0 sm:flex-1'], style: colorStyle(color) }, [
        h('span', { class: 'flex items-center gap-1.5 text-sm font-semibold' }, [iconNode(icon), title]),
        list(parts).length ? h('div', { class: INNER[layoutOf(layout, 'column')] }, p.renderNode(parts)) : null,
        note ? h('span', { class: 'text-sm text-fg-secondary' }, note) : null,
      ])
    }
  }),

  Chip: stateful((p) => {
    const outer = inject(LAYOUT, null)
    return () => {
      const { text = '', color, icon, note } = p.props ?? {}
      return h('span', { class: ['diagram-chip diagram-in max-w-full [overflow-wrap:anywhere]', outer?.value.top && 'self-center'], style: colorStyle(color) }, [
        iconNode(icon),
        text,
        note ? h('span', { class: 'font-normal text-fg-secondary' }, `· ${note}`) : null,
      ])
    }
  }),

  Label: renderer(({ text = '', icon, color }) =>
    h('span', { class: 'flex items-center gap-2 text-sm font-medium', style: COLOR_VALUES[color] ? { color: COLOR_VALUES[color] } : undefined }, [
      iconNode(icon),
      text,
    ]),
  ),

  Arrow: stateful((p) => {
    const outer = inject(LAYOUT, null)
    return () => {
      const { label, both } = p.props ?? {}
      const words = label ? ` ${label}` : ''
      const down = both ? '⇅' : '↓'
      const side = both ? '⇄' : '→'
      const cls = ['diagram-in self-center text-center text-fg-faint', label && 'text-xs']
      if (outer?.value.layout !== 'row') return h('span', { class: cls, 'aria-hidden': 'true' }, down + words)
      return h('span', { class: cls, 'aria-hidden': 'true' }, [
        h('span', { class: 'sm:hidden' }, down + words),
        h('span', { class: 'hidden sm:inline' }, side + words),
      ])
    }
  }),

  // Drawn as an image, so the SVG cannot run scripts or reach the page; it gets the theme's
  // tokens and the diagram classes as its own stylesheet. A page written before briefs carried
  // the SVG as its second argument.
  Diagram: stateful((p) => {
    const css = useThemeCss()
    return () => {
      const { label = '', brief = '', caption, svg } = p.props ?? {}
      const source = svg || (brief.trim().startsWith('<svg') ? brief : '')
      if (!source || !css.value) return null
      return h(Diagram, { label, caption, class: 'rounded-[var(--radius-xl)] bg-bg-subtle p-4 sm:p-5' }, () =>
        h('img', {
          src: `data:image/svg+xml;charset=utf-8,${encodeURIComponent(themedSvg(source, css.value.svg))}`,
          alt: '',
          class: 'block h-auto w-full',
        }),
      )
    }
  }),

  // An interactive piece: its HTML in a sandboxed iframe. Scripts run, but without
  // `allow-same-origin` the frame has no access to the app, its cookies or its storage, and its
  // content policy allows no network. It gets the theme's tokens, so it looks like the app.
  Artifact: stateful((p) => {
    const css = useThemeCss()
    return () => {
      const { title = '', brief = '', height, html } = p.props ?? {}
      const source = html || (/^\s*<(!doctype|html)/i.test(brief) ? brief : '')
      if (!source || !css.value) return null
      return h('iframe', {
        title,
        srcdoc: themedDocument(source, css.value.html),
        sandbox: 'allow-scripts',
        referrerpolicy: 'no-referrer',
        loading: 'lazy',
        class: 'block w-full rounded-[var(--radius-xl)] border-0 bg-bg-subtle',
        style: { height: `${Number(height) > 0 ? Number(height) : DEFAULT_ARTIFACT_HEIGHT}px` },
      })
    }
  }),
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
