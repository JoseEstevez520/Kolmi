<script setup>
import { computed } from 'vue'
import { FileIcon, FolderIcon } from 'elastic-ui'
import { nodeIcon } from '../lib/icons.js'

// A node's mark in a row: its own icon in its colour, or, with none, a folder (which opens as the
// section does) or a page, tinted in the node's colour.
const props = defineProps({
  node: { type: Object, required: true },
  open: { type: Boolean, default: false },
})

const chosen = computed(() => nodeIcon(props.node))
const color = computed(() => props.node.color || undefined)
</script>

<template>
  <component :is="chosen" v-if="chosen" class="size-4" :stroke-width="1.5" />
  <FolderIcon v-else-if="node.kind === 'section'" :open="open" :color="color" size="xs" />
  <FileIcon v-else name="" :color="color" size="xs" />
</template>
