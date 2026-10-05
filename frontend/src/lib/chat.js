import { computed, ref, watch } from 'vue'
import { api } from './api.js'
import { flatten } from './content.js'
import { t } from './i18n.js'

// The titles of the pages an answer cites, for its "From: ..." line; the tree is already kept
// in the browser (content.js), so this needs no request of its own.
export function sourceTitles(ids) {
  if (!ids?.length) return ''
  const byId = new Map(flatten().map((node) => [node.id, node.title]))
  return ids.map((id) => byId.get(id)).filter(Boolean).join(', ')
}

// Whether the admin turned the chat on for this class, read once when the app shell mounts
// (App.vue): the bubble shows only then. `null` while unknown, so it shows only once we're sure.
export const chatEnabled = ref(null)

export async function loadChatEnabled() {
  try {
    chatEnabled.value = Boolean((await api.settings()).chat_enabled)
  } catch {
    chatEnabled.value = false
  }
}

// The chat's state, held once for the whole app (ChatMorph is mounted once, in App.vue): whether
// it is open, the conversation so far, and whether an answer is on its way. Nothing is kept
// between visits; a reload starts a new conversation, as nothing here is saved to the browser.
export const open = ref(false)
export const messages = ref([])
export const responding = ref(false)

// A greeting the first time it opens, not from the model: it just says who it is.
watch(open, (isOpen) => {
  if (isOpen && messages.value.length === 0) {
    messages.value.push({ id: nextId++, role: 'assistant', text: t('chat.greeting') })
  }
})

// The aurora follows what is going on: resting until the first message, thinking while the
// answer is on its way, settling to a quiet tint once the conversation has started.
export const settled = computed(() => messages.value.length > 0)
export const activity = computed(() => (responding.value ? 'thinking' : 'rest'))

let nextId = 1

export async function send(text) {
  const question = text.trim()
  if (!question || responding.value) return

  messages.value.push({ id: nextId++, role: 'user', text: question })
  // `text: ''` from the start, not left out: ChatMessage only shows its "thinking" line once it
  // has a (possibly empty) text to show instead of.
  const replyId = nextId++
  messages.value.push({ id: replyId, role: 'assistant', text: '', status: t('chat.thinking'), sources: [] })
  responding.value = true

  // Found again through `messages.value`, not kept from the object just pushed: Vue only sees a
  // mutation as reactive when it goes through the array's own reactive reference, not a plain
  // object held across the await.
  try {
    const result = await api.askChat(question)
    const reply = messages.value.find((m) => m.id === replyId)
    if (reply) {
      reply.text = result.answer
      reply.sources = result.sources ?? []
      reply.status = ''
    }
  } catch (e) {
    const reply = messages.value.find((m) => m.id === replyId)
    if (reply) {
      reply.status = ''
      reply.error = e.message || t('chat.error')
    }
  } finally {
    responding.value = false
  }
}
