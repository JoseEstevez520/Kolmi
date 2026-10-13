<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { Callout, CodeDiff } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// write_page: replace shows the page's current Markdown against the new one; merge has no text
// to compare (the notes agent merges it when it runs), so it only says so.
const props = defineProps({ args: { type: Object, default: () => ({}) } })
const { t } = useI18n()
const data = usePreviewData()
data.ensure.nodes()
data.ensure.page(props.args.node_id)

const node = computed(() => flatten(data.nodes.value).find((n) => n.id === props.args.node_id))
const current = computed(() => data.pages.value[props.args.node_id]?.content_md)
const merge = computed(() => props.args.mode === 'merge')
const replace = computed(
  () => !merge.value && node.value && typeof current.value === 'string' && typeof props.args.markdown === 'string',
)
</script>

<template>
  <Callout v-if="node && merge" type="note" :title="node.title">{{ t('chat.preview.merge') }}</Callout>
  <CodeDiff
    v-else-if="replace"
    :before="current"
    :after="args.markdown"
    :file="`${node.title}.md`"
    :animate="false"
  />
</template>
