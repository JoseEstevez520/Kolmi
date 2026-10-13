<script setup>
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, DescriptionItem, DescriptionList, StatusText } from 'elastic-ui'
import { usePreviewData } from '../../lib/previewData.js'

// run_pass: how many notes wait for the pass and whether one is already running. Left blank when
// the notes cannot be read.
const { t } = useI18n()
const data = usePreviewData()

const pending = ref(null) // null while loading, false when unreadable
const state = ref(null) // { running, enabled }
onMounted(async () => {
  try {
    pending.value = (await data.loadNotes()).filter((n) => n.status === 'pending').length
  } catch {
    pending.value = false
    return
  }
  try {
    state.value = await data.loadPassState()
  } catch {
    state.value = null
  }
})
</script>

<template>
  <StatusText v-if="pending === null" class="text-meta" :delay="300" :text="t('chat.preview.countingPending')" working />
  <div v-else-if="pending !== false" class="flex flex-col gap-2">
    <DescriptionList>
      <DescriptionItem :term="t('chat.preview.pendingNotes', { n: pending }, pending)" class="py-1.5">
        {{ pending ? t('chat.preview.passReads') : t('chat.preview.passNothing') }}
      </DescriptionItem>
    </DescriptionList>
    <Callout v-if="state?.running" type="caution">{{ t('chat.preview.passRunning') }}</Callout>
    <p v-else-if="state && !state.enabled" class="m-0 text-meta text-fg-muted">{{ t('chat.preview.passOff') }}</p>
  </div>
</template>
