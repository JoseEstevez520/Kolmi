<script setup>
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, CodeDiff, DescriptionItem, DescriptionList, StatusText } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { formatDate } from '../../lib/format.js'
import { usePreviewData } from '../../lib/previewData.js'

// restore_version: the page, the version coming back and its Markdown against the page's now.
// The versions list only carries the first 300 characters of each, so a longer version is
// compared on its opening; the card says so. Nothing is drawn if the version is not found.
const props = defineProps({ args: { type: Object, default: () => ({}) } })
const { t } = useI18n()
const data = usePreviewData()
data.ensure.nodes()

const PREVIEW_LENGTH = 300
const version = ref(undefined) // undefined while loading, null when not found
onMounted(async () => {
  try {
    version.value = await data.loadVersion(props.args.version_id)
  } catch {
    version.value = null
  }
  if (version.value) data.ensure.page(version.value.node_id)
})

const node = computed(() => version.value && flatten(data.nodes.value ?? []).find((n) => n.id === version.value.node_id))
const current = computed(() => data.pages.value?.[version.value?.node_id]?.content_md)
const partial = computed(() => (version.value?.preview ?? '').length >= PREVIEW_LENGTH)
const before = computed(() => (partial.value ? current.value?.slice(0, PREVIEW_LENGTH) : current.value))
</script>

<template>
  <StatusText v-if="version === undefined" class="text-meta" :delay="300" :text="t('chat.preview.loadingVersion')" working />
  <div v-else-if="version && node" class="flex flex-col gap-2">
    <DescriptionList>
      <DescriptionItem :term="node.title" class="py-1.5">{{ t('chat.preview.versionOf', { date: formatDate(version.created_at) }) }}</DescriptionItem>
    </DescriptionList>
    <CodeDiff
      v-if="typeof current === 'string'"
      :before="before"
      :after="version.preview"
      :file="`${node.title}.md`"
      :animate="false"
    />
    <p v-if="partial" class="m-0 text-meta text-fg-muted">{{ t('chat.preview.versionOpening') }}</p>
    <Callout type="note">{{ t('chat.preview.keptFirst') }}</Callout>
  </div>
</template>
