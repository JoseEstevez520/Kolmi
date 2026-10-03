<script setup>
import { useI18n } from 'vue-i18n'
import { NavTreeGroup, NavTreeItem } from 'elastic-ui'
import { prefetchNode } from '../lib/content.js'
import { nodeIcon } from '../lib/icons.js'

// One node of the tree in the sidebar: a section with something inside is a group that folds its
// nodes, its label still a link to the section; anything else is an item. Only the top level
// shows its icon, which is also what the folded sidebar's rail keeps.
defineOptions({ name: 'NavNode' })
const props = defineProps({
  node: { type: Object, required: true },
  // Which sections are open, by id; shared by the whole tree.
  open: { type: Object, required: true },
  top: { type: Boolean, default: false },
})

const { t } = useI18n()
const to = `/node/${props.node.id}`
</script>

<template>
  <NavTreeGroup
    v-if="node.kind === 'section' && node.children?.length"
    v-model:open="open[node.id]"
    :label="node.title"
    :icon="top ? nodeIcon(node) : undefined"
    :value="to"
    :to="to"
    :toggle-label="t('sidebar.toggleSection', { name: node.title })"
  >
    <NavNode v-for="child in node.children" :key="child.id" :node="child" :open="open" />
  </NavTreeGroup>

  <NavTreeItem
    v-else
    :value="to"
    :to="to"
    :icon="top ? nodeIcon(node) : undefined"
    @pointerenter="prefetchNode(node.id)"
  >
    {{ node.title }}
  </NavTreeItem>
</template>
