import { z } from 'zod'
import { createLibrary, defineComponent } from '@openuidev/vue-lang'

// The page catalogue: what the web agent may write in OpenUI Lang (see docs/page-format.md).
// The schemas and descriptions live here, with no renderers, so the same catalogue builds the
// app's library (library.js, onto elastic-ui) and the one the prompt is generated from
// (prompt.js, which the CLI loads in Node). Argument order is the order of the keys below.

export const ROOT = 'Page'

const DESCRIPTIONS = {
  Page: 'The whole page: its blocks, top to bottom, in one column. Always the root.',
  Heading:
    'A heading inside the page. The page title is already shown, so use level 2 for sections and 3 for subsections.',
  Text: 'Running text in Markdown: paragraphs, lists, **bold**, `inline code`, links and tables. No headings and no code fences here.',
  CodeBlock: 'A block of code with a copy button. Name it by its file (title) or its language.',
  Callout:
    'A note set apart from the text: note, tip, important, warning or caution. Its text is Markdown. Never two in a row.',
  StepItem: 'One step: a short title and its explanation in Markdown.',
  Steps: 'Numbered steps for a procedure the reader follows in order.',
  Diagram:
    'A small static drawing as a self-contained SVG string (viewBox, no scripts, no external images), with a label that says in words what it shows. Use mid greys that read on light and dark backgrounds.',
  Artifact:
    'The escape hatch, for what the other components cannot show (an interactive widget, a simulation). A self-contained HTML document with inline CSS and JS, run in a sandboxed iframe with no network access. Use it rarely.',
}

/** Build the catalogue's library with a renderer for each component, by name. */
export function buildLibrary(renderers) {
  const component = (name, props) =>
    defineComponent({ name, props, description: DESCRIPTIONS[name], component: renderers[name] })

  const Heading = component(
    'Heading',
    z.object({
      text: z.string().describe('The heading text'),
      level: z.union([z.literal(2), z.literal(3)]).optional().describe('2 (default) or 3'),
    }),
  )

  const Text = component(
    'Text',
    z.object({ markdown: z.string().describe('Markdown for one or more paragraphs or lists') }),
  )

  const CodeBlock = component(
    'CodeBlock',
    z.object({
      code: z.string().describe('The code, exactly as it should be copied'),
      language: z.string().optional().describe('Language, such as "bash" or "python"'),
      title: z.string().optional().describe('The file it belongs to, such as "main.py"'),
    }),
  )

  const Callout = component(
    'Callout',
    z.object({
      type: z.enum(['note', 'tip', 'important', 'warning', 'caution']),
      text: z.string().describe('Markdown'),
      title: z.string().optional().describe('Defaults to the type name'),
    }),
  )

  const StepItem = component(
    'StepItem',
    z.object({
      title: z.string(),
      text: z.string().describe('Markdown'),
    }),
  )

  const Steps = component('Steps', z.object({ items: z.array(StepItem.ref) }))

  const Diagram = component(
    'Diagram',
    z.object({
      label: z.string().describe('What the drawing shows, in words'),
      svg: z.string().describe('A complete <svg> element with a viewBox'),
      caption: z.string().optional(),
    }),
  )

  const Artifact = component(
    'Artifact',
    z.object({
      title: z.string().describe('What it is, for screen readers'),
      html: z.string().describe('A complete, self-contained HTML document'),
      height: z.number().optional().describe('Height in pixels; 360 by default'),
    }),
  )

  const Block = z.union([
    Heading.ref,
    Text.ref,
    CodeBlock.ref,
    Callout.ref,
    Steps.ref,
    Diagram.ref,
    Artifact.ref,
  ])

  const Page = component('Page', z.object({ blocks: z.array(Block) }))

  return createLibrary({
    root: ROOT,
    components: [Page, Heading, Text, CodeBlock, Callout, Steps, StepItem, Diagram, Artifact],
  })
}

// How the web agent should write a page; the CLI picks it up with the library.
export { promptOptions } from './prompt-options.js'
