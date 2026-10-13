<script setup>
import { computed } from 'vue'
import { Breadcrumbs, Markdown } from 'elastic-ui'
import { trailTo } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// create_note / update_note: the note as it would read, under the place it hints at.
const props = defineProps({ args: { type: Object, default: () => ({}) } })
const data = usePreviewData()
data.ensure.nodes()

const text = computed(() => (typeof props.args.content === 'string' ? props.args.content.trim() : ''))
const trail = computed(() =>
  props.args.node_id == null ? [] : trailTo(props.args.node_id, data.nodes.value).map(({ node }) => ({ label: node.title })),
)
</script>

<template>
  <div v-if="text" class="flex flex-col gap-2">
    <Breadcrumbs v-if="trail.length" :items="trail" />
    <Markdown :source="text" />
  </div>
</template>
