<script setup>
import { computed } from 'vue'
import { FileText, Folder, FolderOpen } from '@lucide/vue'
import { nodeIcon } from '../lib/icons.js'

// A node's mark in a row: its own icon in its colour, or, with none, a plain folder (open as the
// section is) or page, in grey, as everywhere else in the app.
const props = defineProps({
  node: { type: Object, required: true },
  open: { type: Boolean, default: false },
})

const chosen = computed(() => nodeIcon(props.node))
const fallback = computed(() => (props.node.kind === 'section' ? (props.open ? FolderOpen : Folder) : FileText))
</script>

<template>
  <component :is="chosen || fallback" class="size-4" :class="!chosen && 'text-fg-muted'" :stroke-width="1.5" />
</template>
