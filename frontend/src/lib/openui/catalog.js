import { z } from 'zod'
import { createLibrary, defineComponent } from '@openuidev/vue-lang'
import { COLORS } from './colors.js'

// The page catalogue: what the web agent may write in OpenUI Lang (see docs/page-format.md).
// The schemas and descriptions live here, with no renderers, so the same catalogue builds the
// app's library (library.js, onto elastic-ui) and the one the prompt is generated from
// (prompt.js, which the CLI loads in Node). Argument order is the order of the keys below.
//
// Each component mirrors an elastic-ui part, its props simplified, and its description says
// when to reach for it. The figure pieces (Figure, Group, Area, Chip, Label, Arrow) are the
// library's diagram classes, so a model can compose the boxes-with-tints drawings the class
// site draws by hand. Diagram and Artifact are written as a brief, and a stronger model draws
// them after the page is written (backend/app/agents/web.py).

export const ROOT = 'Page'

const DESCRIPTIONS = {
  Page: 'The whole page: its blocks, top to bottom, in one column. Always the root.',
  Heading:
    'A section heading. The page title is shown already, so level 2 for sections and 3 for subsections. Prefer role headings that say what kind of section it is.',
  Text: 'Running text in Markdown: paragraphs, short lists (up to 5 points), **bold**, `inline code` and links. No headings, no code fences and no tables here.',
  CodeBlock:
    'Code that simply is: a file, a command, a folder tree. Name it by its file (title) when it is one. Paste the real code; never describe code in prose.',
  CodeDiff:
    'A change to a file: the code before and after, played as an edit. Use it instead of two CodeBlocks when the point is what changed.',
  Callout:
    'An aside set apart from the text: note, tip, important, warning or caution, one kind per thing. Its text is Markdown. Never two in a row, and never for the main idea.',
  StepItem: 'One step: a short title and its explanation in Markdown.',
  Steps: 'Numbered steps for a procedure the reader follows in order.',
  Table:
    'A comparison or structured facts: column headers and rows of short cells (Markdown inline: `code`, **bold**). Use it whenever two or more things are compared on the same points.',
  DescriptionItem: 'One term and what it is, in a sentence (Markdown).',
  DescriptionList:
    'Terms and their one-sentence definitions, or a record of key and value (G: groupId, A: artifactId). Only for terms the page uses; never a loose glossary.',
  AccordionItem: 'One folded section: its title and its content in Markdown.',
  Accordion:
    'Secondary detail that not everyone needs, folded away (special cases, troubleshooting, long reference). Nothing essential goes here: the page must make sense with every section closed.',
  Card: 'One card: a title, an optional line, an optional link (the whole card opens it) and an optional image URL.',
  Cards:
    'A grid of cards for related things side by side: pages to go to, tools, or the references the page comes from (a book, a talk, a project), each a card with its link. Two columns, one on a phone.',
  Logos:
    'A row of technology or brand names with their logos, to name a stack without spending text (Java, Spring Boot, Vue, Docker...). Names only; the logos are looked up.',
  TerminalEntry: 'One command: what is typed, what it printed, and an optional comment saying what it is for.',
  TerminalReplay:
    'Commands that are run, played back in a terminal with their output. For a short sequence the reader will type. A single command with no output is a CodeBlock instead.',
  AgentPrompt: 'What the person asks the agent, with an optional note on what to notice.',
  AgentStep:
    'Something the agent does on its way (search, read, run, edit): the line while it runs, the line once done, an optional icon, what it printed, a note, and whether it had to ask permission.',
  AgentAnswer: "The agent's answer, with optional code it hands over and a note.",
  AgentReplay:
    'A session with an AI agent, played back step by step, with a short note for each moment. The way to show how an agent works, rather than drawing it. One idea per session; say in the text that it is an example.',
  ChatMessage: 'One message: who sends it (user or assistant) and its text in Markdown.',
  Chat: 'A short chat exchange, shown as a chat: to show what asking an assistant looks like. For an agent that acts, use AgentReplay.',
  Chip: 'A tinted part of a figure: a short name, an optional icon and an optional quieter note after it.',
  Label: 'A plain line in a figure, no tint: an icon and a short text, as one item of a list inside an Area. Its colour, if any, is for the text and icon (green/amber/red for yes/ask/no).',
  Arrow: 'A connector between the parts before and after it: an arrow that points along the layout (down on a phone), with an optional word on it ("calls").',
  Area: 'A larger tinted group with a title: a concept that holds others (Chips and Labels), as the harness round a model. Never an Area inside an Area.',
  Group: 'Lays out parts in a row, a column or a grid inside a Figure, with no tint of its own: two Areas stacked at the end of a row, or four Areas in a grid. A row turns into a column on a phone.',
  Figure:
    'A drawing composed from tinted parts, for pieces that fit together or a flow: Areas, Chips, Labels and Arrows laid out in a row, a column or a grid, on a soft background. The label says in words what it shows. The way to draw most ideas; one colour per concept, the same in the whole page.',
  Diagram:
    'A drawing the Figure pieces cannot make: a curve, a timeline, axes, a cycle, a shape that matters. Write a brief, not the drawing: a drawing model makes the SVG from it. Leave `svg` out.',
  Artifact:
    'A small interactive piece, only when touching it is the point (compare two behaviours live, a simulation, a calculator). At most one per page. Write a brief, not the code: a model writes the HTML from it. Leave `html` out.',
}

