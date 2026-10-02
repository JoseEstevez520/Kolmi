<script setup>
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { ActionButton, Button, Callout, Markdown, StatusText } from 'elastic-ui'
import { ArrowLeft, Maximize2, Minimize2 } from '@lucide/vue'
import { api } from '../lib/api.js'
import { useDelayed } from '../lib/delayed.js'
import { clearDraft, joinNote, loadDraft, saveDraft, splitNote } from '../lib/notes.js'
import { exitZen, toggleZen, zen } from '../lib/zen.js'

// Writing a note, as a page of its own: a title and the text under it, nothing else in the
// way. At /notes/new it starts one; at /notes/:id it reopens one of yours, until the daily
// pass takes it. What is written is kept in this browser as a draft until it is sent.
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// The editor brings Tiptap with it, so it loads with this screen, not with the app.
const NoteEditor = defineAsyncComponent(() => import('../components/NoteEditor.vue'))

const id = computed(() => (route.params.id ? Number(route.params.id) : null))
const isNew = computed(() => id.value == null)

const title = ref('')
const body = ref('')
const loading = ref(false)
// Shown only when the wait is long enough to notice.
const slow = useDelayed(loading)
const error = ref('')
// A note the pass already took: shown, no longer editable.
const closed = ref(null)
const draftSaved = ref(false)
const editor = ref(null)

const content = computed(() => joinNote(title.value, body.value))
const empty = computed(() => !content.value)

// What was there when the screen opened: only a change from it is a draft worth keeping.
let baseline = ''

function fill(text) {
  const parts = splitNote(text)
  title.value = parts.title
  body.value = parts.body
  baseline = joinNote(parts.title, parts.body)
}

async function load() {
  error.value = ''
  closed.value = null
  draftSaved.value = false
  const draft = loadDraft(id.value)

  if (isNew.value) {
    fill(draft ? joinNote(draft.title, draft.body) : '')
    return
  }

  loading.value = true
  try {
    const note = (await api.myNotes()).find((n) => n.id === id.value)
    if (!note) {
      error.value = t('notes.write.notFound')
    } else if (note.status !== 'pending') {
      closed.value = note
    } else {
      fill(draft ? joinNote(draft.title, draft.body) : note.content)
    }
  } catch (e) {
    error.value = e.message || t('notes.errorLong')
  } finally {
    loading.value = false
  }
}

// Kept a moment after the last key, not on every one.
let timer = null
watch([title, body], () => {
  if (loading.value || closed.value || content.value === baseline) return
  draftSaved.value = false
  clearTimeout(timer)
  timer = setTimeout(() => {
    draftSaved.value = saveDraft(id.value, { title: title.value, body: body.value })
  }, 600)
})
onBeforeUnmount(() => clearTimeout(timer))

// Escape leaves zen mode, unless it was closing the "/" menu. Leaving the screen leaves it too.
function onKey(event) {
  if (zen.value && event.key === 'Escape' && !event.defaultPrevented) exitZen()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  exitZen()
})

async function send() {
  clearTimeout(timer)
  if (isNew.value) {
    await api.createNote({ content: content.value, format: 'markdown' })
  } else {
    await api.updateNote({ noteId: id.value, content: content.value })
  }
  clearDraft(id.value)
  router.push('/notes')
}

// Enter in the title goes on to the text, as in a document.
function toText() {
  editor.value?.focus()
}

onMounted(load)
watch(id, load)
</script>

<template>
  <div class="article">
    <div class="mb-10 flex items-center justify-between gap-3">
      <Button variant="ghost" size="sm" :icon="ArrowLeft" to="/notes">{{ t('notes.write.back') }}</Button>
      <div v-if="!closed && !error" class="flex items-center gap-2">
        <span class="text-meta text-fg-muted" aria-live="polite">
          {{ draftSaved ? t('notes.write.draftSaved') : '' }}
        </span>
        <Button
          variant="ghost"
          size="icon"
          :icon="zen ? Minimize2 : Maximize2"
          :aria-label="zen ? t('notes.write.zenExit') : t('notes.write.zen')"
          :aria-pressed="zen"
          @click="toggleZen"
        />
        <ActionButton
          :action="send"
          :disabled="empty || loading"
          :label="isNew ? t('notes.send') : t('notes.write.save')"
          :done-label="isNew ? t('notes.sent') : t('notes.write.saved')"
          :error-label="t('notes.sendError')"
          :icon="isNew ? 'arrowUp' : 'check'"
        />
      </div>
    </div>

    <template v-if="loading">
      <StatusText v-if="slow" :text="t('common.loading')" working />
    </template>

    <Callout v-else-if="error" type="caution" :title="t('notes.error')">{{ error }}</Callout>

    <template v-else-if="closed">
      <Callout type="note" :title="t('notes.write.closedTitle')">{{ t('notes.write.closed') }}</Callout>
      <Markdown v-if="closed.format === 'markdown'" :source="closed.content" class="mt-8" />
      <p v-else class="mt-8 whitespace-pre-line text-fg-secondary">{{ closed.content }}</p>
    </template>

    <template v-else>
      <input
        v-model="title"
        type="text"
        class="mb-6 w-full bg-transparent text-[2rem] leading-tight font-semibold text-fg outline-none placeholder:text-fg-faint"
        :placeholder="t('notes.write.titlePlaceholder')"
        :aria-label="t('notes.write.titleLabel')"
        autofocus
        @keydown.enter.prevent="toText"
      />
      <NoteEditor
        ref="editor"
        v-model="body"
        :label="t('notes.field')"
        :placeholder="t('notes.write.bodyPlaceholder')"
      />
    </template>
  </div>
</template>
