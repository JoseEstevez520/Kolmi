<script setup>
import { computed, inject } from 'vue'
import { TreeDragItem } from 'elastic-ui'
import AdminRow from './AdminRow.vue'

// One node of the admin tree, and its children under it when it is open: a recursive tree that
// reads like folders (sections, which fold open) and files (pages). A row can be dragged to
// another place (or moved with Alt and the arrows).
const props = defineProps({
  node: { type: Object, required: true },
  siblings: { type: Array, required: true },
  index: { type: Number, required: true },
  level: { type: Number, default: 1 },
})

const admin = inject('adminTree')

const children = computed(() => props.node.children ?? [])
const isSection = computed(() => props.node.kind === 'section')
const hasChildren = computed(() => children.value.length > 0)
const open = computed(() => hasChildren.value && admin.isOpen(props.node.id))
const groupId = computed(() => `admin-group-${props.node.id}`)
</script>

<template>
  <li role="none" class="flex flex-col gap-0.5">
    <TreeDragItem :id="node.id" :parent-id="node.parent_id ?? null" :index="index" :section="isSection" :count="children.length">
      <AdminRow
        :node="node"
        :open="open"
        :foldable="hasChildren"
        :count="children.length"
        :level="level"
        :selected="String(admin.selectedId.value) === String(node.id)"
        :tab-stop="admin.tabStop.value === String(node.id)"
        :owns="open ? groupId : undefined"
        @toggle="admin.toggle(node.id)"
        @select="admin.select(node.id)"
      />
    </TreeDragItem>

    <ul v-if="open" :id="groupId" role="group" class="ml-4 flex flex-col gap-0.5">
      <AdminNode
        v-for="(child, i) in children"
        :key="child.id"
        :node="child"
        :siblings="children"
        :index="i"
        :level="level + 1"
      />
    </ul>
  </li>
</template>
