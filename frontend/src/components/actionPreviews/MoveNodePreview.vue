<script setup>
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeGroup, NavTreeItem } from 'elastic-ui'
import { flatten, trailTo } from '../../lib/content.js'
import { usePreviewData } from '../../lib/previewData.js'

// move_node: the sections the node leaves and enters, before and after, with the node lit.
const props = defineProps({ args: { type: Object, default: () => ({}) } })
const { t } = useI18n()
const data = usePreviewData()
data.ensure.nodes()

const node = computed(() => flatten(data.nodes.value).find((n) => n.id === props.args.node_id))
const oldParentId = computed(() => {
  const trail = trailTo(props.args.node_id, data.nodes.value)
  return trail.length > 1 ? trail[trail.length - 2].node.id : null
})
// `parent_id` left out means it stays where it is, only reordered.
const newParentId = computed(() => ('parent_id' in props.args ? props.args.parent_id : oldParentId.value))

const childrenOf = (parentId) =>
  parentId == null ? data.nodes.value : (flatten(data.nodes.value).find((n) => n.id === parentId)?.children ?? [])

// The node's siblings in a parent, with the node placed as the move says.
function placed(parentId) {
  const others = childrenOf(parentId).filter((n) => n.id !== node.value.id)
  if (parentId !== newParentId.value) return others
  const { placement, after_node_id: after } = props.args
  const at = placement === 'first' ? 0 : placement === 'after' ? others.findIndex((n) => n.id === after) + 1 : -1
  if (placement === 'after' && at === 0) return [...others, node.value]
  if (at >= 0) return [...others.slice(0, at), node.value, ...others.slice(at)]
  // No placement: it keeps its place within the same parent, goes last in a new one.
  if (parentId === oldParentId.value) {
    const index = childrenOf(parentId).findIndex((n) => n.id === node.value.id)
    return [...others.slice(0, index), node.value, ...others.slice(index)]
  }
  return [...others, node.value]
}

const parentIds = computed(() => [...new Set([oldParentId.value, newParentId.value])])
const labelOf = (parentId) =>
  parentId == null ? t('chat.preview.topLevel') : flatten(data.nodes.value).find((n) => n.id === parentId)?.title
// Both parents must be known to draw the move; otherwise the plain card stays.
const known = computed(() => node.value && parentIds.value.every((id) => id == null || labelOf(id)))

const columns = computed(() => [
  { key: 'before', label: t('chat.preview.before'), list: (id) => childrenOf(id) },
  { key: 'after', label: t('chat.preview.after'), list: placed },
])
</script>

<template>
  <div v-if="known" class="grid grid-cols-1 gap-4 sm:grid-cols-2">
    <div v-for="column in columns" :key="column.key">
      <p class="m-0 mb-1 text-meta text-fg-faint">{{ column.label }}</p>
      <NavTree :model-value="node.id" :label="column.label">
        <NavTreeGroup v-for="id in parentIds" :key="id ?? 'top'" :label="labelOf(id)" default-open>
          <NavTreeItem v-for="n in column.list(id)" :key="n.id" :value="n.id">{{ n.title }}</NavTreeItem>
        </NavTreeGroup>
      </NavTree>
    </div>
  </div>
</template>
