<script setup>
import { defineAsyncComponent, onMounted, ref } from 'vue'
import { Button, ThemeToggle } from 'elastic-ui'
import { PenLine } from '@lucide/vue'
import { useRoute } from 'vue-router'
import { api } from '../lib/api.js'
import { streamNoteAi } from '../lib/noteAi.js'
import { ready, session } from '../lib/auth.js'
import { inkOn, setInkOn } from '../lib/ink.js'

// Development only (/dev/note-ai): the real note editor with the AI on, against the real chat,
// without saving a note (so nothing reaches the class's pass). Each question is logged in
// chat_messages and counts against the day's limit, like any. Needs a signed-in session.
// ?note=<id> opens one of your notes (still not saved); ?fake streams made-up answers.
const NoteEditor = defineAsyncComponent(() => import('../components/NoteEditor.vue'))
const route = useRoute()

const body = ref(`## Spring Boot: beans

Un bean es un objeto que crea y gestiona el contenedor de Spring.

singleton por defecto → una sola instancia, todos los que lo piden reciben la misma

petición: navegador → controller → service → repository → BD

¿Qué diferencia hay entre @Component y @Bean?

¿cómo es una Raspberry Pi?`)
const editorKey = ref(0)

onMounted(async () => {
  const id = Number(route.query.note)
  if (!id) return
  try {
    const note = (await api.myNotes()).find((n) => n.id === id)
    if (note) {
      body.value = note.content
      editorKey.value++
    }
  } catch {
    /* not signed in: the sample stays */
  }
})

// "A mano" is the real setting (Settings, "Diagrams by hand"): a Figure's parts in ink.

// ?fake streams a made-up answer instead, to look at the editor without a session or a model.
const fake = route.query.fake !== undefined
const FAKE = {
  photo:
    '## Raspberry Pi\nUn ordenador completo en una placa del tamaño de una tarjeta: CPU, RAM, USB, HDMI, Ethernet y pines GPIO. Corre Linux.\n\n![Raspberry Pi 4 Model B](https://thumb.wikimedia.org/wikipedia/commons/thumb/f/f1/Raspberry_Pi_4_Model_B_-_Side.jpg/960px-Raspberry_Pi_4_Model_B_-_Side.jpg)\n*Imagen: Laserlicht, CC BY-SA 4.0, [Wikimedia Commons](https://commons.wikimedia.org/wiki/File:Raspberry_Pi_4_Model_B_-_Side.jpg)*\n\nSe alimenta por USB-C y gasta unos 5 W, así que puede quedarse encendida como servidor de la clase todo el curso sin problema.\n',
  ask: '## @Component vs @Bean\n\nAmbos registran beans; cambia quién crea el objeto → Spring o tú.\n\n```kolmi-ai\nroot = Answer([t])\nt = Table(["", "@Component", "@Bean"], [["Va sobre", "tu clase", "un método de una @Configuration"], ["Lo crea", "Spring, al escanear", "tú, en el método"]])\n```\n',
  complete:
    '```kolmi-ai\nroot = Answer([f])\nf = Figure("Varios personajes apuntan al mismo planeta", [g, a, p], "row")\ng = Group([l, le, h], "column")\nl = Chip("Luke", "violet")\nle = Chip("Leia", "violet")\nh = Chip("Han", "violet")\na = Arrow("homeworld")\np = Chip("Tatooine", "green", "globe", "Planet")\n```\n',
}
async function fakeAssist(text, note, onToken, onFix, onStatus) {
  if (/raspberry/i.test(text)) {
    onStatus?.('Using search images...')
    await new Promise((r) => setTimeout(r, 1500))
  }
  const answer = /raspberry/i.test(text)
    ? '%%ask\n' + FAKE.photo
    : text.endsWith('?')
      ? '%%ask\n' + FAKE.ask
      : '%%complete\n' + FAKE.complete
  for (const piece of answer.match(/.{1,12}/gs)) {
    await new Promise((r) => setTimeout(r, 40))
    onToken(piece)
  }
}

function realAssist(text, note, onToken, onFix, onStatus) {
  return streamNoteAi(text, note, { onToken, onFix, onStatus })
}
const assist = fake ? fakeAssist : realAssist
const aiError = ref('')
</script>

<template>
  <main class="mx-auto flex max-w-2xl flex-col gap-10 px-4 py-10">
    <div class="flex items-center gap-2 text-meta text-fg-muted">
      El editor real con la IA activada, contra el chat real. No guarda la nota.
      <Button
        variant="ghost"
        size="sm"
        :icon="PenLine"
        class="ml-auto"
        :class="inkOn && 'bg-bg-muted text-fg'"
        :aria-pressed="inkOn"
        @click="setInkOn(!inkOn)"
      >
        A mano
      </Button>
      <ThemeToggle />
    </div>
    <p v-if="!fake && ready && !session" class="m-0 rounded-lg bg-bg-muted p-3 text-copy">
      Para usar el modelo real hace falta iniciar sesión en este puerto:
      <RouterLink to="/login" class="underline">entrar</RouterLink>
      y vuelve aquí. O prueba el modo simulado:
      <RouterLink to="/dev/note-ai?fake" class="underline">?fake</RouterLink>.
    </p>
    <NoteEditor
      :key="editorKey"
      v-model="body"
      label="Nota de prueba"
      placeholder="Escribe…"
      :assist="assist"
      @ai-error="aiError = $event || 'La IA no ha podido responder.'"
    />
    <p v-if="aiError" class="m-0 text-meta text-danger">{{ aiError }}</p>
  </main>
</template>

