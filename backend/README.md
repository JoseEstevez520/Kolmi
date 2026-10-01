# Backend

API en Python + FastAPI. Todavía no hay código.

## Qué hará

- Validar el token de Supabase en cada petición.
- Cuentas: `GET /perfil`, `POST /registro`, `POST /notas`, `GET /notas/mias`.
- El job diario de agentes.

El detalle de las cuentas está en [`../docs/autenticacion.md`](../docs/autenticacion.md).

## Variables de entorno

`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CODIGO_CLASE`. En `.env`, nunca en git.
