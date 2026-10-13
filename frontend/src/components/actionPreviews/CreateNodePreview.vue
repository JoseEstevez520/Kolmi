<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeGroup, NavTreeItem } from 'elastic-ui'
import { flatten } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'
import { trimAround } from '../../lib/treeContext.js'

// create_node: the new section or page, in its place in the tree: its parent and the last
// two siblings before it, the rest left out.
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
// New nodes go last in their parent.
const context = computed(() => {
  const siblings = parent.value ? (parent.value.children ?? []) : data.nodes.value
  return trimAround([...siblings, { id: 'new', title: title.value }], siblings.length)
})
</script>

<template>
  <NavTree v-if="title && known" static :label="t('chat.preview.toCreate')">
    <NavTreeGroup v-if="parent" :label="parent.title" default-open>
      <NavTreeItem v-for="n in context.items" :key="n.id" :value="n.id" :mark="n.id === 'new' ? 'new' : undefined">{{ n.title }}</NavTreeItem>
    </NavTreeGroup>
    <template v-else>
      <NavTreeItem v-for="n in context.items" :key="n.id" :value="n.id" :mark="n.id === 'new' ? 'new' : undefined">{{ n.title }}</NavTreeItem>
    </template>
  </NavTree>
  <p v-if="title && known && context.hidden" class="m-0 mt-1 text-meta text-fg-faint">
    {{ t('chat.preview.more', { n: context.hidden }) }}
  </p>
</template>
