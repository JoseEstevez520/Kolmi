import { h } from 'vue'
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
  Chart,
  ChatMessage,
  CodeBlock,
  CodeDiff,
  CodeWalkthrough,
  CodeWalkthroughStep,
  DescriptionItem,
  DescriptionList,
  Diagram,
  DiagramArea,
  DiagramArrow,
  DiagramChip,
  DiagramGroup,
  DiagramImage,
  DiagramItem,
  LogoList,
  LogoListItem,
  Markdown,
  Prose,
  SandboxFrame,
  Steps,
  StepsItem,
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  TerminalReplay,
  slugify,
} from 'elastic-ui'
import { createParser } from '@openuidev/vue-lang'
// The runtime an Artifact's piece runs on, served as a file of its own: only a page with a piece
// loads it, inside the piece's frame.
import sandboxRuntime from 'elastic-ui/sandbox-runtime.js?url'
import { buildLibrary, ROOT } from './catalog.js'
import { COLOR_VALUES } from './colors.js'
import { iconFor } from './icons.js'
import { logoFor } from './logos.js'

// The page catalogue drawn with elastic-ui. Every renderer gets the parsed `props` and a
// `renderNode` for its children; both are declared so Vue does not pass them on as attributes.
// Props can be partial while a page streams, so each one reads them defensively.

const declared = ['props', 'renderNode']

function renderer(render) {
  return { props: declared, setup: (p) => () => render(p.props ?? {}, p.renderNode) }
}

// A Markdown block that flows in the page's own Prose instead of opening a second article.
const markdown = (source) => h(Markdown, { source: source ?? '', class: 'contents' })

// A child component's props, read as data (a session's events, a terminal's entries).
const propsOf = (node) => node?.props ?? {}
const list = (value) => (Array.isArray(value) ? value : [])

// -- figures ---------------------------------------------------------------------------------

// The figure pieces' props, mapped onto elastic-ui's diagram parts: a colour by its name in the
// palette, an icon by its name in the icon set, a layout only if it is one of the three.
const colorOf = (name) => COLOR_VALUES[name]
const axisOf = (axis) => {
  if (!axis || typeof axis !== 'object') return undefined
  const { title, unit, scale, min, max } = axis
  const number = (v) => (Number.isFinite(Number(v)) && v !== null && v !== '' ? Number(v) : undefined)
  return { title, unit, scale: scale === 'log' ? 'log' : undefined, min: number(min), max: number(max) }
}
const layoutOf = (value) => (value === 'row' || value === 'column' || value === 'grid' ? value : undefined)

// -- cards -----------------------------------------------------------------------------------

// A link to a page of the notes (`/node/12`) goes through the router, so it never reloads the app.
function card({ title = '', text, href, image }) {
  const link = href?.startsWith('/') ? { to: href } : { href: href || undefined }
  return h(Card, { size: 'sm', ...link, class: 'h-full' }, () => [
    image ? h(CardImage, { src: image, alt: title, fade: true, class: 'aspect-video' }) : null,
    h(CardHeader, { class: 'gap-1' }, () => [
      h(CardTitle, { as: 'h3' }, () => title),
      text ? h(CardDescription, null, () => text) : null,
    ]),
  ])
}

// A cell's Markdown (`code`, **bold**), in the table's own type rather than an article's.
const cell = (value) => h(Markdown, { source: String(value ?? ''), class: 'text-ui [color:inherit] [&_p]:m-0' })

