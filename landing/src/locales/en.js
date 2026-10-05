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
    run: 'Run it',
    code: 'Code',
    switchLocale: 'Leer en español',
  },

  hero: {
    slogan: 'Learn as a hive.',
    lead: 'A notebook a whole class writes together. Everyone drops their notes, and at night an AI turns them into organized pages with diagrams, charts and interactive pieces.',
    scope: 'For one class, self-hosted.',
    primary: 'Run it for your class',
    secondary: 'See how it works',
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
        'CI/CD automates the steps you used to do by hand after each change: run the tests, build the image, and deploy it. Every push to the repository triggers **GitHub Actions**, GitHub’s service for running these automated jobs. The pipeline runs the tests, builds a **Docker image** (the app packaged with everything it needs to run), pushes it to a **registry** (a service that stores Docker images), and the server pulls the new image from there.',
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
    conclusion: 'Raw notes never go out. Only the summary does.',
  },

  today: {
    title: 'What you can do today',
    student: {
      title: 'As a student',
      items: [
        '**Drop a note** in free text, with files attached, whenever you have something to add.',
        '**Read the class’s pages**: diagrams, charts, tables, step-by-step replays of agent sessions and interactive pieces.',
        '**Find your way** with the content tree, a table of contents and links to the previous and next page.',
        '**Check the class timetable.**',
        '**Take a short tour** the first time you sign in.',
        '**Take the notebook with you**: download all the pages, or one section, as Markdown files, to keep or to upload to NotebookLM.',
      ],
    },
    admin: {
      title: 'As an admin',
      items: [
        '**Run the nightly pass** on a schedule, or on demand with “Run now”.',
        '**Check what the AI did** in the AI log: what it read, what it changed and the notes it worked from.',
        '**Organize the tree** by hand: create, rename, move, reorder and delete.',
        '**Set the class’s timetable and language**, Spanish or English.',
      ],
    },
  },

  pages: {
    title: 'What a page can hold',
    lead: 'A page is more than text. The web agent draws each idea for what it is. These pieces come from the class’s own pages.',
    diagram: {
      title: 'A diagram, where an idea has parts',
      label:
        'One model thinks in every agent; what changes is the role. The builder edits and runs commands, the planner asks first, the tutor does neither, and the explorer only reads',
      model: 'One model · thinks in all of them',
      builder: 'Builder · Build, in OpenCode',
      builderNote: 'Makes the change you ask for.',
      planner: 'Planner · Plan, in OpenCode',
      plannerNote: 'Thinks the change through and proposes it.',
      tutor: 'Tutor · made by you',
      tutorNote: 'Explains, but doesn’t solve the exercise for you.',
      explorer: 'Explorer · a subagent',
      explorerNote: 'Another agent sends it to look, and it comes back with the answer.',
      edits: 'Edits',
      runs: 'Runs commands',
      reads: 'Reads',
      yes: 'yes',
      asks: 'asks you',
      no: 'no',
      conclusion: 'What changes from one agent to another is not the model, but its instructions and permissions.',
    },
    chart: {
      title: 'A chart, where numbers matter',
      label: 'Quality against cost per solved task: almost the same quality, from twenty cents to seventy-four dollars',
      x: 'Cost per solved task',
      y: 'SWE-bench Verified',
      series: 'Models',
      caption: 'Data: AgentMarketCap, April 2026, as the class page shows it.',
      conclusion: 'Paying more doesn’t always buy more quality.',
    },
  },

  run: {
    title: 'Run it locally',
    lead: 'You need Python 3, Node 20 or higher, a Supabase project and an API key for a model.',
    commands: [
      '# backend, on :8000',
      'cd backend',
      'python3 -m venv .venv && source .venv/bin/activate',
      'pip install -r requirements-dev.txt',
      'cp .env.example .env    # Supabase, CLASS_CODE and the model keys',
      'uvicorn app.main:app --reload',
      '',
      '# frontend, on :5173',
      'cd frontend',
      'npm install',
      'cp .env.example .env',
      'npm run dev',
    ].join('\n'),
    after:
      'Create the tables first with `supabase/schema.sql`. The `.env` files stay out of git. Each class runs its own instance, and the backend ships as a Docker image: build, run and the cron for the pass are in the backend’s README.',
    backendReadme: 'Backend README',
    status: {
      title: 'In development',
      body: 'Next come “Ask the hive”, a chat with the notes, and forums.',
      roadmap: 'See the roadmap',
    },
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
    cta: 'Bring the hive to your class.',
    primary: 'Get the code',
    license: 'Open source under the MIT license.',
    security: 'Security issues follow SECURITY.md, never a public issue.',
  },

  links: {
    repo,
    backendReadme: `${blob}/backend/README.md`,
    roadmap: `${blob}/ROADMAP.md`,
    license: `${blob}/LICENSE`,
    security: `${blob}/SECURITY.md`,
  },
}
