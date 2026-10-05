// The landing's texts in English. They follow the README section by section: a change to one
// goes into the other (and into es.js) in the same commit. `**bold**` and `code` in backticks
// are drawn by RichText.

const repo = 'https://github.com/JoseEstevez520/Kolmi'
const blob = `${repo}/blob/main`

export default {
  meta: {
    title: 'Kolmi · Learn as a hive',
    description:
      'Kolmi is a notebook a whole class writes together: everyone drops their notes, and an AI turns them into organized pages.',
  },

  nav: {
    label: 'Sections',
    how: 'How it works',
    pages: 'Pages',
    code: 'Code',
    switchLocale: 'Leer en español',
  },

  hero: {
    slogan: 'Learn as a hive.',
    lead: 'A notebook a whole class writes together. Everyone drops their notes, and at night an AI turns them into organized pages with diagrams, charts and interactive pieces.',
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
      'In a class, everyone takes their own notes, and nobody has the whole notebook. Kolmi makes one, together.',
      'Everyone drops what they have, in their own words and in no particular format. At night the hive works: an AI reads what is new, joins what belongs together and writes the class’s pages. Each page is laid out like a good study guide, with a diagram where an idea has parts, a chart where numbers matter and small interactive pieces to try things out.',
    ],
    quote: 'Everyone adds a drop; the class ends up with honeycomb.',
    scope: 'Kolmi is for one class. Each class runs its own copy, with its own data.',
  },

  how: {
    title: 'How it works',
    body: 'A team of agents runs once a day. The **gatekeeper** reads each new note, strips names and private data, discards what adds nothing and decides which page it belongs to. The **notes agent** writes what the gatekeeper lets through, and the **web agent** lays it out as a page.',
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

  today: {
    title: 'What you can do today',
    student: {
      title: 'As a student',
      items: [
        { title: 'Drop a note', text: 'In free text, with files, whenever you have something to add.' },
        { title: 'Read the class’s pages', text: 'Diagrams, charts, tables, replays and interactive pieces.' },
        { title: 'Find your way', text: 'A content tree, a table of contents, the previous and next page.' },
        { title: 'Check the timetable', text: 'The class’s week, at a glance.' },
        { title: 'Take a short tour', text: 'The first time you sign in.' },
        { title: 'Take the notebook with you', text: 'Every page as Markdown, to keep or upload to NotebookLM.' },
      ],
    },
    admin: {
      title: 'As an admin',
      items: [
        { title: 'Run the nightly pass', text: 'On a schedule, or right now with “Run now”.' },
        { title: 'Check what the AI did', text: 'What it read, what it changed and the notes it worked from.' },
        { title: 'Organize the tree', text: 'Create, rename, move, reorder and delete.' },
        { title: 'Set timetable and language', text: 'The class’s week, in Spanish or English.' },
      ],
    },
  },

  pages: {
    title: 'What a page can hold',
    lead: 'The web agent lays each page out like a good study guide: in sections, with the right piece for each idea.',
    label: 'Loose notes go to the web agent, which turns them into an organized page with sections, diagrams, charts, tables, code, replays and interactive pieces',
    notes: 'Loose notes',
    agent: 'web agent',
    page: 'An organized page',
    pieces: ['Sections', 'Diagrams', 'Charts', 'Tables', 'Code', 'Replays', 'Interactive pieces'],
    conclusion: 'A piece where it helps, and plain text where text is enough.',
  },


  docs: {
    title: 'Documentation',
    items: [
      { title: 'The idea', text: 'The problem, the team of agents and why raw notes stay private.', href: `${blob}/docs/idea.md` },
      { title: 'Authentication and users', text: 'Accounts, roles and the class code.', href: `${blob}/docs/authentication.md` },
      { title: 'Features and actions', text: 'What the app does and how each action is built.', href: `${blob}/docs/features.md` },
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
    license: `${blob}/LICENSE`,
    security: `${blob}/SECURITY.md`,
  },
}
