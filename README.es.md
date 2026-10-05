<p align="center">
  <img src="assets/logo.svg" alt="Kolmi" width="104">
</p>

<h1 align="center">Kolmi</h1>

<p align="center">
  <strong>Kolmi convierte los apuntes sueltos de cada estudiante en páginas compartidas, ordenadas y visuales, sin que nadie toque git.</strong>
</p>

<p align="center">
  Para una clase, en su propio servidor.
</p>

<p align="center">
  <a href="docs/idea.md"><img src="https://img.shields.io/badge/Docs-Leer-2563eb?style=flat-square&logo=readthedocs&logoColor=white" alt="Documentación de Kolmi"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/Licencia-MIT-f59e0b?style=flat-square&logo=opensourceinitiative&logoColor=white" alt="Licencia MIT"></a>
</p>

<p align="center">
  <a href="#en-local">En local</a> ·
  <a href="README.md">English</a>
</p>

<p align="center">
  <img src="assets/readme/before-after.png" alt="Dos notas sueltas sobre Docker a la izquierda y, a la derecha, la página compartida que Kolmi escribió con ellas, ordenada en secciones con bloques de código" width="100%">
</p>

<p align="center"><sub>Dos notas sueltas entran, una página sale. Es una pasada nocturna real.</sub></p>

## ¿Qué es Kolmi?

Una clase sabe mucho, y casi todo se queda en el cuaderno de cada uno. Compartirlo a mano exige
saber git y un framework, así que casi nadie lo hace, aunque tenga algo que contar.

Kolmi quita ese paso. Cada persona deja sus apuntes en texto libre, sin formato. Una vez al día
la app lee los nuevos, junta los que tratan del mismo tema y escribe las páginas compartidas que
lee toda la clase, con diagramas, tablas y gráficas en vez de un montón de texto.

> Cada uno pone una gota; la clase se queda con un panal.

## Cómo funciona

Un equipo de agentes trabaja una vez al día. El portero lee cada nota nueva, quita nombres y
datos privados, descarta lo que no aporta y decide a qué página va. El agente de notas escribe lo
que el portero deja pasar, y el agente web lo convierte en una página.

| | Nota en bruto | Página compartida |
|---|---|---|
| Quién la ve | su autor y los admins, hasta que la pasada la recoge | toda la clase |
| Cómo es | texto libre y archivos | ordenada, con diagramas, tablas y gráficas |
| Nombres y datos privados | lo que hayas escrito | eliminados |

Las notas en bruto no salen nunca. Solo sale el resumen.

## Qué puedes hacer hoy

- **Dejar notas** en texto libre, con archivos adjuntos.
- **Leer las páginas compartidas**, que pueden llevar diagramas, tablas, gráficas y
  reproducciones de sesiones de agentes.
- **Recorrer el árbol de contenido de la clase**, con migas de pan, tabla de contenidos y
  enlaces a la página anterior y a la siguiente.
- **Lanzar la pasada nocturna** con un horario, o cuando quieras con "Run now" en Admin.
- **Revisar qué hizo la IA** en el registro: qué leyó, qué cambió y de qué notas partió.
- **Editar el árbol** a mano en Admin: crear, renombrar, mover, reordenar y borrar.
- **Fijar el horario y el idioma de la clase**, español o inglés.

<p align="center">
  <img src="assets/readme/diagram.png" alt="Una página escrita por Kolmi, con un diagrama de cuatro roles de agente y lo que puede hacer cada uno" width="100%">
</p>

<p align="center"><sub>Una página puede llevar más que texto. El diagrama es parte de la página.</sub></p>

## En local

Necesitas Python 3, Node 20 o superior, un proyecto de Supabase y una clave de API de un modelo.

```bash
# backend, en :8000
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env    # Supabase, CLASS_CODE y las claves del modelo
uvicorn app.main:app --reload

# frontend, en :5173
cd frontend
npm install
cp .env.example .env
npm run dev
```

Antes, crea las tablas con [supabase/schema.sql](supabase/schema.sql). Los `.env` se quedan fuera
de git. Cada clase lleva su propia instancia, y el backend se publica como imagen de Docker:
cómo construirla, ejecutarla y programar la pasada está en [backend/README.md](backend/README.md)
(en inglés).

> **Estado: en desarrollo.** Lo siguiente es un chat con los apuntes y foros. Mira
> [ROADMAP.md](ROADMAP.md) (en inglés).

## Documentación

La documentación está en inglés.

- [La idea](docs/idea.md): el problema, el equipo de agentes y por qué las notas en bruto son privadas.
- [Autenticación y usuarios](docs/authentication.md): cuentas, roles y el código de clase.
- [Funciones y acciones](docs/features.md): qué hace la app y cómo se construye cada acción.
- [Formato de página](docs/page-format.md): cómo llega una página de la pasada a la pantalla.
- [Pruebas con casos reales](docs/testing.md): el plan para probarlo antes de que lo use la clase.
- [Datos y privacidad](docs/privacy.md): qué se guarda, quién lo ve y qué sale de la instancia.
- [Tono de marca](docs/brand-tone.md): cómo suena Kolmi.

## Ecosistema

- [elastic-ui](https://github.com/JoseEstevez520/elastic-ui) es la librería de componentes con
  la que está hecha la web.
- [ies-teis-daw2](https://github.com/JoseEstevez520/ies-teis-daw2) guarda el material propio de
  la clase. Kolmi no lo necesita para funcionar.

## Licencia

Kolmi es de código abierto bajo la [licencia MIT](LICENSE). Los problemas de seguridad se
comunican según [SECURITY.md](SECURITY.md), nunca en una issue pública.
