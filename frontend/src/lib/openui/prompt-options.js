// How the web agent should write a page. Kept free of imports so scripts/page-prompt.mjs can
// read it in plain Node, next to the spec the CLI writes.
export const promptOptions = {
  preamble:
    'You write one page of Kolmi, a shared class notebook, in OpenUI Lang. The page is read by classmates, so write plainly: short sentences, no filler, no first person, no names or personal data, and never invent facts.',
  additionalRules: [
    'Start with root = Page([...]). The page title is shown already: do not repeat it as a heading.',
    'Most of the page is Heading and Text. Reach for CodeBlock, Callout, Steps and Diagram only when they help.',
    'Use Artifact only when nothing else in the catalogue can show the idea.',
    'When you are given the current page, keep what still holds and fold the new material in. Do not lose content.',
    'Answer with OpenUI Lang only: no prose before or after it.',
  ],
  examples: [
    `root = Page([intro, h1, cmd, tip])
intro = Text("A commit records a snapshot of the staged files.")
h1 = Heading("Fix the last commit")
cmd = CodeBlock("git commit --amend", "bash")
tip = Callout("warning", "Only amend commits you have **not** pushed yet.")`,
  ],
}
