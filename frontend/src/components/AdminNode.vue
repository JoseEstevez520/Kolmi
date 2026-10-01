<script setup>
import { computed, inject, ref } from 'vue'
import { ChevronRight, Plus } from '@lucide/vue'
import AdminCreateDialog from './AdminCreateDialog.vue'
import AdminNodeDialog from './AdminNodeDialog.vue'
import AdminRow from './AdminRow.vue'

// One node of the admin tree, and its children under it: a recursive tree that
// reads like folders (sections, which fold open) and files (pages). Every row
// can be renamed, edited, moved, reordered, have something added inside it, and
// be deleted.
const props = defineProps({
  node: { type: Object, required: true },
  siblings: { type: Array, required: true },
  index: { type: Number, required: true },
})

const admin = inject('adminTree')

const children = computed(() => props.node.children ?? [])
const isSection = computed(() => props.node.kind === 'section')
const hasChildren = computed(() => children.value.length > 0)
const open = ref(true)

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
  <li class="flex flex-col">
    <AdminRow
      :node="node"
      :open="hasChildren && open"
      :can-move-up="canMoveUp"
      :can-move-down="canMoveDown"
      :rename="(title) => admin.update(node.id, { title })"
      :move-up="() => reorderTo(-1)"
      :move-down="() => reorderTo(1)"
      :remove="() => admin.remove(node.id)"
    >
      <template #toggle>
        <button
          v-if="hasChildren"
          type="button"
          class="focus-ring flex size-6 shrink-0 items-center justify-center rounded-[var(--radius-sm)] text-fg-muted hover:bg-bg-muted hover:text-fg"
          :aria-label="open ? `Collapse ${node.title}` : `Expand ${node.title}`"
          :aria-expanded="open"
          @click="open = !open"
        >
          <ChevronRight
            class="size-4 transition-transform duration-150"
            :class="open && 'rotate-90'"
            :stroke-width="1.5"
          />
        </button>
        <span v-else class="size-6 shrink-0" aria-hidden="true" />
      </template>

      <template #actions>
        <AdminCreateDialog v-if="isSection" :parent-id="node.id" :parent-title="node.title">
          <template #trigger>
            <span class="inline-flex items-center gap-2">
              <Plus class="size-4" />
              <span class="sr-only">Add inside {{ node.title }}</span>
            </span>
          </template>
        </AdminCreateDialog>
        <AdminNodeDialog :node="node" />
      </template>
    </AdminRow>

    <ul v-if="hasChildren && open" class="ml-3 flex flex-col border-l border-border pl-3">
      <AdminNode
        v-for="(child, i) in children"
        :key="child.id"
        :node="child"
        :siblings="children"
        :index="i"
      />
    </ul>
  </li>
</template>
