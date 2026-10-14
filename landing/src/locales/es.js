// The landing's texts in Spanish, key for key as en.js, following README.es.md.

const repo = 'https://github.com/JoseEstevez520/Kolmi'
const blob = `${repo}/blob/main`

export default {
  meta: {
    title: 'Kolmi · Aprende en colmena',
    description:
      'Kolmi es donde una clase junta sus apuntes: cada uno deja los suyos y, cada noche, una IA los convierte en páginas compartidas que la clase puede leer y a las que puede preguntar.',
  },

  nav: {
    label: 'Secciones',
    how: 'Cómo funciona',
    chat: 'Chat',
    ai: 'Tu IA',
    code: 'Código',
    switchLocale: 'Read in English',
  },

  hero: {
    slogan: 'Aprende en colmena.',
    lead: 'Los apuntes de la clase están repartidos entre chats y carpetas en la nube, y nadie sabe de cuáles fiarse. Kolmi los junta en un sitio: cada uno deja los suyos y, cada noche, una IA los convierte en páginas compartidas que la clase puede leer y a las que puede preguntar.',
    scope: 'Para una clase, en su propio servidor.',
    primary: 'Móntalo en tu clase',
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
        'CI/CD automatiza lo que hacías a mano tras cada cambio. Cada push dispara **GitHub Actions**: pasa los tests, construye una **imagen de Docker** y la sube a un **registry**, de donde la descarga el servidor.',
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
      'Todas las clases acaban igual. Los apuntes están en chats, en carpetas en la nube y en fotos de la pizarra. Dos personas apuntaron lo mismo de forma distinta, nadie sabe qué versión es la buena, y lo que necesitas antes del examen está en el cuaderno de otro.',
      'En Kolmi cada uno deja lo que tiene, con sus palabras y sin formato. Cada noche la colmena lee lo nuevo y juzga cada nota: la junta con lo que la clase ya tiene, quita nombres y datos privados y descarta lo que no aporta. Lo que queda se convierte en las páginas de la clase, organizadas como una guía de estudio, con un diagrama donde una idea tiene partes y una tabla o gráfica donde importan los números. La nota en bruto sigue siendo privada.',
    ],
    scope: 'Kolmi es para una clase. Cada clase lleva su propia copia, con sus propios datos. Un admin es un estudiante que cuida de la clase; no hay cuenta de profesor.',
  },

  how: {
    title: 'Cómo funciona',
    body: 'Un equipo de agentes trabaja una vez al día, con el horario que fija un admin. El **portero** lee cada nota nueva, quita nombres y datos privados, descarta lo que no aporta y decide a qué página va. El motivo de cada decisión queda en el registro de la IA. El **agente de notas** escribe lo que el portero deja pasar, y el **agente web** la maqueta como página.',
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
  },

  ask: {
    title: 'Pregunta a los apuntes',
    body: 'El chat responde con las páginas de la clase, no con lo que un modelo recuerda. Busca los pasajes más cercanos a tu pregunta, responde con ellos y dice qué páginas usó. Si pides una tabla o los pasos de un procedimiento, la dibuja.',
    label: 'Una conversación inventada: una pregunta respondida con los apuntes, con sus fuentes, y una nota que el chat propone crear, a la espera de confirmación',
    question: '¿Qué dicen los apuntes sobre los scopes de un bean?',
    answer: 'Un scope decide cuándo crea Spring un bean y cuánto tiempo se reutiliza. Casi todos son `singleton`, uno para toda la aplicación. Usa `request` cuando el bean guarda estado de una sola petición.',
    sources: 'Fuentes: Scopes de un bean',
    request: 'Apunta que el examen llega hasta la unidad 4.',
    reply: 'Aquí tienes la nota. No se guarda nada hasta que la confirmes.',
    proposal: {
      label: 'Crear una nota',
      done: 'Nota creada',
      args: { Título: 'Examen', Texto: 'El examen llega hasta la unidad 4.' },
      result: 'Nota enviada. Esta noche la colmena la lee.',
    },
    caption: 'Una conversación inventada. La tarjeta funciona, sin nada detrás.',
    acts: 'El chat puede actuar, pero nunca por su cuenta. Todo lo que cambia algo vuelve como una tarjeta que enseña qué cambiaría, y ocurre cuando lo confirmas. Un estudiante puede dejar y editar sus notas así. Un admin además puede mover páginas, editar el horario y cuidar de la gente de la clase. También puede avisar de un problema de la app. Un admin enciende el chat y fija un límite diario por estudiante.',
  },

  ai: {
    title: 'Tu propia IA, conectada',
    body: 'Kolmi también es un servidor MCP, así que la IA que ya usas puede trabajar con los apuntes de la clase en tu nombre. Pongamos que el curso está en Moodle y el código de las prácticas en un repo de GitHub. Con Moodle, GitHub y Kolmi conectados al mismo asistente, le pides que lea el material de esta semana y lo pase a limpio. Lee primero el árbol de la clase, mira lo que ya dicen las páginas y deja una nota por tema, cada una con el enlace de donde salió. La IA de un admin puede, en cambio, integrar el material directamente en una página.',
    label: 'Tu asistente de IA lee Moodle y un repo de GitHub, y deja notas en Kolmi',
    material: 'Tu material',
    moodle: 'Moodle',
    repo: 'repo de GitHub',
    reads: 'lee',
    assistant: 'tu IA',
    leaves: 'deja',
    notes: 'notas en Kolmi',
    connect: 'En Ajustes, en **Conecta tu IA**, le pones nombre a la conexión y recibes un token, que se muestra una sola vez, y el comando para tu cliente con la dirección de tu instancia ya puesta. Para Claude Code tiene esta forma:',
    command: 'claude mcp add --transport http kolmi <url> --header "Authorization: Bearer <token>"',
    limits: 'Hay instrucciones para Claude Code, Gemini CLI y Codex CLI, y para cualquier otro cliente que acepte un token de portador. Las apps de chat cuyos conectores piden iniciar sesión con OAuth aún no se admiten. Leer es libre. Tu IA actúa con tu rol, y todo lo que cambia algo te lo pregunta antes.',
  },

  today: {
    title: 'Alrededor de los apuntes',
    items: [
      { title: 'Apuntes en directo', text: 'Durante una clase, alguien comparte lo que escribe y el resto lo sigue según aparece. La nota sigue siendo una nota normal y pasa por la pasada nocturna.' },
      { title: 'El horario', text: 'La semana de la clase en una pantalla. Un admin la edita arrastrando sobre la cuadrícula.' },
      { title: 'Descargas', text: 'Cualquier sección como archivos Markdown, para guardarla o subirla a NotebookLM. Las páginas también pueden llevar archivos para descargar.' },
      { title: 'El registro de la IA', text: 'Qué leyó cada pasada, qué cambió y por qué descartó una nota.' },
      { title: 'Los admins son estudiantes', text: 'Un estudiante con más permisos: lanza la pasada, organiza el árbol y deja entrar a gente nueva.' },
      { title: 'Una interfaz tranquila', text: 'Poco texto, iconos que dicen su nombre al pasar el ratón, y la app en español o inglés.' },
    ],
  },

  run: {
    title: 'Móntalo en tu clase',
    body: 'Necesitas Python 3, Node 20 o superior, un proyecto de Supabase y una clave de API de un modelo. El backend se publica como imagen de Docker, y la pasada nocturna es una tarea de cron en el mismo servidor. Los pasos están en el README y en el del backend (en inglés).',
    scope: 'Cada clase lleva su propia instancia, con su propio proyecto de Supabase y su propio servidor. No se comparte nada entre clases, y las claves se quedan en tu `.env`.',
    cta: 'Leer los pasos',
  },

  docs: {
    title: 'Documentación',
    items: [
      { title: 'La idea', text: 'El problema, el equipo de agentes y por qué las notas en bruto son privadas.', href: `${blob}/docs/idea.md` },
      { title: 'Autenticación y usuarios', text: 'Cuentas, roles y el código de clase.', href: `${blob}/docs/authentication.md` },
      { title: 'Funciones y acciones', text: 'Qué hace la app y cómo se construye cada acción.', href: `${blob}/docs/features.md` },
      { title: 'El chat', text: 'Qué escribe el modelo, cómo viaja una pregunta y cómo se propone un cambio.', href: `${blob}/docs/chat.md` },
      { title: 'El MCP', text: 'Conectar tu propia IA: tokens, recursos, prompt y evals.', href: `${blob}/docs/mcp.md` },
      { title: 'Acciones como herramientas', text: 'Cómo cada función es una acción que comparten la web, el chat y el MCP.', href: `${blob}/docs/tools.md` },
      { title: 'Apuntes en directo', text: 'Seguir una clase a través de los apuntes de alguien.', href: `${blob}/docs/live-notes.md` },
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
    ],
  },

  footer: {
    contact: '¿Dudas, o lo quieres en tu clase? Escríbeme.',
    cta: 'Lleva la colmena a tu clase.',
    primary: 'Ver el código',
    license: 'Código abierto con licencia MIT.',
    security: 'Los problemas de seguridad van por SECURITY.md, nunca en un issue público.',
  },

  links: {
    repo,
    linkedin: 'https://www.linkedin.com/in/jose-est%C3%A9vez-b9b761388',
    run: `${blob}/README.es.md#en-local`,
    license: `${blob}/LICENSE`,
    security: `${blob}/SECURITY.md`,
  },
}
