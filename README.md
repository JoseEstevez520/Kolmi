<p align="center">
  <img src="assets/logo.svg" alt="Kolmi" width="120">
</p>

# Kolmi

**Aprende en colmena.**

Apuntes colaborativos para una clase. Los alumnos dejan notas en crudo y un equipo de agentes
las convierte en páginas de apuntes, sin que nadie tenga que tocar git ni Vue.

El nombre viene de "colmena": cada uno aporta su parte y entre todos sale algo completo.

## Cómo funciona

1. Alguien deja una nota (texto libre) desde la web.
2. La nota se guarda en privado, en el servidor.
3. Una vez al día, un cron despierta al equipo de agentes.
4. El portero junta las notas del mismo tema, quita nombres y datos, descarta lo que no
   aporta y decide dónde va cada una.
5. Los agentes de apuntes la redactan y el de la web la publica.

El detalle, en [docs/idea.md](docs/idea.md). La parte de cuentas y login, en
[docs/autenticacion.md](docs/autenticacion.md). Cómo habla la app, en
[docs/tono-de-marca.md](docs/tono-de-marca.md).

## Stack

- **Backend**: Python + FastAPI, en un VPS.
- **Base de datos y auth**: Supabase.
- **Frontend**: Vue 3 + Vite.
- **Agentes**: SDK de OpenAI; LangGraph si hacen falta bucles o aprobación.

## Estado

Diseño. Todavía no hay código.

## Estructura

```
backend/   - API en Python + FastAPI
frontend/  - web en Vue 3 + Vite
docs/      - la idea, las especificaciones y el tono de marca
assets/    - logo y demás recursos
```