const color = z
  .enum(COLORS)
  .optional()
  .describe('One colour per concept, the same in the whole page. green/amber/red only for yes/with conditions/no')
const icon = z.string().optional().describe('An icon name from the icon set')
const layout = z.enum(['row', 'column', 'grid']).optional()

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
      language: z.string().optional().describe('Language, such as "bash" or "java"'),
      title: z.string().optional().describe('The file it belongs to, such as "main.py"'),
    }),
  )

  const CodeDiff = component(
    'CodeDiff',
    z.object({
      before: z.string().describe('The code before the change'),
      after: z.string().describe('The same code after it'),
      file: z.string().optional().describe('The file changed'),
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
    z.object({ title: z.string(), text: z.string().describe('Markdown') }),
  )
  const Steps = component('Steps', z.object({ items: z.array(StepItem.ref) }))

  const Table = component(
    'Table',
    z.object({
      columns: z.array(z.string()).describe('The header of each column'),
      rows: z.array(z.array(z.string())).describe('Each row, one short cell per column'),
      caption: z.string().optional(),
    }),
  )

  const DescriptionItem = component(
    'DescriptionItem',
    z.object({ term: z.string(), text: z.string().describe('Markdown, one sentence') }),
  )
  const DescriptionList = component(
    'DescriptionList',
    z.object({ items: z.array(DescriptionItem.ref) }),
  )

  const AccordionItem = component(
    'AccordionItem',
    z.object({ title: z.string(), text: z.string().describe('Markdown') }),
  )
  const Accordion = component('Accordion', z.object({ items: z.array(AccordionItem.ref) }))

  const Card = component(
    'Card',
    z.object({
      title: z.string(),
      text: z.string().optional().describe('One line'),
      href: z.string().optional().describe('A full URL; the whole card is the link'),
      image: z.string().optional().describe('An image URL, only one given in the notes'),
    }),
  )
  const Cards = component('Cards', z.object({ items: z.array(Card.ref) }))

  const Logos = component(
    'Logos',
    z.object({ names: z.array(z.string()).describe('Technology names, such as "Spring Boot"') }),
  )

  const TerminalEntry = component(
    'TerminalEntry',
    z.object({
      command: z.string().describe('What is typed, without the prompt'),
      output: z.string().optional().describe('What it printed; ✔ or ✖ at a line start reads as passed or failed'),
      comment: z.string().optional().describe('What the command is for'),
    }),
  )
  const TerminalReplay = component(
    'TerminalReplay',
    z.object({
      entries: z.array(TerminalEntry.ref),
      title: z.string().optional().describe('Where it runs, such as "~/shop"'),
    }),
  )

  const note = z.string().optional().describe('What to notice at this moment, in one sentence')
  const AgentPrompt = component('AgentPrompt', z.object({ text: z.string(), note }))
  const AgentStep = component(
    'AgentStep',
    z.object({
      running: z.string().describe('While it runs: "Reading Shop.java"'),
      done: z.string().describe('Once done: "Read Shop.java"'),
      icon,
      output: z.string().optional().describe('What it printed or found'),
      note,
      permission: z
        .enum(['ask-allow', 'ask-deny', 'deny'])
        .optional()
        .describe('It stopped to ask and was allowed or denied, or was refused outright'),
    }),
  )
  const AgentAnswer = component(
    'AgentAnswer',
    z.object({
      text: z.string(),
      code: z.string().optional().describe('Code the answer hands over'),
      note,
    }),
  )
  const AgentReplay = component(
    'AgentReplay',
    z.object({ events: z.array(z.union([AgentPrompt.ref, AgentStep.ref, AgentAnswer.ref])) }),
  )

  const ChatMessage = component(
    'ChatMessage',
    z.object({ role: z.enum(['user', 'assistant']), text: z.string().describe('Markdown') }),
  )
  const Chat = component('Chat', z.object({ messages: z.array(ChatMessage.ref) }))

  // The figure pieces.
  const Chip = component(
    'Chip',
    z.object({
      text: z.string(),
      color,
      icon,
      note: z.string().optional().describe('A quieter word or two after the name'),
    }),
  )
  const Label = component(
    'Label',
    z.object({ text: z.string(), icon, color }),
  )
  const Arrow = component(
    'Arrow',
    z.object({
      label: z.string().optional().describe('A word on the arrow, such as "calls"'),
      both: z.boolean().optional().describe('Both ways (⇄)'),
    }),
  )
  const Area = component(
    'Area',
    z.object({
      title: z.string(),
      parts: z.array(z.union([Chip.ref, Label.ref, Arrow.ref])),
      color,
      icon,
      note: z.string().optional().describe('One short sentence under the parts'),
      layout: layout.describe('How its parts are laid out; column by default'),
    }),
  )
  const Group = component(
    'Group',
    z.object({ parts: z.array(z.union([Area.ref, Chip.ref, Label.ref, Arrow.ref])), layout }),
  )
  const Figure = component(
    'Figure',
    z.object({
      label: z.string().describe('What the figure shows, in words, for screen readers'),
      parts: z.array(z.union([Area.ref, Chip.ref, Label.ref, Arrow.ref, Group.ref])),
      layout: layout.describe('row (default; a column on a phone), column or grid'),
      caption: z.string().optional(),
    }),
  )

  const Diagram = component(
    'Diagram',
    z.object({
      label: z.string().describe('What the drawing shows, in words'),
      brief: z
        .string()
        .describe('For the drawing model: what to draw, its parts and labels, the colour of each concept, and the one thing to notice'),
      caption: z.string().optional(),
      svg: z.string().optional().describe('Leave out: filled in by the drawing model'),
    }),
  )

  const Artifact = component(
    'Artifact',
    z.object({
      title: z.string().describe('What it is, for screen readers'),
      brief: z
        .string()
        .describe('For the coding model: what the piece shows, what the reader can do with it, its parts and colours, and what it should make obvious'),
      height: z.number().optional().describe('Its height in pixels while it loads; it then takes the height of what it holds'),
      html: z.string().optional().describe('Leave out: filled in by the coding model'),
    }),
  )

  const Block = z.union([
    Heading.ref,
    Text.ref,
    CodeBlock.ref,
    CodeDiff.ref,
    Callout.ref,
    Steps.ref,
    Table.ref,
    DescriptionList.ref,
    Accordion.ref,
    Cards.ref,
    Logos.ref,
    TerminalReplay.ref,
    AgentReplay.ref,
    Chat.ref,
    Figure.ref,
    Diagram.ref,
    Artifact.ref,
  ])

  const Page = component('Page', z.object({ blocks: z.array(Block) }))

  return createLibrary({
    root: ROOT,
    components: [
      Page,
      Heading,
      Text,
      CodeBlock,
      CodeDiff,
      Callout,
      Steps,
      StepItem,
      Table,
      DescriptionList,
      DescriptionItem,
      Accordion,
      AccordionItem,
      Cards,
      Card,
      Logos,
      TerminalReplay,
      TerminalEntry,
      AgentReplay,
      AgentPrompt,
      AgentStep,
      AgentAnswer,
      Chat,
      ChatMessage,
      Figure,
      Group,
      Area,
      Chip,
      Label,
      Arrow,
      Diagram,
      Artifact,
    ],
  })
}

// How the web agent should write a page; the CLI picks it up with the library.
export { promptOptions } from './prompt-options.js'
