# AGENTS.md

Kolmi: apuntes colaborativos para una clase. Este repo es el producto; el material de la
clase vive en su propio repo.

## Qué hay

- `backend/` — API en Python + FastAPI.
- `frontend/` — web en Vue 3 + Vite.
- `docs/` — la idea y las especificaciones.

## Reglas

- **Una instancia por clase.** Nada de multitenant: cada clase despliega la suya, con su
  Supabase y su VPS.
- **Cero secretos en git.** Las claves de Supabase y `CODIGO_CLASE` van en `.env`, nunca al
  repo.
- **Los agentes van con el SDK de OpenAI.** Se pasa a LangGraph solo si hacen falta bucles o
  aprobación.
- Los documentos van en español y en `.md`.
