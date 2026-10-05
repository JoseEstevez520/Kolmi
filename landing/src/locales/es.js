// The landing's texts in Spanish, key for key as en.js, following README.es.md.

const repo = 'https://github.com/JoseEstevez520/Kolmi'
const blob = `${repo}/blob/main`

export default {
  meta: {
    title: 'Kolmi · Aprende en colmena',
    description:
      'Kolmi es un cuaderno que escribe toda la clase entre todos: cada uno deja sus apuntes y la IA los convierte en páginas ordenadas.',
  },

  nav: {
    label: 'Secciones',
    how: 'Cómo funciona',
    pages: 'Páginas',
    run: 'Instalar',
    code: 'Código',
    switchLocale: 'Read in English',
  },

  hero: {
    slogan: 'Aprende en colmena.',
    lead: 'Un cuaderno que escribe toda la clase entre todos. Cada uno deja sus apuntes y, de noche, la IA los convierte en páginas ordenadas, con diagramas, gráficas y piezas interactivas.',
    scope: 'Para una clase, en su propio servidor.',
    primary: 'Móntalo en tu clase',
    secondary: 'Mira cómo funciona',
  },

  demo: {
    label: 'Dos notas sueltas sobre CI/CD y la página compartida que Kolmi escribió con ellas',
    notes: [
      'ci/cd: cada vez que hago push github actions pasa los tests solo. si pasan construye la imagen de docker. todo va en un yaml dentro de .github/workflows',
      'despues del build la imagen se sube a un registry y el servidor la baja de ahi. si fallan los tests no se despliega nada. para hacer rollback se despliega la imagen anterior',
    ],
    noteDate: 'Anoche',
    noteStatus: 'En los apuntes',
    page: {
      title: 'CI/CD con GitHub Actions y Docker',
      intro:
        'CI/CD automatiza los pasos que hacías a mano tras cada cambio: pasar los tests, construir la imagen y desplegarla. Cada push al repositorio dispara **GitHub Actions**, el servicio de GitHub que ejecuta estas tareas automáticas. El pipeline pasa los tests, construye una **imagen de Docker** (la aplicación empaquetada con todo lo necesario para ejecutarla), la sube a un **registry** (un servicio que guarda imágenes de Docker) y el servidor descarga de ahí la imagen nueva.',
      diagramLabel:
        'Un git push dispara GitHub Actions, que pasa los tests, construye la imagen de Docker y la sube a un registry; el servidor descarga la imagen de ahí',
      push: 'git push',
      triggers: 'dispara',
      actions: 'GitHub Actions',
      actionsNote: 'ejecuta las tareas automáticas',
      tests: 'tests',
      build: 'docker build',
      pushImage: 'docker push',
      registry: 'registry',
      pulls: 'descarga',
      server: 'el servidor baja la imagen',
      conclusion: 'Todo el camino se hace solo tras cada push.',
    },
    caption: 'Dos notas sueltas entran, una página sale. Es una pasada nocturna real.',
  },

  what: {
    title: '¿Qué es Kolmi?',
    body: [
      'En una clase cada uno toma sus propios apuntes y nadie tiene el cuaderno entero. Kolmi lo hace entre todos.',
      'Cada persona deja lo que tiene, con sus palabras y sin formato. De noche trabaja la colmena: una IA lee lo nuevo, junta lo que va unido y escribe las páginas de la clase. Cada página se organiza como una buena guía de estudio, con un diagrama donde una idea tiene partes, una gráfica donde importan los números y piezas interactivas para probar cosas.',
    ],
    quote: 'Cada uno pone una gota; la clase se queda con un panal.',
    scope: 'Kolmi es para una clase. Cada clase lleva su propia copia, con sus propios datos.',
  },

  how: {
    title: 'Cómo funciona',
    body: 'Un equipo de agentes trabaja una vez al día. El **portero** lee cada nota nueva, quita nombres y datos privados, descarta lo que no aporta y decide a qué página va. El **agente de notas** escribe lo que el portero deja pasar, y el **agente web** la maqueta como página.',
    lead: 'Mira una pasada con las dos notas de arriba. Es una sesión inventada y resumida.',
    intro: 'De noche la pasada se despierta y recoge lo nuevo.',
    events: [
      {
        kind: 'prompt',
        text: 'Pasada nocturna · 2 notas nuevas',
        note: 'Nadie pulsa nada: la pasada la despierta un horario.',
      },
      {
        kind: 'step',
        icon: 'gatekeeper',
        running: 'El portero lee 2 notas nuevas',
        done: 'El portero leyó 2 notas',
        output:
          'Mismo tema: CI/CD.\nSin nombres ni datos privados.\nNada que descartar.\nVa a: Despliegue › CI/CD con GitHub Actions y Docker',
        duration: 1800,
        note: 'El portero va primero: las notas en bruto nunca llegan a los otros dos.',
      },
      {
        kind: 'step',
        icon: 'notes',
        running: 'El agente de notas escribe el tema',
        done: 'El agente de notas escribió el tema',
        duration: 1600,
        note: 'Dos notas se vuelven una explicación, con el estilo de la casa.',
      },
      {
        kind: 'step',
        icon: 'web',
        running: 'El agente web maqueta la página',
        done: 'El agente web actualizó la página',
        diff: {
          file: 'ci-cd.md',
          before: '# CI/CD con GitHub Actions y Docker\n',
          after:
            '# CI/CD con GitHub Actions y Docker\n\nCada push dispara GitHub Actions…\n\n<Diagrama: push → tests → build → registry → servidor>\n\n**Todo el camino se hace solo tras cada push.**\n',
        },
        duration: 1800,
        note: 'La página lleva un diagrama, porque la idea tiene partes.',
      },
      {
        kind: 'answer',
        text: 'Hecho: 1 página actualizada con 2 notas. Las notas en bruto se quedan en el servidor.',
        note: 'Solo sale el resumen.',
      },
    ],
    table: {
      label: 'Una nota en bruto y una página compartida, comparadas',
      head: ['', 'Nota en bruto', 'Página compartida'],
      rows: [
        ['Quién la ve', 'su autor y los admins, hasta que la pasada la recoge', 'toda la clase'],
        ['Cómo es', 'texto libre y archivos', 'organizada, con diagramas, tablas, gráficas y piezas interactivas'],
        ['Nombres y datos privados', 'lo que hayas escrito', 'eliminados'],
      ],
    },
    conclusion: 'Las notas en bruto no salen nunca. Solo sale el resumen.',
  },

  today: {
    title: 'Qué puedes hacer hoy',
    student: {
      title: 'Como estudiante',
      items: [
        '**Dejar una nota** en texto libre, con archivos adjuntos, cuando tengas algo que aportar.',
        '**Leer las páginas de la clase**: diagramas, gráficas, tablas, reproducciones paso a paso de sesiones de agentes y piezas interactivas.',
        '**Moverte** con el árbol de contenido, una tabla de contenidos y enlaces a la página anterior y a la siguiente.',
        '**Consultar el horario de la clase.**',
        '**Hacer un recorrido corto** la primera vez que entras.',
        '**Llevarte el cuaderno**: descargar todas las páginas, o una sección, como archivos Markdown, para guardarlas o subirlas a NotebookLM.',
      ],
    },
    admin: {
      title: 'Como admin',
      items: [
        '**Lanzar la pasada nocturna** con un horario, o cuando quieras con “Run now”.',
        '**Revisar qué hizo la IA** en el registro: qué leyó, qué cambió y de qué notas partió.',
        '**Organizar el árbol** a mano: crear, renombrar, mover, reordenar y borrar.',
        '**Fijar el horario y el idioma de la clase**, español o inglés.',
      ],
    },
    schedule: {
      lead: 'La pasada corre cuando dice el admin. Pruébalo: son los mismos controles de la app.',
      days: 'Días en que corre la pasada',
      times: 'Horas a las que corre la pasada',
      addTime: 'Añadir una hora',
      words: { everyDay: 'Todos los días', weekdays: 'Entre semana', weekends: 'Fines de semana', none: 'Nunca' },
    },
  },

  pages: {
    title: 'Qué cabe en una página',
    lead: 'Una página es más que texto. El agente web dibuja cada idea como lo que es. Estas piezas salen de las propias páginas de la clase.',
    diagram: {
      title: 'Un diagrama, donde una idea tiene partes',
      label:
        'Un mismo modelo piensa en todos los agentes; lo que cambia es el papel. El constructor edita y ejecuta comandos, el planificador pregunta antes, el tutor no hace ninguna de las dos y el explorador solo lee',
      model: 'Un mismo modelo · piensa en todos',
      builder: 'Constructor · Build, en OpenCode',
      builderNote: 'Hace el cambio que le pides.',
      planner: 'Planificador · Plan, en OpenCode',
      plannerNote: 'Piensa el cambio y te lo propone.',
      tutor: 'Tutor · hecho por ti',
      tutorNote: 'Te explica, pero no te resuelve la práctica.',
      explorer: 'Explorador · un subagente',
      explorerNote: 'Otro agente lo manda a buscar, y vuelve solo con la respuesta.',
      edits: 'Edita',
      runs: 'Ejecuta comandos',
      reads: 'Lee',
      yes: 'sí',
      asks: 'te pregunta',
      no: 'no',
      conclusion: 'Lo que cambia de un agente a otro no es el modelo, son sus instrucciones y sus permisos.',
    },
    chart: {
      title: 'Una gráfica, donde importan los números',
      label: 'Calidad frente a coste por tarea resuelta: casi la misma calidad, de veinte céntimos a setenta y cuatro dólares',
      x: 'Coste por tarea resuelta',
      y: 'SWE-bench Verified',
      series: 'Modelos',
      caption: 'Datos: AgentMarketCap, abril de 2026, como los muestra la página de la clase.',
      conclusion: 'Pagar más no siempre compra más calidad.',
    },
    code: {
      title: 'Código para copiar, y un aviso donde importa',
      lead: 'El pipeline es un archivo YAML en `.github/workflows`:',
      after: '`needs: test` hace que el job de build espere al de test. Si los tests fallan, el build no corre y no se despliega nada.',
      warning:
        'Usa una etiqueta distinta para cada versión, por ejemplo `app:v1`, `app:v2`. No sobrescribas la única etiqueta con el build nuevo si quieres poder volver atrás.',
    },
  },

  run: {
    title: 'En local',
    lead: 'Necesitas Python 3, Node 20 o superior, un proyecto de Supabase y una clave de API de un modelo.',
    commands: [
      '# backend, en :8000',
      'cd backend',
      'python3 -m venv .venv && source .venv/bin/activate',
      'pip install -r requirements-dev.txt',
      'cp .env.example .env    # Supabase, CLASS_CODE y las claves del modelo',
      'uvicorn app.main:app --reload',
      '',
      '# frontend, en :5173',
      'cd frontend',
      'npm install',
      'cp .env.example .env',
      'npm run dev',
    ].join('\n'),
    after:
      'Crea antes las tablas con `supabase/schema.sql`. Los `.env` se quedan fuera de git. Cada clase lleva su propia instancia, y el backend se distribuye como imagen de Docker: cómo construirla, arrancarla y programar la pasada está en el README del backend.',
    backendReadme: 'README del backend',
    status: {
      title: 'En desarrollo',
      body: 'Lo siguiente es “Pregunta a la colmena”, un chat con los apuntes, y foros.',
      roadmap: 'Ver la hoja de ruta (en inglés)',
    },
  },

  docs: {
    title: 'Documentación',
    items: [
      { title: 'La idea', text: 'El problema, el equipo de agentes y por qué las notas en bruto son privadas.', href: `${blob}/docs/idea.md` },
      { title: 'Autenticación y usuarios', text: 'Cuentas, roles y el código de clase.', href: `${blob}/docs/authentication.md` },
      { title: 'Funciones y acciones', text: 'Qué hace la app y cómo se construye cada acción.', href: `${blob}/docs/features.md` },
      { title: 'Formato de página', text: 'Cómo llega una página de la pasada a la pantalla.', href: `${blob}/docs/page-format.md` },
      { title: 'Pruebas con casos reales', text: 'El plan para probarlo antes de que lo use la clase.', href: `${blob}/docs/testing.md` },
      { title: 'Datos y privacidad', text: 'Qué se guarda, quién lo ve y qué sale de la instancia.', href: `${blob}/docs/privacy.md` },
      { title: 'Tono de marca', text: 'Cómo suena Kolmi.', href: `${blob}/docs/brand-tone.md` },
      { title: 'Imágenes de marca', text: 'Cómo hacer una imagen que parezca de Kolmi.', href: `${blob}/docs/brand-visuals.md` },
    ],
  },

  ecosystem: {
    title: 'Ecosistema',
    items: [
      { title: 'elastic-ui', text: 'La librería de componentes con la que está hecha la web.', href: 'https://github.com/JoseEstevez520/elastic-ui' },
      { title: 'ies-teis-daw2', text: 'El repositorio de la clase, con sus herramientas y el material del que salieron las primeras páginas.', href: 'https://github.com/JoseEstevez520/ies-teis-daw2' },
    ],
  },

  footer: {
    cta: 'Lleva la colmena a tu clase.',
    primary: 'Ver el código',
    license: 'Código abierto con licencia MIT.',
    security: 'Los problemas de seguridad van por SECURITY.md, nunca en un issue público.',
  },

  links: {
    repo,
    backendReadme: `${blob}/backend/README.md`,
    roadmap: `${blob}/ROADMAP.md`,
    license: `${blob}/LICENSE`,
    security: `${blob}/SECURITY.md`,
  },
}
