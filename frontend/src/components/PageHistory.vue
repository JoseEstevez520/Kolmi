<script setup>
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { ConfirmButton, PopoverMorph, StatusText, Timeline, TimelineItem } from 'elastic-ui'
import { History, RotateCcw } from '@lucide/vue'
import { api } from '../lib/api.js'
import { forgetNode, loadNode } from '../lib/content.js'
import { formatShortDate } from '../lib/format.js'

// A page's earlier versions, for an admin, in the page's top bar: each with when it was kept and
// how it began, and a restore that asks first. The server keeps them (every rewrite saves the one
// before, a restore too), so the list is read each time it opens and nothing is worked out here.
const props = defineProps({
  nodeId: { type: Number, required: true },
})
const { t } = useI18n()

const open = ref(false)
const versions = ref([])
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    versions.value = await api.pageVersions(props.nodeId)
  } catch (e) {
    error.value = e.message || t('history.error')
  } finally {
    loading.value = false
  }
}

watch(open, (isOpen) => isOpen && load())

// How a version began: its first line of text, without the Markdown marks in front.
function firstLine(preview) {
  const line = (preview ?? '').split('\n').find((text) => text.trim()) ?? ''
  return line.replace(/^\s*(#+|[-*>]|\d+\.)\s*/, '').trim() || t('history.untitled')
}

// The page shows the version put back at once: it is read again from the server.
async function restore(versionId) {
  await api.restoreVersion(versionId)
  forgetNode(props.nodeId)
  await loadNode(props.nodeId)
  await load()
}
</script>

<template>
  <PopoverMorph
    v-model:open="open"
    variant="ghost"
    size="sm"
    align="end"
    fluid
    :label="t('history.label')"
  >
    <template #trigger>
      <History aria-hidden="true" />
      <span class="max-sm:sr-only">{{ t('history.button') }}</span>
    </template>

    <StatusText v-if="loading && !versions.length" :delay="300" :text="t('history.loading')" working />
    <StatusText v-else-if="error" class="text-meta" :text="error" error />
    <p v-else-if="!versions.length" class="text-meta text-fg-muted">{{ t('history.none') }}</p>
    <Timeline
      v-else
      :label="t('history.label')"
      class="[--timeline-bg:var(--popover-bg,var(--color-surface-raised))]"
    >
      <TimelineItem
        v-for="version in versions"
        :key="version.id"
        :date="formatShortDate(version.created_at)"
        :title="firstLine(version.preview)"
      >
        <ConfirmButton
          variant="ghost"
          tone="warning"
          :icon="RotateCcw"
          :label="t('history.restore', { date: formatShortDate(version.created_at) })"
          :confirm-label="t('history.confirm')"
          :cancel-label="t('common.cancel')"
          :action="() => restore(version.id)"
        />
      </TimelineItem>
    </Timeline>
  </PopoverMorph>
</template>
