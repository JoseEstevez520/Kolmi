<script setup>
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'
import { Button, ChatComposer, ChatMorph, Markdown, ThemeToggle } from 'elastic-ui'
import { PenLine, X } from '@lucide/vue'
import ChatConversation from '../components/ChatConversation.vue'
import NoteAiFence from '../components/NoteAiFence.vue'
import PageLayout from '../components/PageLayout.vue'
import ReaderSelection from '../components/ReaderSelection.vue'
import { ready, session } from '../lib/auth.js'
import {
  activity,
  clearReaderQuestion,
  draft,
  draftQuote,
  open as chatOpen,
  responding,
  send,
  settled,
} from '../lib/chat.js'
import { chatSize } from '../lib/chatPanel.js'
import { inkOn, setInkOn } from '../lib/ink.js'
import { streamReader } from '../lib/reader.js'

const { t } = useI18n()
const route = useRoute()
const fake = route.query.fake !== undefined

const pageSource = `Un bean con scope **singleton** se crea una sola vez por contenedor de Spring: cualquier servicio que lo pida por inyección de dependencias recibe exactamente la misma referencia en memoria.

Cuando necesitas estado propio por cada uso, el scope **prototype** construye una instancia nueva cada vez que el contenedor resuelve el bean.

\`\`\`kolmi-ai
root = Answer([t])
t = Table(["Scope", "Instancias", "Cuándo usarlo"], [["singleton", "Una por contenedor", "Servicios sin estado mutable"], ["prototype", "Una por solicitud al contenedor", "Objetos con estado propio"]])
\`\`\`

En aplicaciones web existe además **request**, que ata la vida del objeto a una única petición HTTP entrante.`

function fakeReply(selection, detail) {
  const term = selection.toLowerCase()
  if (!detail) {
    if (term.includes('prototype')) {
      return 'Aquí indica que el contenedor **crea un objeto distinto** en cada inyección o consulta, de modo que dos consumidores nunca comparten estado interno.'
    }
    if (term.includes('contenedor') || term.includes('referencia')) {
      return 'Es el registro central de Spring (`ApplicationContext`) que instancia los objetos una vez y reparte su **misma dirección de memoria** a quien los declara.'
    }
    return 'En este pasaje significa que todos los servicios reciben **la misma instancia** creada al arrancar el contenedor, sin duplicar el objeto en cada petición.'
  }
  if (term.includes('prototype')) {
    return `## Prototype frente a Singleton

Con \`prototype\`, Spring ejecuta \`new\` en cada resolución y entrega referencias independientes.

\`\`\`kolmi-ai
root = Answer([f])
f = Figure("Cada servicio recibe su propia instancia", [s, a, p], "row")
s = Group([s1, s2], "column")
s1 = Chip("OrderService", "blue")
s2 = Chip("CartService", "blue")
a = Arrow("nueva instancia")
p = Group([p1, p2], "column")
p1 = Chip("Bean #01", "violet", "box", "estado propio")
p2 = Chip("Bean #02", "violet", "box", "estado propio")
\`\`\`

Si guardas datos del usuario dentro de un **contenedor** compartido, \`prototype\` evita mezclar sesiones.`
  }
  return `## Una sola instancia compartida

El **contenedor** crea el objeto una vez y entrega la misma **referencia** a cada clase dependiente.

\`\`\`kolmi-ai
root = Answer([f])
f = Figure("Varios servicios apuntan a la misma instancia", [g, a, one], "row")
g = Group([c1, c2, c3], "column")
c1 = Chip("OrderService", "blue")
c2 = Chip("MailService", "blue")
c3 = Chip("ReportService", "blue")
a = Arrow("misma referencia")
one = Chip("Repository #01", "green", "database", "singleton")
\`\`\`

Como todos leen y escriben sobre el mismo objeto, un servicio \`singleton\` no debe guardar campos mutables por petición.`
}

async function fakeStream(selection, _context, { detail = false, signal, onText, onTextDone }) {
  await new Promise((r) => setTimeout(r, 220))
  const answer = fakeReply(selection, detail)
  let acc = ''
  for (const chunk of answer.match(/.{1,14}/gs) ?? []) {
    if (signal?.aborted) return ''
    await new Promise((r) => setTimeout(r, 45))
    acc += chunk
    onText(acc)
  }
  onTextDone?.()
  return acc
}

const runner = fake ? fakeStream : streamReader
</script>

<template>
  <main class="py-12">
    <div class="article mb-8 flex items-center gap-2 text-meta text-fg-muted">
      <span>Vista de lectura con Curio ({{ fake ? 'respuesta simulada' : 'modelo real' }}).</span>
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

    <div v-if="!fake && ready && !session" class="article mb-6 rounded-lg bg-bg-muted p-3 text-copy">
      Para probar contra el modelo real inicia sesión en <RouterLink to="/login" class="underline">/login</RouterLink>, o usa
      <RouterLink to="/dev/curio?fake" class="underline">/dev/curio?fake</RouterLink>.
    </div>

    <PageLayout title="Scopes de beans en Spring" lead="DWCS · Inyección de dependencias">
      <ReaderSelection
        title="Scopes de beans en Spring"
        :node-id="1"
        :enabled="true"
        :stream="runner"
      >
        <Markdown :source="pageSource" :components="{ 'kolmi-ai': NoteAiFence }" />
      </ReaderSelection>
    </PageLayout>

    <ChatMorph
      v-model:open="chatOpen"
      v-model:size="chatSize"
      resizable
      class="chat-panel"
      :label="t('chat.label')"
      :title="t('chat.title')"
      :settled="settled"
      :activity="activity"
    >
      <ChatConversation />
      <div v-if="draftQuote" class="mx-auto flex w-full max-w-2xl px-4 pt-2">
        <div class="flex min-w-0 flex-1 items-center gap-2 rounded-2xl bg-bg-muted px-3.5 py-2 text-meta text-fg-secondary">
          <span class="min-w-0 flex-1 truncate">
            <span v-if="draftQuote.title" class="text-fg-muted">{{ draftQuote.title }} · </span>“{{ draftQuote.text }}”
          </span>
          <Button
            variant="ghost"
            size="icon"
            class="size-6 shrink-0"
            :icon="X"
            :aria-label="t('reader.close')"
            :title="t('reader.close')"
            @click="clearReaderQuestion"
          />
        </div>
      </div>
      <ChatComposer v-model="draft" :placeholder="t('chat.placeholder')" :responding="responding" @send="send" />
    </ChatMorph>
  </main>
</template>
