# Autenticación y usuarios

Cuentas, login y registro de la app de [Notas de clase](README.md). Es solo esta parte: el
job de agentes, las páginas de apuntes y el chat/RAG quedan fuera.

## Contexto

La app es para una sola clase, no para varias (nada de multitenant). Los alumnos dejan notas
y un job diario las convierte en apuntes. Aquí solo van las cuentas.

Stack:

- **Supabase** (en la nube, plan gratis): Auth y Postgres.
- **Backend propio** en un VPS, con Python y FastAPI.
- **Frontend**: la web que ya existe, adaptada.

## Login

Dos métodos a la vez:

1. **Google**, con el provider de Supabase Auth.
2. **Email y contraseña**, con el Auth nativo de Supabase.

Las contraseñas las guarda Supabase Auth (hasheadas); ni el backend ni el admin las ven. El
formulario de email llama directo a `supabase.auth.signUp` / `signInWithPassword` desde el
frontend. Para recuperarla, `resetPasswordForEmail`.

En Supabase, Authentication → Providers → Email, se desactiva "Confirm email" al registrarse,
o se configura un SMTP propio (Resend, Brevo) si se quiere activar.

## Código de clase y perfil

Tras el **primer** login (con cualquier método), si el usuario no tiene perfil, se le pide un
**código de clase** y un **nombre visible** (prellenado con el de Google si existe). El código
está en una variable de entorno del backend, `CODIGO_CLASE`. Sin perfil no se pueden dejar
notas.

## Base de datos

Dos tablas en Supabase:

```sql
create table perfiles (
  id uuid primary key references auth.users(id) on delete cascade,
  nombre text not null,
  aprobado boolean default true,
  creado timestamptz default now()
);

create table notas (
  id bigserial primary key,
  usuario_id uuid references perfiles(id) on delete cascade,
  contenido text not null,
  estado text default 'pendiente',  -- pendiente | procesada | descartada
  creada timestamptz default now()
);
```

Las dos con RLS (Row Level Security: cada fila decide quién puede leerla o escribirla)
activado y **sin políticas públicas**: solo entra el backend, con la service role key.

## Backend (FastAPI)

Todas las rutas reciben `Authorization: Bearer <access_token de Supabase>` y lo validan con
`supabase.auth.get_user(token)`.

| Ruta | Qué hace |
|---|---|
| `GET /perfil` | el perfil del usuario, o 404 si no existe |
| `POST /registro` | `{codigo, nombre}`: valida el código contra `CODIGO_CLASE` y crea el perfil. 403 si el código no vale |
| `POST /notas` | `{contenido}`: exige perfil con `aprobado = true` y guarda la nota como `pendiente` |
| `GET /notas/mias` | las notas del propio usuario |

Variables de entorno: `SUPABASE_URL`, `SUPABASE_SERVICE_KEY`, `CODIGO_CLASE`. La service key
no sale del backend.

## Frontend

- Pantalla de login: botón "Entrar con Google", formulario de email y contraseña, y enlaces a
  "Registrarse" y "He olvidado mi contraseña".
- `@supabase/supabase-js` con la anon key (pública), solo para el login.
- Tras entrar, llama a `GET /perfil`; si da 404, muestra la pantalla de código y nombre.
- Pantalla principal: formulario para dejar una nota y lista de "mis notas".
- Texto de privacidad visible: "Usamos tu email solo para que puedas entrar en la app de la
  clase."

## Configuración manual

1. Google Cloud Console: crear credenciales OAuth (Web) con la redirect URI que indica
   Supabase.
2. Supabase → Authentication → Providers → Google: pegar el client ID y el secret.
3. Supabase → Authentication → URL Configuration: añadir el dominio de la web.

Estos pasos van también en el README del proyecto cuando se monte.

## Fuera de alcance

El job diario de agentes, las páginas de apuntes y el chat/RAG.
