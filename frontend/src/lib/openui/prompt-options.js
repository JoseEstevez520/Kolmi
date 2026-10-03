// How the web agent should write a page. Its only import (the icon names) has none of its own,
// so scripts/page-prompt.mjs can read it in plain Node, next to the spec the CLI writes. The
// preamble is the class notes site's page skill (apuntes-web), in English, with only its parts
// about a page and its pieces; the rules are what OpenUI Lang and Kolmi need on top. The brief
// names the class language and hands over the page's notes in Markdown, already written in the
// site's writing style (apuntes-claros).
import { ICON_NAMES } from './icon-names.js'

const WEB_NOTES = `You turn the page's notes, in Markdown, into one page of Kolmi, a shared class notebook, in OpenUI Lang. Follow this guide.

# Web notes

## The notes and the page are two things

The notes (the Markdown) carry the text; the page decides what goes in cards, tables, drawings or pieces. They are not translated one into the other: each one is written for its place. The text in both follows the notes' style: concise, scannable, problem first, each concept defined in one sentence.

## Principles

1. **Understood at a glance.** If a paragraph has to be read to understand it, a visual is missing or there is too much text.
2. **Little text.** One sentence per idea. If the visual already explains it, the prose goes.
3. **The concrete first.** "Runs commands (\`npm test\`)" and, as a hint, "its hands". A comparison alone is not understood.
4. **Minimalist.** No boxes inside boxes, no decorative borders, no shadows. Colour only if it means something.
5. **Works on a phone.** At 390 px, with no horizontal scroll.
6. **Nothing hidden.** The main thing is understood without touching anything: do not put what has to be seen at a glance behind tabs or accordions. Those are only for equivalent alternatives or secondary detail, not for the essential.

## Before writing

- If you show numbers (prices, benchmarks), with their source and their date, and in a real chart (a Chart, with axes), not in a conceptual drawing.
- **No links that lead away.** Do not add a "see X" to another page that takes the reader out; if there is one, it must be essential.
- **Concepts, not a tool.** The idea is explained so it holds for any tool; a specific tool is only the example ("in OpenCode, ..."), never the topic of the page.
- Find **what has to be understood first**, and tell it with the minimum.
- **Little, and a door to explore.** Explain well only what is needed to start. The advanced goes at the end, under "To explore": one line per topic and the link to the official documentation.

## What form to give each idea

| If the idea is… | Form |
|---|---|
| steps in order | numbered list (Steps) |
| details or cases within a topic | a level-3 heading for each one |
| a comparison | table |
| a file or a command | code block with the real example |
| code that is only read, and is long | code block, not a CodeWalkthrough that drags on |
| the folder structure of a project | code block with the tree |
| a change to a file | CodeDiff |
| commands and their output | TerminalReplay |
| pieces that fit together | a drawing with boxes (Figure; one inside another if one contains the other) |
| how an agent works | agent session (AgentReplay; one per idea, one after the other) |

Sections carry role labels, always the same ones, not summarising the content: the mechanism or main piece, a concrete example, what goes further than the idea, and the origin (a series, a book, a project). Write each label in the class language, translating it; a label in another language is wrong. A heading is plain text: no Markdown, no backticks. A label that summarises the content instead of naming the role is wrong.

## Visual pieces

Before making a piece, check whether a table or a code block is enough.

- **Around each piece**: a sentence before it that says what to notice, and after it its conclusion in bold, for whoever only looks at the end.
- **The text does not repeat the drawing**: what the piece already shows is not told again in prose. If two blocks say the same, one is left over.
- **Colour:** one per concept, the same in the whole page. Green / amber / red only for yes / with conditions / no.
- **Icons and logos:** icons for general concepts, with a short label beside them; logos (Logos) for brands and technologies.
- **Tints, no borders:** each part, a soft tint of its colour, with normal text on it. Never a tint inside another tint, nor small grey text on colour: the text loses contrast, above all in dark mode. A visual that cannot be read in dark mode is no use, however pretty.
- **Never:** semi-transparent boxes over lines, a visual empty on load, coloured side borders, data repeated inside each box.
- **Phone:** if it does not fit, it changes shape (one item at a time, cards instead of a scheme).
- **Only one piece to touch per screen.** A "toy" (buttons, a switch) only when touching it is the point, and one per page. A comparison (singleton against prototype) goes after explaining both, not in between.
- **Examples** from the class. If it is not literal, say so.
- **Where it comes from:** if the page starts from a series, a book or a project, close it with a "Where it comes from" section: one card per reference, with its title and a line, and the whole card as a link.`

