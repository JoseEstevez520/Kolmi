<p align="center">
  <img src="assets/logo.svg" alt="Kolmi" width="120">
</p>

<h1 align="center">Kolmi</h1>

<p align="center"><strong>Learn as a hive.</strong></p>

Kolmi is a collaboration app for a class. Everyone contributes a little — a note, a doubt, an
answer — and the AI turns it into shared notes. No one has to learn git or a framework to
take part.

## The thesis

Learning is social. People learn by asking, explaining and building on each other's ideas,
not alone. Vygotsky called it **social constructivism**: knowledge is co-constructed. Kolmi
is a hive for that.

> Everyone adds a drop; the class ends up with honeycomb.

## What it does today

- Students log in and leave raw notes.
- The hive works at night: once a day, a team of agents reads the new notes, groups them by
  topic, strips names and private data, and turns them into shared notes and pages.
- Raw notes stay private. Only the summary goes out.

More ways to contribute are coming — a chat with the notes, forums, whatever the class needs.
See [ROADMAP.md](ROADMAP.md).

## Self-hosting

Kolmi is self-hostable: each class runs its own instance (a small server and a Supabase
project). Nothing is shared between classes. The backend ships as a Docker image; build, run
and the nightly cron are in [backend/README.md](backend/README.md).

## Status

In development. Login, notes, the content tree, the admin panel with the AI log, and the
nightly pass all work. DeepSeek writes the pages in OpenUI Lang, in the class's language.

## Docs

- [The idea](docs/idea.md)
- [Authentication and users](docs/authentication.md)
- [Features and actions](docs/features.md)
- [Page format](docs/page-format.md)
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
