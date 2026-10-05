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
    code: 'Código',
    switchLocale: 'Read in English',
  },

  hero: {
    slogan: 'Aprende en colmena.',
    lead: 'Un cuaderno que escribe toda la clase entre todos. Cada uno deja sus apuntes y, de noche, la IA los convierte en páginas ordenadas, con diagramas, gráficas y piezas interactivas.',
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
  },

  today: {
    title: 'Qué puedes hacer hoy',
    student: {
      title: 'Como estudiante',
      items: [
        { title: 'Dejar una nota', text: 'En texto libre, con archivos, cuando tengas algo que aportar.' },
        { title: 'Leer las páginas de la clase', text: 'Diagramas, gráficas, tablas, reproducciones y piezas interactivas.' },
        { title: 'Moverte', text: 'Un árbol de contenido, una tabla de contenidos, la página anterior y la siguiente.' },
        { title: 'Consultar el horario', text: 'La semana de la clase, de un vistazo.' },
        { title: 'Hacer un recorrido corto', text: 'La primera vez que entras.' },
        { title: 'Llevarte el cuaderno', text: 'Todas las páginas en Markdown, para guardarlas o subirlas a NotebookLM.' },
      ],
    },
    admin: {
      title: 'Como admin',
      items: [
        { title: 'Lanzar la pasada nocturna', text: 'Con un horario, o al momento con “Run now”.' },
        { title: 'Revisar qué hizo la IA', text: 'Qué leyó, qué cambió y de qué notas partió.' },
        { title: 'Organizar el árbol', text: 'Crear, renombrar, mover, reordenar y borrar.' },
        { title: 'Fijar horario e idioma', text: 'La semana de la clase, en español o inglés.' },
      ],
    },
  },

  pages: {
    title: 'Qué cabe en una página',
    lead: 'El agente web organiza cada página como una buena guía de estudio: por secciones, con la pieza justa para cada idea.',
    label: 'Las notas sueltas pasan al agente web, que las convierte en una página organizada con secciones, diagramas, gráficas, tablas, código, reproducciones y piezas interactivas',
    notes: 'Notas sueltas',
    agent: 'agente web',
    page: 'Una página organizada',
    pieces: ['Secciones', 'Diagramas', 'Gráficas', 'Tablas', 'Código', 'Reproducciones', 'Piezas interactivas'],
    conclusion: 'Una pieza donde ayuda, y texto donde basta con texto.',
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
    license: `${blob}/LICENSE`,
    security: `${blob}/SECURITY.md`,
  },
}
