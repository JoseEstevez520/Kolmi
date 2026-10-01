<script setup>
import { computed, inject } from 'vue'
import AdminCreateDialog from './AdminCreateDialog.vue'
import AdminNodeDialog from './AdminNodeDialog.vue'
import AdminRow from './AdminRow.vue'

// One node of the admin tree, and its children under it: a recursive tree
// (design.md, "Screens"). Every row can be renamed, edited, moved, reordered,
// have something added inside it, and be deleted.
const props = defineProps({
  node: { type: Object, required: true },
  siblings: { type: Array, required: true },
  index: { type: Number, required: true },
})

const admin = inject('adminTree')

const children = computed(() => props.node.children ?? [])
const canMoveUp = computed(() => props.index > 0)
const canMoveDown = computed(() => props.index < props.siblings.length - 1)

async function reorderTo(delta) {
  const target = props.index + delta
  if (target < 0 || target >= props.siblings.length) return
  const ids = props.siblings.map((node) => node.id)
  ;[ids[props.index], ids[target]] = [ids[target], ids[props.index]]
  await admin.reorder(ids)
}
</script>

<template>
  <div class="flex flex-col gap-2">
    <AdminRow
      :node="node"
      :can-move-up="canMoveUp"
      :can-move-down="canMoveDown"
      :rename="(title) => admin.update(node.id, { title })"
      :move-up="() => reorderTo(-1)"
      :move-down="() => reorderTo(1)"
      :remove="() => admin.remove(node.id)"
    >
      <template #actions>
        <AdminNodeDialog :node="node" />
        <AdminCreateDialog :parent-id="node.id" :parent-title="node.title" />
      </template>
    </AdminRow>

    <div v-if="children.length" class="flex flex-col gap-2 border-l border-border pl-4">
      <AdminNode
        v-for="(child, i) in children"
        :key="child.id"
        :node="child"
        :siblings="children"
        :index="i"
      />
    </div>
  </div>
</template>
