<script setup>
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import {
  ActionButton,
  Button,
  Callout,
  Field,
  Input,
  Markdown,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  StatusText,
} from 'elastic-ui'
import { ArrowLeft, Maximize2, Minimize2 } from '@lucide/vue'
import { api } from '../lib/api.js'
import { loadNodes, nodes } from '../lib/content.js'
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
const error = ref('')
// A note the pass already took: shown, no longer editable.
const closed = ref(null)
const draftSaved = ref(false)
const editor = ref(null)

// Where the student thinks the note goes, as a hint for the daily pass; "Not sure" leaves it
// empty. A Select item needs a non-empty value, so that one travels under a sentinel.
const NOT_SURE = '__none__'
const hint = ref(NOT_SURE)
const hintId = computed(() => (hint.value === NOT_SURE ? null : Number(hint.value)))

// Every section and page, parents first, each with its depth to indent it.
const places = computed(() => {
  const out = []
  const walk = (items, depth) => {
    for (const item of items) {
      out.push({ id: item.id, title: item.title, depth })
      if (item.children?.length) walk(item.children, depth + 1)
    }
  }
  walk(nodes.value, 0)
  return out
})

const content = computed(() => joinNote(title.value, body.value))
const empty = computed(() => !content.value)

// What was there when the screen opened: only a change from it is a draft worth keeping.
let baseline = ''
let baselineHint = NOT_SURE

function fill(text, nodeId = null) {
  const parts = splitNote(text)
  title.value = parts.title
  body.value = parts.body
  hint.value = nodeId == null ? NOT_SURE : String(nodeId)
  baseline = joinNote(parts.title, parts.body)
  baselineHint = hint.value
}

async function load() {
  error.value = ''
  closed.value = null
  draftSaved.value = false
  const draft = loadDraft(id.value)

  if (isNew.value) {
    fill(draft ? joinNote(draft.title, draft.body) : '', draft?.nodeId ?? null)
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
      fill(
        draft ? joinNote(draft.title, draft.body) : note.content,
        draft && 'nodeId' in draft ? draft.nodeId : note.node_id,
      )
    }
  } catch (e) {
    error.value = e.message || t('notes.errorLong')
  } finally {
    loading.value = false
  }
}

// Kept a moment after the last key, not on every one.
let timer = null
watch([title, body, hint], () => {
  if (loading.value || closed.value) return
  if (content.value === baseline && hint.value === baselineHint) return
  draftSaved.value = false
  clearTimeout(timer)
  timer = setTimeout(() => {
    draftSaved.value = saveDraft(id.value, {
      title: title.value,
      body: body.value,
      nodeId: hintId.value,
    })
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
    await api.createNote({ content: content.value, format: 'markdown', nodeId: hintId.value })
  } else {
    await api.updateNote({ noteId: id.value, content: content.value, nodeId: hintId.value })
  }
  clearDraft(id.value)
  router.push('/notes')
}

// Enter in the title goes on to the text, as in a document.
function toText() {
  editor.value?.focus()
}

onMounted(load)
// The tree is usually loaded already, for the sidebar; if it fails, the hint just has no options.
onMounted(() => loadNodes().catch(() => {}))
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

    <StatusText v-if="loading" :delay="300" :text="t('common.loading')" working />

    <Callout v-else-if="error" type="caution" :title="t('notes.error')">{{ error }}</Callout>

    <template v-else-if="closed">
      <Callout type="note" :title="t('notes.write.closedTitle')">{{ t('notes.write.closed') }}</Callout>
      <Markdown v-if="closed.format === 'markdown'" :source="closed.content" class="mt-8" />
      <p v-else class="mt-8 whitespace-pre-line text-fg-secondary">{{ closed.content }}</p>
    </template>

    <template v-else>
      <Input
        v-model="title"
        bare
        class="mb-6 text-display"
        :placeholder="t('notes.write.titlePlaceholder')"
        :aria-label="t('notes.write.titleLabel')"
        autofocus
        @keydown.enter.prevent="toText"
      />
      <Field :label="t('notes.write.hintLabel')" :description="t('notes.write.hintHelp')" class="mb-6">
        <Select v-model="hint">
          <SelectTrigger>
            <SelectValue :placeholder="t('notes.write.hintNotSure')" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem :value="NOT_SURE">{{ t('notes.write.hintNotSure') }}</SelectItem>
            <SelectItem v-for="place in places" :key="place.id" :value="String(place.id)">
              <span :style="{ paddingInlineStart: `${place.depth}rem` }">{{ place.title }}</span>
            </SelectItem>
          </SelectContent>
        </Select>
      </Field>
      <NoteEditor
        ref="editor"
        v-model="body"
        :label="t('notes.field')"
        :placeholder="t('notes.write.bodyPlaceholder')"
      />
    </template>
  </div>
</template>
