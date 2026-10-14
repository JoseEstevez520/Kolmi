// The landing's texts in English. They follow the README section by section: a change to one
// goes into the other (and into es.js) in the same commit. `**bold**` and `code` in backticks
// are drawn by RichText.

const repo = 'https://github.com/JoseEstevez520/Kolmi'
const blob = `${repo}/blob/main`

export default {
  meta: {
    title: 'Kolmi · Learn as a hive',
    description:
      'Kolmi is where a class keeps its notes together: everyone leaves theirs, and every night an AI turns them into shared pages the class can read and ask questions of.',
  },

  nav: {
    label: 'Sections',
    how: 'How it works',
    chat: 'Chat',
    ai: 'Your AI',
    code: 'Code',
    switchLocale: 'Leer en español',
  },

  hero: {
    slogan: 'Learn as a hive.',
    lead: 'The class’s notes are scattered across chats and drives, and nobody knows which to trust. Kolmi keeps them in one place: everyone leaves theirs, and every night an AI turns them into shared pages the class can read and ask questions of.',
    scope: 'For one class, self-hosted.',
    primary: 'Run it for your class',
  },

  demo: {
    label: 'Two loose notes about CI/CD, and the shared page Kolmi wrote from them',
    notes: [
      'ci/cd: every time i push, github actions runs the tests on its own. if they pass it builds the docker image. its all in a yaml file inside .github/workflows',
      'after the build the image goes to a registry and the server pulls it from there. if the tests fail nothing gets deployed. to rollback you just deploy the previous image',
    ],
    noteDate: 'Last night',
    noteStatus: 'In the notes',
    page: {
      title: 'CI/CD with GitHub Actions and Docker',
      intro:
        'CI/CD automates what you used to do by hand after each change. Every push triggers **GitHub Actions**: it runs the tests, builds a **Docker image** and pushes it to a **registry**, where the server pulls it from.',
      diagramLabel:
        'A git push triggers GitHub Actions, which runs the tests, builds the Docker image and pushes it to a registry; the server pulls the image from there',
      push: 'git push',
      triggers: 'triggers',
      actions: 'GitHub Actions',
      actionsNote: 'runs the automated jobs',
      tests: 'tests',
      build: 'docker build',
      pushImage: 'docker push',
      registry: 'registry',
      pulls: 'pulls',
      server: 'server pulls image',
      conclusion: 'The whole path runs by itself after each push.',
    },
    caption: 'Two loose notes in, one page out. This one is a real run of the nightly pass.',
  },

  what: {
    title: 'What is Kolmi?',
    body: [
      'Every class ends up with the same mess. The notes sit in chats, personal drives and photos of the whiteboard. Two people wrote the same thing down differently, nobody knows which version is right, and what you need before the exam is in someone else’s notebook.',
      'In Kolmi everyone leaves what they have, in their own words and in no particular format. Each night the hive reads what is new and judges every note: it joins it with what the class already has, strips names and private data and drops what adds nothing. What is left becomes the class’s pages, laid out like a study guide, with a diagram where an idea has parts and a table or chart where the numbers matter. The raw note stays private.',
    ],
    scope: 'Kolmi is for one class. Each class runs its own copy, with its own data. An admin is a student who looks after the class; there is no teacher account.',
  },

  how: {
    title: 'How it works',
    body: 'A team of agents runs once a day, on the schedule an admin sets. The **gatekeeper** reads each new note, strips names and private data, discards what adds nothing and decides which page it belongs to. The reason for each decision is kept in the AI log. The **notes agent** writes what the gatekeeper lets through, and the **web agent** lays it out as a page.',
    lead: 'Watch one pass take the two notes from above. It is a made-up session, shortened.',
    intro: 'At night the pass wakes up and takes what is new.',
    events: [
      {
        kind: 'prompt',
        text: 'Nightly pass · 2 new notes',
        note: 'Nobody presses anything: a schedule wakes the pass.',
      },
      {
        kind: 'step',
        icon: 'gatekeeper',
        running: 'Gatekeeper reading 2 new notes',
        done: 'Gatekeeper read 2 notes',
        output:
          'Same topic: CI/CD.\nNo names or private data.\nNothing to discard.\nGoes to: Deployment › CI/CD with GitHub Actions and Docker',
        duration: 1800,
        note: 'The gatekeeper goes first: the raw notes never reach the other two.',
      },
      {
        kind: 'step',
        icon: 'notes',
        running: 'Notes agent writing the topic',
        done: 'Notes agent wrote the topic',
        duration: 1600,
        note: 'Two notes become one explanation, in the house style.',
      },
      {
        kind: 'step',
        icon: 'web',
        running: 'Web agent laying out the page',
        done: 'Web agent updated the page',
        diff: {
          file: 'ci-cd.md',
          before: '# CI/CD with GitHub Actions and Docker\n',
          after:
            '# CI/CD with GitHub Actions and Docker\n\nEvery push triggers GitHub Actions…\n\n<Diagram: push → tests → build → registry → server>\n\n**The whole path runs by itself after each push.**\n',
        },
        duration: 1800,
        note: 'The page gets a diagram, because the idea has parts.',
      },
      {
        kind: 'answer',
        text: 'Done: 1 page updated from 2 notes. The raw notes stay on the server.',
        note: 'Only the summary goes out.',
      },
    ],
    table: {
      label: 'A raw note and a shared page compared',
      head: ['', 'Raw note', 'Shared page'],
      rows: [
        ['Who sees it', 'its author and the admins, until the pass takes it', 'the whole class'],
        ['What it looks like', 'free text and files', 'organized, with diagrams, tables, charts and interactive pieces'],
        ['Names and private data', 'whatever you wrote', 'stripped'],
      ],
    },
  },

  ask: {
    title: 'Ask the notes',
    body: 'The chat answers from the class’s own pages, not from what a model remembers. It finds the passages closest to your question, answers with them and says which pages it used. Ask for a table or the steps of a procedure and it draws one.',
    label: 'A made-up conversation: a question answered from the notes, with its sources, and a note the chat proposes to make, waiting for a confirmation',
    question: 'What do the notes say about bean scopes?',
    answer: 'A scope decides when Spring creates a bean and how long it is reused. Most beans are `singleton`, one for the whole app. Use `request` when the bean holds state for a single request.',
    sources: 'Sources: Bean scopes',
    request: 'Make a note that the exam covers up to unit 4.',
    reply: 'Here is the note. Nothing is saved until you confirm it.',
    proposal: {
      label: 'Create a note',
      done: 'Created a note',
      args: { Title: 'Exam', Text: 'The exam covers up to unit 4.' },
      result: 'Note sent. Tonight the hive reads it.',
    },
    caption: 'A made-up conversation. The card works, with nothing behind it.',
    acts: 'The chat can act, but never on its own. Anything that changes something comes back as a card showing what would change, and it happens when you confirm. A student can leave and edit their own notes this way. An admin can also move pages, edit the timetable and look after the class’s people. It can report a problem with the app too. An admin turns the chat on and sets a daily limit per student.',
  },

  ai: {
    title: 'Your own AI, connected',
    body: 'Kolmi is also an MCP server, so the AI you already use can work with the class’s notes as you. Say your course is on Moodle and the practice code is in a GitHub repo. With Moodle, GitHub and Kolmi connected to the same assistant, you ask it to read this week’s material and write it up. It reads the class’s tree first, sees what the pages already say and leaves one note per topic, each with the link it came from. An admin’s AI can fold the material straight into a page instead.',
    label: 'Moodle and a GitHub repo are read by your AI assistant, which leaves notes in Kolmi',
    material: 'Your material',
    moodle: 'Moodle',
    repo: 'GitHub repo',
    reads: 'reads',
    assistant: 'your AI',
    leaves: 'leaves',
    notes: 'notes in Kolmi',
    connect: 'In Settings, under **Connect your AI**, you name the connection and get a token, shown once, and the command for your client with your instance’s address already in it. For Claude Code it has this shape:',
    command: 'claude mcp add --transport http kolmi <url> --header "Authorization: Bearer <token>"',
    limits: 'There are instructions for Claude Code, Gemini CLI and Codex CLI, and for any other client that takes a bearer token. Chat apps whose connectors need an OAuth sign-in are not supported yet. Reading is free. Your AI acts with your role, and anything that changes something asks you first.',
  },

  today: {
    title: 'Around the notes',
    items: [
      { title: 'Live notes', text: 'During a class, someone shares what they are writing and the rest follow it as it appears. The note stays an ordinary note and goes through the nightly pass.' },
      { title: 'The timetable', text: 'The class’s week on one screen. An admin edits it by dragging on the grid.' },
      { title: 'Downloads', text: 'Any section as Markdown files, to keep or to upload to NotebookLM. Pages can carry files to download too.' },
      { title: 'The AI log', text: 'What each pass read, what it changed and why it discarded a note.' },
      { title: 'Admins are students', text: 'A student with more permissions: runs the pass, shapes the tree and lets new people in.' },
      { title: 'A quiet interface', text: 'Little text, icons that say their name on hover, and the app in English or Spanish.' },
    ],
  },

  run: {
    title: 'Run it for your class',
    body: 'You need Python 3, Node 20 or higher, a Supabase project and an API key for a model. The backend ships as a Docker image, and the nightly pass is a cron job on the same server. The steps are in the README and in the backend’s README.',
    scope: 'Each class runs its own instance, with its own Supabase project and server. Nothing is shared between classes, and the keys stay in your `.env`.',
    cta: 'Read the steps',
  },

  docs: {
    title: 'Documentation',
    items: [
      { title: 'The idea', text: 'The problem, the team of agents and why raw notes stay private.', href: `${blob}/docs/idea.md` },
      { title: 'Authentication and users', text: 'Accounts, roles and the class code.', href: `${blob}/docs/authentication.md` },
      { title: 'Features and actions', text: 'What the app does and how each action is built.', href: `${blob}/docs/features.md` },
      { title: 'The chat', text: 'What the model writes, how a question travels and how a change is proposed.', href: `${blob}/docs/chat.md` },
      { title: 'The MCP', text: 'Connecting your own AI: tokens, resources, prompt and evals.', href: `${blob}/docs/mcp.md` },
      { title: 'Actions as tools', text: 'How every feature is one action that the web, the chat and the MCP share.', href: `${blob}/docs/tools.md` },
      { title: 'Live notes', text: 'Following a class through someone’s notes.', href: `${blob}/docs/live-notes.md` },
      { title: 'Page format', text: 'How a page goes from the pass to the screen.', href: `${blob}/docs/page-format.md` },
      { title: 'Testing with real cases', text: 'The plan for trying it before the class does.', href: `${blob}/docs/testing.md` },
      { title: 'Data and privacy', text: 'What is stored, who sees it and what leaves the instance.', href: `${blob}/docs/privacy.md` },
      { title: 'Brand tone', text: 'How Kolmi sounds.', href: `${blob}/docs/brand-tone.md` },
      { title: 'Brand visuals', text: 'How to make an image that looks like Kolmi.', href: `${blob}/docs/brand-visuals.md` },
    ],
  },

  ecosystem: {
    title: 'Ecosystem',
    items: [
      { title: 'elastic-ui', text: 'The component library the web is built with.', href: 'https://github.com/JoseEstevez520/elastic-ui' },
    ],
  },

  footer: {
    contact: 'Questions, or want it in your class? Write to me.',
    cta: 'Bring the hive to your class.',
    primary: 'Get the code',
    license: 'Open source under the MIT license.',
    security: 'Security issues follow SECURITY.md, never a public issue.',
  },

  links: {
    repo,
    linkedin: 'https://www.linkedin.com/in/jose-est%C3%A9vez-b9b761388',
    run: `${blob}/README.md#run-it-locally`,
    license: `${blob}/LICENSE`,
    security: `${blob}/SECURITY.md`,
  },
}
