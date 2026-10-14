<script setup>
import { useI18n } from 'vue-i18n'
import { CommandEmpty, CommandInput, CommandItem, CommandList, CommandPalette } from 'elastic-ui'
import { FileText, Folder } from '@lucide/vue'
import { nodeIcon } from '../lib/icons.js'

// Find a node by title anywhere in the tree: the library's command palette, opened from the
// screen's search icon (or Ctrl/Cmd K), one result per node with where it sits. Picking one says so.
const props = defineProps({
  nodes: { type: Array, required: true },
  byId: { type: Map, required: true },
})
const emit = defineEmits(['pick'])
const open = defineModel('open', { type: Boolean, default: false })
const { t } = useI18n()

// Where a node sits, from the top, without its own title.
function place(node) {
  const trail = []
  for (let up = props.byId.get(String(node.parent_id)); up; up = props.byId.get(String(up.parent_id))) trail.unshift(up.title)
  return trail.join(' / ')
}
</script>

<template>
  <CommandPalette v-model:open="open" :trigger="false" shortcut="mod+k" :label="t('admin.search')">
    <CommandInput />
    <CommandList>
      <CommandEmpty />
      <CommandItem
        v-for="node in nodes"
        :key="node.id"
        :value="String(node.id)"
        :keywords="[node.title, place(node)]"
        :icon="nodeIcon(node) || (node.kind === 'section' ? Folder : FileText)"
        @select="emit('pick', node.id)"
      >
        {{ node.title }}
        <span v-if="place(node)" class="ml-2 text-fg-faint">{{ place(node) }}</span>
      </CommandItem>
    </CommandList>
  </CommandPalette>
</template>
