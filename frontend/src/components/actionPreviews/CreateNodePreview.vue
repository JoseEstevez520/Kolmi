<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeGroup, NavTreeItem } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// create_node: the new section or page, in its place in the tree.
const props = defineProps({ args: { type: Object, default: () => ({}) } })
const { t } = useI18n()
const data = usePreviewData()
data.ensure.nodes()

const parent = computed(() =>
  props.args.parent_id == null ? null : flatten(data.nodes.value).find((n) => n.id === props.args.parent_id),
)
const title = computed(() => String(props.args.title ?? '').trim())
// A parent that is not in the tree is a stale or wrong id: draw nothing rather than guess.
const known = computed(() => props.args.parent_id == null || Boolean(parent.value))
</script>

<template>
  <NavTree v-if="title && known" model-value="new" :label="t('chat.preview.toCreate')">
    <NavTreeGroup v-if="parent" :label="parent.title" default-open>
      <NavTreeItem value="new">{{ title }}</NavTreeItem>
    </NavTreeGroup>
    <NavTreeItem v-else value="new">{{ title }}</NavTreeItem>
  </NavTree>
</template>
