<script setup>
import { computed, inject, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, TreeDragHandle, TreeDragItem } from 'elastic-ui'
import { ChevronRight, Plus } from '@lucide/vue'
import AdminCreateDialog from './AdminCreateDialog.vue'
import AdminNodeDialog from './AdminNodeDialog.vue'
import AdminRow from './AdminRow.vue'

// One node of the admin tree, and its children under it: a recursive tree that
// reads like folders (sections, which fold open) and files (pages). Every row
// can be renamed, edited, dragged to another place (by its grip, or Alt with the
// arrows), have something added inside it, and be deleted.
const props = defineProps({
  node: { type: Object, required: true },
  siblings: { type: Array, required: true },
  index: { type: Number, required: true },
})

const admin = inject('adminTree')
const { t } = useI18n()

const children = computed(() => props.node.children ?? [])
const isSection = computed(() => props.node.kind === 'section')
const hasChildren = computed(() => children.value.length > 0)
const open = ref(true)

</script>

<template>
  <li class="flex flex-col">
    <TreeDragItem :id="node.id" :parent-id="node.parent_id ?? null" :index="index" :section="isSection" :count="children.length">
    <AdminRow
      :node="node"
      :open="hasChildren && open"
      :rename="(title) => admin.update(node.id, { title })"
      :remove="() => admin.remove(node.id)"
    >
      <template #handle>
        <TreeDragHandle :label="t('admin.move')" />
      </template>

      <template #toggle>
        <Button
          v-if="hasChildren"
          variant="ghost"
          size="icon"
          class="size-6"
          :aria-label="t(open ? 'admin.collapse' : 'admin.expand', { title: node.title })"
          :aria-expanded="open"
          @click="open = !open"
        >
          <ChevronRight
            class="size-4 transition-transform duration-150"
            :class="open && 'rotate-90'"
            :stroke-width="1.5"
          />
        </Button>
        <span v-else class="size-6 shrink-0" aria-hidden="true" />
      </template>

      <template #actions>
        <AdminCreateDialog
          v-if="isSection"
          :parent-id="node.id"
          :parent-title="node.title"
          size="icon"
        >
          <template #trigger>
            <Plus class="size-4" aria-hidden="true" />
            <span class="sr-only">{{ t('admin.addInsideOf', { title: node.title }) }}</span>
          </template>
        </AdminCreateDialog>
        <AdminNodeDialog :node="node" />
      </template>
    </AdminRow>
    </TreeDragItem>

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