// Line numbers such as "3-5, 9"; anything else (a model pasting the code) lights up what the step adds.
const lineRanges = (value) => (/^\s*\d+(\s*-\s*\d+)?(\s*,\s*\d+(\s*-\s*\d+)?)*\s*$/.test(value ?? '') ? value : undefined)

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

  // Each step carries the whole code as it stands then; the file is the walkthrough's, one for all.
  CodeWalkthrough: renderer(({ steps, file }) => {
    const rows = list(steps).map(propsOf).filter((step) => step.code)
    if (!rows.length) return null
    return h(CodeWalkthrough, { class: 'my-8' }, () =>
      rows.map(({ title, text, code, highlight }, i) =>
        h(CodeWalkthroughStep, { key: i, title, code, highlight: lineRanges(highlight), file }, () => markdown(text)),
      ),
    )
  }),
  WalkthroughStep: renderer(() => null),

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
    return h(Table, null, () => [
      h(TableHeader, null, () => h(TableRow, null, () => cols.map((name, i) => h(TableHead, { key: i }, () => cell(name))))),
      h(TableBody, null, () =>
        list(rows).map((row, r) =>
          h(TableRow, { key: r }, () => cols.map((_, i) => h(TableCell, { key: i }, () => cell(list(row)[i])))),
        ),
      ),
      caption ? h(TableCaption, null, () => caption) : null,
    ])
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

  // In the text's colour: the app is grey, and colour only carries meaning (design.md).
  Logos: renderer(({ names }) =>
    h(LogoList, null, () =>
      list(names).map((name) => h(LogoListItem, { key: String(name), icon: logoFor(name), mono: true }, () => String(name))),
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

  // The figure pieces, on elastic-ui's diagram parts. A row runs down when it no longer fits and
  // its arrows turn with it; that is the library's, measured from the parts.
  Figure: renderer(({ label = '', parts, layout, caption }, renderNode) =>
    h(Diagram, { label, caption, class: 'rounded-[var(--radius-xl)] bg-bg-subtle p-5 sm:p-6' }, () =>
      h(DiagramGroup, { layout: layoutOf(layout) ?? 'row' }, () => renderNode(parts ?? [])),
    ),
  ),

  Group: renderer(({ parts, layout }, renderNode) =>
    h(DiagramGroup, { layout: layoutOf(layout) ?? 'column' }, () => renderNode(parts ?? [])),
  ),

  Area: renderer(({ title = '', parts, color, icon, note, layout }, renderNode) =>
    h(
      DiagramArea,
      { title, icon: iconFor(icon), color: colorOf(color), note, layout: layoutOf(layout) },
      list(parts).length ? () => renderNode(parts) : undefined,
    ),
  ),

  Chip: renderer(({ text = '', color, icon, note }) =>
    h(DiagramChip, { icon: iconFor(icon), color: colorOf(color), note }, () => text),
  ),

  Label: renderer(({ text = '', icon, color }) =>
    h(DiagramItem, { icon: iconFor(icon), color: colorOf(color) }, () => text),
  ),

  Arrow: renderer(({ label, both }) => h(DiagramArrow, { label, both: !!both })),

  // Drawn as an image by the library, so the SVG cannot run scripts or reach the page. A page
  // written before briefs carried the SVG as its second argument.
  Diagram: renderer(({ label = '', brief = '', caption, svg }) => {
    const source = svg || (brief.trim().startsWith('<svg') ? brief : '')
    if (!source) return null
    return h(Diagram, { label, caption, class: 'rounded-[var(--radius-xl)] bg-bg-subtle p-4 sm:p-5' }, () =>
      h(DiagramImage, { svg: source }),
    )
  }),

  // Values on real axes, the library's Chart. The axes keep only what the catalogue offers.
  Chart: renderer(({ label = '', series, variant, x, y, caption }) => {
    const drawn = list(series)
      .map(propsOf)
      .map(({ name = '', points, color }) => ({
        name,
        color: colorOf(color),
        points: list(points).filter((p) => p && p.x != null && Number.isFinite(Number(p.y))).map((p) => ({ x: p.x, y: Number(p.y), label: p.label || undefined })),
      }))
      .filter((one) => one.points.length)
    if (!drawn.length) return null
    return h(Chart, {
      label,
      caption,
      series: drawn,
      variant: ['line', 'bars', 'points'].includes(variant) ? variant : 'line',
      x: axisOf(x),
      y: axisOf(y),
      class: 'not-prose my-8',
    })
  }),
  ChartSeries: renderer(() => null),

  // An interactive piece in the library's sandboxed frame: no way to the app or the network, the
  // theme's tokens, and as tall as what it holds. `height` is only where it starts. A piece made
  // of the library's parts (a Vue component, from <template>) runs on the sandbox runtime; a page
  // written before it carries a whole HTML document, in that slot or, older, in the brief's.
  Artifact: renderer(({ title = '', brief = '', height, piece }) => {
    const common = { label: title, height: Number(height) > 0 ? Number(height) : undefined }
    if (/^\s*<template[\s>]/i.test(piece ?? '')) return h(SandboxFrame, { ...common, piece, runtime: sandboxRuntime })
    const html = piece || (/^\s*<(!doctype|html)/i.test(brief) ? brief : '')
    return html ? h(SandboxFrame, { ...common, html }) : null
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
