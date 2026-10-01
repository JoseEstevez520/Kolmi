# Frontend

Vue 3 + Vite web, starting from the class repo's web.

## Status

The code is here as a base, but it **doesn't run as is**: it imports the class content (the
`.md` under `modulos/` and `extra/`, through relative paths), and that content isn't here.
Before using it, adapt it:

- Replace the content imports with Kolmi's own pages.
- Adjust `src/data/paginas.js` and the router to the app screens (login, leave a note, my
  notes).

## Run it

```bash
npm install
npm run dev
```

Needs Node 20 or higher. The design and rules are in [`design.md`](design.md).
