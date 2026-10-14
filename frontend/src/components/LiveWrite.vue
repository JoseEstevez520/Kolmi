<script setup>
import { defineAsyncComponent, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { onBeforeRouteLeave } from 'vue-router'
import { Button, Input, StatusText } from 'elastic-ui'
import { Eye, EyeOff, Square } from '@lucide/vue'
import { api } from '../lib/api.js'
import { invalidate } from '../lib/cached.js'

// The writer's side of a live note: a title, the editor, a "Share live" switch (off until the
// author turns it on) and "End session". What is written is saved a moment after the last key.
// While it is shared, the text is sent again now and then even if it did not change, so a long
// pause (the teacher talking) does not drop the note out of "Now".
const props = defineProps({
  note: { type: Object, required: true },
})
const emit = defineEmits(['ended'])

const { t } = useI18n()
const NoteEditor = defineAsyncComponent(() => import('./NoteEditor.vue'))

const title = ref(props.note.title)
const body = ref(props.note.content ?? '')
const shared = ref(props.note.shared)
const ending = ref(false)

// '', 'saving', 'saved' or 'error', like the notes screen.
const status = ref('')
let saved = { title: title.value, body: body.value }
let timer = null
let inFlight = null
let again = false

async function save(keepalive = false) {
  clearTimeout(timer)
  if (inFlight) {
    again = true
    return inFlight
  }
  const sent = { title: title.value.trim() || saved.title, body: body.value }
  if (sent.title === saved.title && sent.body === saved.body) return
  status.value = 'saving'
  inFlight = (async () => {
    try {
      await api.saveLiveNote({
        id: props.note.id,
        content: sent.body !== saved.body ? sent.body : undefined,
        title: sent.title !== saved.title ? sent.title : undefined,
        keepalive,
      })
      saved = sent
      status.value = 'saved'
    } catch (e) {
      // The session hit its time limit: it is over, the screen goes to the ended note.
      if (e.status === 409) {
        emit('ended')
        return
      }
      // The text stays on screen; the next change tries again.
      status.value = 'error'
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

watch([title, body], () => {
  clearTimeout(timer)
  timer = setTimeout(save, 1000)
})

// The switch takes effect at once, not after the debounce.
async function setShared(value) {
  const before = shared.value
  shared.value = value
  try {
    await api.saveLiveNote({ id: props.note.id, shared: value })
  } catch {
    shared.value = before
    status.value = 'error'
  }
}

// Heartbeat: resend the text while shared, so the note stays "live" through a quiet stretch.
const HEARTBEAT = 2 * 60 * 1000
let heartbeat = null
onMounted(() => {
  heartbeat = setInterval(() => {
    if (!shared.value || ending.value) return
    api.saveLiveNote({ id: props.note.id, content: body.value }).catch(() => {})
  }, HEARTBEAT)
  document.addEventListener('visibilitychange', onHide)
  window.addEventListener('pagehide', onHide)
})
onBeforeUnmount(() => {
  clearTimeout(timer)
  clearInterval(heartbeat)
  document.removeEventListener('visibilitychange', onHide)
  window.removeEventListener('pagehide', onHide)
})

function onHide() {
  if (document.visibilityState === 'hidden') save(true)
}
onBeforeRouteLeave(async () => {
  await save()
  invalidate('live')
})

async function end() {
  ending.value = true
  try {
    await save()
    await api.endLiveNote({ id: props.note.id })
    emit('ended')
  } catch {
    status.value = 'error'
    ending.value = false
  }
}

const statusText = () =>
  ({ saving: t('notes.write.saving'), saved: t('notes.write.saved'), error: t('notes.write.saveError') })[status.value] ?? ''
</script>

<template>
  <div>
    <div class="mb-8 flex flex-wrap items-center justify-between gap-3">
      <Button
        variant="ghost"
        size="icon"
        :icon="shared ? Eye : EyeOff"
        :disabled="ending"
        :aria-pressed="shared"
        :aria-label="t('live.share')"
        :title="t('live.share')"
        @click="setShared(!shared)"
      />
      <div class="flex items-center gap-2">
        <StatusText
          v-if="status"
          :class="['text-meta', status !== 'error' && 'text-fg-muted']"
          :text="statusText()"
          :working="status === 'saving'"
          :error="status === 'error'"
        />
        <Button variant="ghost" size="icon" :icon="Square" :disabled="ending" :aria-label="t('live.end')" :title="t('live.end')" @click="end" />
      </div>
    </div>
    <Input v-model="title" bare class="mb-6 text-display" :aria-label="t('live.titleLabel')" />
    <NoteEditor v-model="body" :label="t('live.titleLabel')" placeholder="" />
  </div>
</template>
