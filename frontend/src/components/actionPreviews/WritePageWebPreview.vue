<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, DescriptionItem, DescriptionList } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// write_page_web: the page and how big the new web is. OpenUI Lang is not worth a diff; what
// matters is that it replaces the web only, the Markdown stays, and the server checks it first.
const props = defineProps({ args: { type: Object, default: () => ({}) } })
const { t } = useI18n()
const data = usePreviewData()
data.ensure.nodes()

const node = computed(() => flatten(data.nodes.value ?? []).find((n) => n.id === props.args.node_id))
const lines = computed(() => (typeof props.args.content_web === 'string' ? props.args.content_web.trim().split('\n').length : 0))
</script>

<template>
  <div v-if="node && lines" class="flex flex-col gap-2">
    <DescriptionList>
      <DescriptionItem :term="node.title" class="py-1.5">{{ t('chat.preview.webLines', { n: lines }, lines) }}</DescriptionItem>
    </DescriptionList>
    <Callout type="note">{{ t('chat.preview.webReplaces') }}</Callout>
  </div>
</template>
