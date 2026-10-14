<script setup>
import { computed, inject } from 'vue'
import { useI18n } from 'vue-i18n'
import { NavTree, NavTreeItem, PopoverMorph } from 'elastic-ui'
import { FolderInput } from '@lucide/vue'
import PlaceTree from './PlaceTree.vue'

// Move a node into another section: the sections as a tree to pick from, an alternative to dragging
// that works with the keyboard and on a touch screen. A section is never offered a place inside
// itself. Only a section may sit at the top level, so a page is not offered it.
const props = defineProps({
  node: { type: Object, required: true },
})

const admin = inject('adminTree')
const { t } = useI18n()

const TOP = '__top__'

// The sections only, without the node (and so nothing under it).
const sections = computed(() => {
  const prune = (items) =>
    items
      .filter((item) => item.kind === 'section' && item.id !== props.node.id)
      .map((item) => ({ ...item, children: prune(item.children ?? []) }))
  return prune(admin.rootNodes.value)
})

const here = computed(() => (props.node.parent_id == null ? TOP : String(props.node.parent_id)))

async function pick(value, close) {
  close()
  if (value === here.value) return
  try {
    await admin.move(props.node.id, value === TOP ? null : Number(value))
  } catch {
    // The page says what went wrong.
  }
}
</script>

<template>
  <PopoverMorph variant="ghost" size="icon" align="start" :label="t('admin.moveTo', { title: node.title })">
    <template #trigger>
      <FolderInput class="size-4" aria-hidden="true" />
      <span class="sr-only">{{ t('admin.moveTo', { title: node.title }) }}</span>
    </template>
    <template #default="{ close }">
      <NavTree :model-value="here" selectable :label="t('admin.moveTo', { title: node.title })" @select="(value) => pick(value, close)">
        <NavTreeItem v-if="node.kind === 'section'" :value="TOP">{{ t('admin.topLevel') }}</NavTreeItem>
        <PlaceTree :items="sections" />
      </NavTree>
    </template>
  </PopoverMorph>
</template>
