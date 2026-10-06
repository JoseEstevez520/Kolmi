# The idea

Students in a class leave raw notes and a team of agents turns them into shared notes and
pages. No code yet: this is the design.

## The problem

Publishing a note by hand means knowing git and Vue, and most people don't, even when they
have something to say. The idea is that they only have to leave the note.

## How it works

1. The note is written wherever is comfortable (a chat bot or a box on the web), in free
   text, with no format.
2. It's stored **privately**, on our own server, outside the repo. The raw note is never
   published.
3. A cron wakes the agent team once a day.
4. The **gatekeeper** reviews them: it joins the ones about the same topic, strips names and
   classmate data, discards what doesn't add anything, and decides whether it goes in and
   where. If it's already in the notes, it fixes it; if not, it adds it.
5. The notes agents write what the gatekeeper passes, and the web one publishes it. The web
   rebuilds itself.

## The team

They're the same roles as any agent team, split like this:

| Agent | What it does |
|---|---|
| Gatekeeper | knows the courses: anonymizes, joins duplicates, discards and decides where each note goes |
| Notes | writes the note in the house style |
| Web | turns it into a page or updates the one it belongs to |

The gatekeeper goes first: the raw note never reaches the other two.

## Why private

A draft can carry names or classmate data, and what gets published once is already copied:
clones, caches, git history. That's why the raw note stays on the server and only the summary
goes out, without names. The gatekeeper is the door it goes through, not the one who cleans
up after.

## How it would be built

The infrastructure is two pieces:

- **The server**: the web app, the daily job and, later, the chat. Optionally, OpenCode in
  server mode too.
- **Supabase** (cloud, free): login and a database with the notes, the pages and their
  versions. If you ever want, it self-hosts on the server.

The agents are built with the OpenAI SDK, each with its own loop. One moves to LangGraph (a
framework for multi-step agent flows) only when it must pause and resume its own reasoning,
survive a long run or coordinate with other agents.

The account side has its own spec: [Authentication](authentication.md).

### Phase 1: notes and the daily pass

Students log in and leave notes; they don't touch the pages. A cron (the server's task
scheduler) runs the agent flow once a day: it takes the pending notes, groups them by topic
and classifies, writes and reviews. Each page's previous version is saved, so you can go
back.

It costs cents a day.

### Phase 2: chat with the notes (RAG)

A chatbot that answers by asking the notes, not by what the model remembers. RAG is that:
find the chunks that talk about the topic first and answer only with them.

- **Store**: with pgvector (a Postgres extension that stores vectors) on Supabase, a table of
  chunks with tags, metadata and embeddings (the numbers that represent the meaning of each
  chunk).
- **Index**: at the end of the daily pass, only the pages that changed.
- **Answer**: on each question, find the similar chunks and the LLM answers only with them,
  citing the page.

## Open questions

- Where notes come in: chat bot or web.
- How long the raw note is kept once its summary is published.

## Status

No code yet. It's the design, in case someone wants to start it.
