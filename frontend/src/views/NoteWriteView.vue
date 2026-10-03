<script setup>
import { computed, defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'
import {
  Button,
  Callout,
  Input,
  Markdown,
  NavTree,
  NavTreeItem,
  PopoverMorph,
  StatusText,
  TruncatedText,
} from 'elastic-ui'
import { ArrowLeft, Folder, Maximize2, Minimize2 } from '@lucide/vue'
import PlaceTree from '../components/PlaceTree.vue'
import { api } from '../lib/api.js'
import { loadNodes, nodes } from '../lib/content.js'
import { joinNote, splitNote } from '../lib/notes.js'
import { exitZen, toggleZen, zen } from '../lib/zen.js'

// Writing a note, as a page of its own: a title and the text under it, nothing else in the
// way. At /notes/new it starts one; at /notes/:id it reopens one of yours, until the daily
// pass takes it. What is written is saved to the server as it goes: there is no send.
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

// The editor brings Tiptap with it, so it loads with this screen, not with the app.
const NoteEditor = defineAsyncComponent(() => import('../components/NoteEditor.vue'))

// The note being written: none until a new one is first saved.
const noteId = ref(route.params.id === 'new' ? null : Number(route.params.id))

const title = ref('')
const body = ref('')
const loading = ref(false)
const error = ref('')
// A note the pass already took: shown, no longer editable.
const closed = ref(null)
const editor = ref(null)

// Where the student thinks the note goes, as a hint for the daily pass; "Not sure" leaves it
// empty. The tree's items need a non-empty value, so that one travels under a sentinel.
const NOT_SURE = '__none__'
const hint = ref(NOT_SURE)
const hintId = computed(() => (hint.value === NOT_SURE ? null : Number(hint.value)))

// The hint lives in the top bar as a quiet piece of metadata: a ghost button with the picked
// place's short path, opening the tree. Picking a place closes it.

// Each node's path from the top, to name the picked one by its last two steps.
const paths = computed(() => {
  const out = new Map()
  const walk = (items, trail) => {
    for (const item of items) {
      const path = [...trail, item.title]
      out.set(String(item.id), path)
      if (item.children?.length) walk(item.children, path)
    }
  }
  walk(nodes.value, [])
  return out
})
const hintPath = computed(() => paths.value.get(hint.value)?.slice(-2).join(' / ') ?? '')

const content = computed(() => joinNote(title.value, body.value))

// What the server has, to save only a change from it.
let saved = { content: '', hint: NOT_SURE }

async function load() {
  if (noteId.value == null) return
  loading.value = true
  try {
    const note = (await api.myNotes()).find((n) => n.id === noteId.value)
    if (!note) {
      error.value = t('notes.write.notFound')
    } else if (note.status !== 'pending') {
      closed.value = note
    } else {
      const parts = splitNote(note.content)
      title.value = parts.title
      body.value = parts.body
      hint.value = note.node_id == null ? NOT_SURE : String(note.node_id)
      saved = { content: content.value, hint: hint.value }
    }
  } catch (e) {
    error.value = e.message || t('notes.errorLong')
  } finally {
    loading.value = false
  }
}

// '' (nothing to say yet), 'saving', 'saved' or 'error'. Saves come every few seconds while
// writing, so "Saving…" only shows when one takes long enough to notice; a quick one leaves
// "Saved" still, instead of flickering through "Saving…" each time.
const status = ref('')
const SHOW_SAVING_AFTER = 600
let savingTimer = null
function startSaving() {
  clearTimeout(savingTimer)
  if (status.value === 'error') status.value = 'saving'
  else savingTimer = setTimeout(() => (status.value = 'saving'), SHOW_SAVING_AFTER)
}
function endSaving(result) {
  clearTimeout(savingTimer)
  status.value = result
}
const statusText = computed(
  () =>
    ({
      saving: t('notes.write.saving'),
      saved: t('notes.write.saved'),
      error: t('notes.write.saveError'),
    })[status.value] ?? '',
)

// One save at a time. A change made while one is in flight is saved right after it, so the
// latest text wins and a new note is created only once. An empty note is never sent: a new one
// isn't created, and a cleared one keeps its last text.
let timer = null
let inFlight = null
let again = false
let leaving = false

function save(keepalive = false) {
  clearTimeout(timer)
  if (inFlight) {
    again = true
    return inFlight
  }
  if (loading.value || closed.value || error.value || !content.value) return
  if (content.value === saved.content && hint.value === saved.hint) return

  const sent = { content: content.value, hint: hint.value }
  startSaving()
  inFlight = (async () => {
    try {
      const fields = { content: sent.content, nodeId: hintId.value, keepalive }
      if (noteId.value == null) {
        const note = await api.createNote({ ...fields, format: 'markdown' })
        noteId.value = note.id
        // The URL becomes the note's own, so going back and reopening finds it.
        if (!leaving) router.replace({ name: 'note', params: { id: note.id } })
      } else {
        await api.updateNote({ ...fields, noteId: noteId.value })
      }
      saved = sent
      endSaving('saved')
    } catch {
      // The text stays on screen; the next change tries again.
      endSaving('error')
    } finally {
      inFlight = null
    }
    if (again) {
      again = false
      if (status.value !== 'error') await save(keepalive)
    }
  })()
  return inFlight
}

// Saved a moment after the last key, not on every one.
watch([title, body, hint], () => {
  if (loading.value || closed.value) return
  clearTimeout(timer)
  timer = setTimeout(save, 1200)
})

// Leaving the screen, or the tab, saves what is pending. A closing tab can't wait, so that save
// is sent with keepalive to outlive the page.
onBeforeRouteLeave(() => {
  leaving = true
  return save()
})
function onHide() {
  if (document.visibilityState === 'hidden') save(true)
}
onMounted(() => {
  document.addEventListener('visibilitychange', onHide)
  window.addEventListener('pagehide', onHide)
})
onBeforeUnmount(() => clearTimeout(savingTimer))

onBeforeUnmount(() => {
  clearTimeout(timer)
  document.removeEventListener('visibilitychange', onHide)
  window.removeEventListener('pagehide', onHide)
})

// Escape leaves zen mode, unless it was closing the "/" menu. Leaving the screen leaves it too.
function onKey(event) {
  if (zen.value && event.key === 'Escape' && !event.defaultPrevented) exitZen()
}

onMounted(() => window.addEventListener('keydown', onKey))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKey)
  exitZen()
})