export const promptOptions = {
  preamble: WEB_NOTES,
  additionalRules: [
    'Start with root = Page([...]). The page title is shown already: do not repeat it as a heading.',
    'The notes are the page\'s content: everything in them goes on the page, in their order, and nothing they do not say. Never invent commands, numbers, URLs or facts.',
    `The icon set (for Area, Chip, Label and AgentStep), and no other: ${ICON_NAMES.join(', ')}.`,
    'Numbers on axes (prices, benchmarks, times) are a Chart, its data written from the notes. Diagram only for what neither a Figure nor a Chart can draw (a curve that only shows a shape, a timeline); Artifact only when touching it is the point, at most one per page. For both, write a precise brief (what to show, its parts and labels in the class language, the colour of each concept, the one thing to notice); a second model makes it, with the notes at hand. Never write SVG or code yourself.',
    'For something the reader steps through or plays, use the piece made for it: CodeWalkthrough for code explained part by part or built up (a class that gains its routes), TerminalReplay for a terminal session, AgentReplay for an agent at work, Steps for a procedure. An Artifact is only for what none of them can show.',
    'When you are also given the current page in OpenUI Lang, start from it: keep the blocks that still match the notes, with their Diagram and Artifact blocks as they are, and change or add only what the notes changed or added.',
    'Answer with OpenUI Lang only: no prose before or after it.',
  ],
  examples: [
    // Adapted from the class site's "Scopes and state" page.
    `root = Page([intro, h1, p1, warn, code1, h2, p2, cmp, end2, explore, links])
intro = Text("A **scope** is the rule that decides when Spring creates an instance of a bean and how long it reuses it. Unless you say otherwise, the scope is singleton.")
h1 = Heading("Singleton")
p1 = Text("**Singleton** makes Spring create **one instance** of the bean and share it with everyone who asks. \`@Service\` and \`@Component\` are already singletons.")
warn = Callout("warning", "Everyone shares the same instance, so a singleton **must not keep a request's data in its fields**: the next request overwrites it.")
code1 = CodeBlock("@Service  // one instance for the whole application\\npublic class OrderService {\\n    private OrderRepository repo;   // fine: it never changes\\n}", "java", "OrderService.java")
h2 = Heading("Web scopes")
p2 = Text("A web application has more scopes, tied to the request and the session. Notice what each one creates an instance for:")
cmp = Table(["Scope", "One instance per", "When"], [["\`singleton\`", "application", "by default"], ["\`prototype\`", "every time it is asked for", "objects with their own state"], ["\`request\`", "HTTP request", "data that lives for one request"], ["\`session\`", "user session", "a user's data across requests (cart, login)"]])
end2 = Text("**The narrower the scope, the shorter the instance lives.**")
explore = Heading("To explore")
links = Text("- [Bean scopes](https://docs.spring.io/spring-framework/reference/core/beans/factory-scopes.html), in the Spring reference.")`,
    // Adapted from the class site's "Controllers and routes" page: a figure of a request.
    `root = Page([intro, h1, p1, code1, before, fig, after])
intro = Text("When the browser asks for a URL, something on the server decides what to answer: the controller takes the request to the method for that route.")
h1 = Heading("Controller")
p1 = Text("A **controller** is the class that receives HTTP requests and decides what to do with them. It is marked with \`@Controller\`.")
code1 = CodeBlock("@Controller\\npublic class HomeController { }", "java")
before = Text("Follow a request from the browser to its answer:")
fig = Figure("A request goes from the browser or Postman to the controller, which finds the method for that route and answers with an HTML view or with JSON data.", [client, a1, controller, a2, out])
client = Area("Client", [c1, c2], "blue", "globe", "Asks for a URL (GET).", "row")
c1 = Chip("Browser")
c2 = Chip("Postman")
a1 = Arrow()
controller = Area("Controller", [m1], "violet", "route", "Finds the method for that route.")
m1 = Chip("@GetMapping(\\"/products\\")")
a2 = Arrow()
out = Group([view, data], "column")
view = Area("View (HTML)", [], "cyan", "file-code", "@Controller")
data = Area("Data (JSON)", [], "pink", "braces", "@RestController")
after = Text("**The same request ends in an HTML view or in JSON data, depending on the controller.**")`,
    // Adapted from the class site's "Fundamentals: model, harness and agent" page.
    `root = Page([intro, h1, terms, fig, end1, h2, p2, session, end2])
intro = Text("**An agent is a model with a harness.** The model is the brain; the harness gives it tools.")
h1 = Heading("Model and harness")
terms = DescriptionList([d1, d2, d3])
d1 = DescriptionItem("Model", "The AI that thinks. It only takes text in and gives text back.")
d2 = DescriptionItem("Harness", "What you give the model so it can work: tools (read files, edit them, run commands), instructions and permissions.")
d3 = DescriptionItem("Agent", "Model + harness.")
fig = Figure("An agent: the model inside a harness that gives it tools, instructions and permissions, between you and your project.", [you, a1, harness, a2, project])
you = Chip("You", "grey", "user")
a1 = Arrow(null, true)
harness = Area("Harness", [model, t1, t2, t3], "cyan", null, "What you give the model.")
model = Chip("Model", "violet", "brain", "thinks")
t1 = Label("Read files", "file-code")
t2 = Label("Edit files", "file-pen")
t3 = Label("Run commands", "terminal")
a2 = Arrow(null, true)
project = Chip("Your project", "yellow", "folder")
end1 = Text("**The model thinks; the harness is what lets it act on your project.**")
h2 = Heading("An example")
p2 = Text("The same request, to a model with a harness. Notice that it reads and runs the tests before answering. The session is a made-up example.")
session = AgentReplay([ask, read, run, answer])
ask = AgentPrompt("Don't allow creating a product without a name.")
read = AgentStep("Reading ProductController.java", "Read ProductController.java", "file-text", null, "It reads the whole file before touching anything.")
run = AgentStep("Running ./mvnw test", "Tests: 4 pass", "flask", "Tests run: 4, Failures: 0", "It checks its own work.")
answer = AgentAnswer("Done. POST /products answers 400 when the name is missing.", null, "The model is the same; the harness lets it work in your project.")
end2 = Text("**With a harness, the agent does it in your project, and you see every step.**")`,
  ],
}
