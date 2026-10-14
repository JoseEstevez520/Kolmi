# The chat

The chat answers from the class's notes, and a model that wants to change something proposes
it first. This page says what the model writes, what it doesn't, and how to change either.

## What the model writes

An answer is a short program in OpenUI Lang, the same language the pages use. The model picks
parts from a catalogue the app already has, and the app draws them:

```
root = Answer([t, s, src])
t = Text("A scope decides when Spring creates a bean and how long it is reused.")
s = Steps([StepItem("No state", "Leave it as `singleton`."), StepItem("State per request", "Use `request`.")])
src = Sources([144, 143])
```

The model never copies a page or a figure. It says things in its own words and points at a page
by id; `Sources` loads the title and links it. If the program doesn't parse, or has no `Answer`
root, the web shows the raw text as Markdown instead.

## The parts

| Part | Shows |
|---|---|
| `Text(markdown)` | The answer itself, a few sentences |
| `Callout(type, text, title?)` | An aside: a warning, a tip |
| `Steps([StepItem(title, text)])` | A procedure in order |
| `Table(columns, rows, caption?)` | Two or more things on the same points |
| `Chart(label, series, variant?)` | Real numbers only |
| `Cards([Card(title, text?, href?)])` | Related things side by side |
| `CodeBlock(code, language?, title?)` | Code that simply is |
| `Sources([ids])` | The pages the answer rests on, linked |
| `Proposal(id)` | A change the model proposed, as a card to confirm |

The signatures and descriptions in the prompt are generated from the frontend catalogue
(`npm run page-prompt` writes `backend/app/agents/openui/chat.spec.json`), and a test checks that
every part the prompt names exists there. Which parts are offered is `CHAT_PARTS` in
`backend/app/agents/prompts.py`. `Diagram` and `Artifact` are left out: both need a second,
slower call to draw.

## How a question travels

1. The web sends the question and the last turns to `POST /chat/stream`.
2. The API loads the tree, the timetable and the closest passages of the notes, and gives the
   model the index and the tools for the asker's role.
3. The reply comes back as server-sent events: `status` while a tool runs, `token` for each piece
   of the program, `proposal` for each change, then `done` (or `error`).
4. The web draws the parts as the program arrives. It reads the stream with `fetch`, since
   `EventSource` can't send the auth header.

When the person has a page open (`/node/:id`), the web adds its id to the question as `node_id`.
The API checks it against the tree it already loaded for that person and puts one line in the
user part of the prompt: the page's title and id, and a reminder to read it with `read_page` if
the question is about it. The content is not sent. An id that doesn't exist, or that the person
can't see, is dropped without a word.

A change is never run by the model. It becomes a row in `chat_proposals` and a card; Confirm is a
new request. See [tools.md](tools.md).

## What a proposal shows

Each action with a preview draws what it would change inside its card: the tree before and after
for a move, a diff for a page, the week for a timetable slot, the people and their new status. The
raw arguments stay hidden until you press Edit, and the preview follows what you type. An action
with no preview shows the plain key and value card. The previews live in
`frontend/src/components/actionPreviews/`, one per kind of change.

## Speed and cost

Most of an answer's time used to be the model reasoning, not reading. The chat's model answers
without it (`CHAT_THINKING=false`, DeepSeek only), which took a typical answer on the real tree
from about 40 seconds to about 15. Turn it on if the answers get careless. `CHAT_MODEL` picks a
different model for the chat alone.

What the person waits for is cut in other ways too:

- The stream opens with a status ("Searching the notes...") before any preparation, so the first
  byte no longer waits for the embedding call. The class settings and the daily limit are still
  checked first and fail as plain HTTP errors.
- The passages search, the page tree, the class language and the timetable are read at the same
  time. They share one Supabase client, which is safe across threads.
- A `: ping` comment goes out after 15 seconds of silence, so a proxy doesn't cut a slow answer.
  The client ignores it.
- The chat isn't offered `list_nodes` and `search_pages` (`CHAT_LEFT_OUT` in
  `backend/app/actions/tools.py`): its prompt already has the tree and the passages. The MCP
  still offers both.

## Adding a part

1. Define it in the frontend catalogue (`frontend/src/lib/openui/catalog.js`) with a description
   the model reads. Take references (an id), never a figure.
2. Add its renderer and put it in the chat library (`chat-library.js`).
3. Add it to `CHAT_PARTS`, run `npm run page-prompt`, and run the backend tests.
4. Try it with a real model on three or four phrasings of the same question.

If the piece itself doesn't exist, it is built in elastic-ui first.

## Questions to try

- What does the class cover? Give me a table.
- How do bean scopes work? Give me the steps to choose one.
- What do the notes say about Thymeleaf forms?
- Who won the world cup? (not about the class: it should say so)
- Make a note that the exam is next Friday. (a proposal)
- As an admin: move the Thymeleaf page into Extra.
