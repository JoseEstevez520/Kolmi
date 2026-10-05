<p align="center">
  <img src="assets/logo.svg" alt="Kolmi" width="120">
</p>

<h1 align="center">Kolmi</h1>

<p align="center"><strong>Learn as a hive.</strong></p>

Kolmi is a collaboration app for a class. Everyone takes their own notes, and Kolmi turns them
into pages the whole class can read: well ordered, with diagrams and tables, not a pile of text.
Nobody has to learn git or a framework to take part.

<p align="center">
  <img src="docs/screenshots/diagram.png" alt="A page written by Kolmi, with a diagram of four agent roles and what each one may do" width="860">
</p>

<p align="center"><sub>A page the hive wrote from the class's notes. The diagram is part of the page.</sub></p>

## How it works

1. **You leave a note.** Free text, whenever you have something to add: a note, a doubt, an
   answer.
2. **Kolmi works at night.** Once a day a team of agents reads the new notes, joins the ones
   about the same topic and strips names and private data.
3. **The class reads the result.** The notes become shared pages, in the class's language.

Raw notes stay private. Only the summary goes out.

> Everyone adds a drop; the class ends up with honeycomb.

## What a page can hold

<table>
  <tr>
    <td width="50%"><img src="docs/screenshots/replay.png" alt="An agent session replayed step by step: the request, the files it read and edited, and its answer"></td>
    <td width="50%"><img src="docs/screenshots/chart.png" alt="A scatter chart of quality against cost per task, on a logarithmic axis"></td>
  </tr>
  <tr>
    <td align="center"><sub>A session you can play or step through.</sub></td>
    <td align="center"><sub>A chart with real axes.</sub></td>
  </tr>
</table>

## Where it's going

Notes are the first way to contribute. Next come a chat with the notes, forums and whatever
else the class needs. See [ROADMAP.md](ROADMAP.md).

## Self-hosting

Each class runs its own instance: a small server and a Supabase project. Nothing is shared
between classes. The backend ships as a Docker image; build, run and the cron that runs the
pass are in [backend/README.md](backend/README.md).

To try it locally you need Python 3, Node 20 or higher, a Supabase project and an API key for
a model:

```bash
# backend, on :8000
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env    # Supabase, CLASS_CODE and the model keys
uvicorn app.main:app --reload

# frontend, on :5173
cd frontend
npm install
cp .env.example .env
npm run dev
```

Create the tables first with [supabase/schema.sql](supabase/schema.sql). The `.env` files stay
out of git.

## Status

In development. Login, notes with files, the content tree, the admin panel with the AI log, the
class timetable and the nightly pass all work.

## Docs

- [The idea](docs/idea.md)
- [Authentication and users](docs/authentication.md)
- [Features and actions](docs/features.md)
- [Page format](docs/page-format.md)
- [Testing with real cases](docs/testing.md)
- [Data and privacy](docs/privacy.md)
- [Brand tone](docs/brand-tone.md)

## Structure

```
backend/   - Python + FastAPI API
frontend/  - Vue 3 + Vite web
docs/      - the idea, specs and brand tone
assets/    - logo and other resources
```

## License

MIT. See [LICENSE](LICENSE).
