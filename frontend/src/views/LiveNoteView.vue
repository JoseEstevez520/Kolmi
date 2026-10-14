<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'
import { Button, Callout, ConfirmButton, Status } from 'elastic-ui'
import { ArrowLeft } from '@lucide/vue'
import LiveWatch from '../components/LiveWatch.vue'
import TextSkeleton from '../components/TextSkeleton.vue'
import { api } from '../lib/api.js'
import { profile } from '../lib/auth.js'
import { invalidate } from '../lib/cached.js'
import { refreshLiveCount } from '../lib/liveCount.js'
import { usePolling } from '../lib/polling.js'

// One live note, watched: a read-only view that follows it (LiveWatch). It asks every few
// seconds with the `updated_at` it already has, so a note that has not changed costs a tiny
// answer. Its author writes it from the note itself (NoteWriteView's header), so they are sent
// there instead.
const route = useRoute()
const router = useRouter()
const { t } = useI18n()

const id = Number(route.params.id)
const POLL = 4000

const note = ref(null)
const loading = ref(true)
const error = ref('')

const canDelete = computed(() => note.value && profile.value?.role === 'admin')

async function load() {
  try {
    const answer = await api.liveNote({ id, since: note.value?.updated_at })
    if (answer.mine) {
      router.replace(answer.note_id ? { name: 'note', params: { id: answer.note_id } } : { name: 'notes' })
      return
    }
    if (answer.unchanged) {
      // The text is the same; whether it is still live or ended may not be.
      note.value = { ...note.value, live: answer.live, ended: answer.ended }
    } else {
      note.value = answer
    }
    error.value = ''
  } catch (e) {
    // Once loaded, a failed beat is skipped; the next one tries again.
    if (!note.value) error.value = e.status === 404 ? t('live.notFound') : e.message
  } finally {
    loading.value = false
  }
}
usePolling(load, POLL)

// [state, label] for the header: live while it is written, ended once the author ends it.
const state = computed(() => {
  if (note.value?.live) return ['working', t('live.state.live')]
  if (note.value?.ended) return ['done', t('live.state.ended')]
  return ['idle', note.value?.shared ? t('live.state.stopped') : t('live.state.private')]
})

async function remove() {
  await api.deleteLiveNote({ id })
  invalidate('live')
  refreshLiveCount()
  router.push({ name: 'notes' })
}
</script>

<template>
  <main class="py-16">
    <div class="article">
      <div class="mb-8 flex items-center justify-between gap-3">
        <Button variant="ghost" size="icon" :icon="ArrowLeft" to="/notes" :aria-label="t('notes.write.back')" :title="t('notes.write.back')" />
        <ConfirmButton
          v-if="canDelete"
          variant="ghost"
          :label="t('live.deleteLabel')"
          :confirm-label="t('live.deleteConfirm')"
          :cancel-label="t('live.deleteCancel')"
          :action="remove"
        />
      </div>

      <TextSkeleton v-if="loading" heading />
      <Callout v-else-if="error" type="caution" :title="t('live.error')">{{ error }}</Callout>

      <template v-else-if="note">
        <div class="prose">
          <div class="flex items-start justify-between gap-4">
            <h1>{{ note.title }}</h1>
            <Status compact class="mt-2 shrink-0" :state="state[0]" :label="state[1]" />
          </div>
          <p class="text-fg-muted" :title="t('live.notChecked')">{{ note.author ?? '?' }}</p>
        </div>

        <LiveWatch v-if="!note.ended || note.content" :content="note.content ?? ''" :live="note.live" />
      </template>
    </div>
  </main>
</template>