// Enter in the title goes on to the text, as in a document.
function toText() {
  editor.value?.focus()
}

onMounted(load)
// The tree is usually loaded already, for the sidebar; if it fails, the hint just has no options.
onMounted(() => loadNodes().catch(() => {}))
</script>

<template>
  <div class="article">
    <div class="mb-10 flex items-center justify-between gap-3">
      <Button variant="ghost" size="sm" :icon="ArrowLeft" to="/notes">{{ t('notes.write.back') }}</Button>
      <div v-if="!closed && !error" class="flex min-w-0 items-center gap-2">
        <PopoverMorph
          v-if="!loading"
          variant="ghost"
          size="sm"
          align="end"
          fluid
          class="min-w-0 text-fg-muted"
          :label="hintPath ? `${t('notes.write.hintLabel')} ${hintPath}` : t('notes.write.hintLabel')"
        >
          <template #trigger>
            <Folder class="size-4 shrink-0" aria-hidden="true" />
            <TruncatedText class="min-w-0">{{ hintPath || t('notes.write.hintEmpty') }}</TruncatedText>
          </template>
          <template #default="{ close }">
            <NavTree v-model="hint" selectable :label="t('notes.write.hintLabel')" @select="close">
              <NavTreeItem :value="NOT_SURE">{{ t('notes.write.hintNotSure') }}</NavTreeItem>
              <PlaceTree :items="nodes" />
            </NavTree>
          </template>
        </PopoverMorph>
        <StatusText
          v-if="status"
          :class="['text-meta', status !== 'error' && 'text-fg-muted']"
          :text="statusText"
          :working="status === 'saving'"
          :error="status === 'error'"
        />
        <Button
          variant="ghost"
          size="icon"
          :icon="zen ? Minimize2 : Maximize2"
          :aria-label="zen ? t('notes.write.zenExit') : t('notes.write.zen')"
          :aria-pressed="zen"
          @click="toggleZen"
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
      <NoteEditor
        ref="editor"
        v-model="body"
        :label="t('notes.field')"
        :placeholder="t('notes.write.bodyPlaceholder')"
      />
    </template>
  </div>
</template>
