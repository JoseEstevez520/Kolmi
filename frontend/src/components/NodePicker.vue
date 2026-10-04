<script setup>
import { computed } from 'vue'
import { NavTree, NavTreeItem, PopoverMorph, TruncatedText } from 'elastic-ui'
import { Folder } from '@lucide/vue'
import PlaceTree from './PlaceTree.vue'
import { nodes } from '../lib/content.js'

// Pick a node from the tree, as a quiet ghost button that opens it: its label is the picked
// node's short path, or `noneLabel` when nothing is picked. Used by the note editor's "Where
// does it go?" and the timetable editor's "Which page?" alike, so both pick a node the same
// way. The tree's items need a non-empty value, so "none" travels under a sentinel.
const NONE = '__none__'

const props = defineProps({
  modelValue: { type: [Number, String, null], default: null },
  // Shown in the trigger when nothing is picked, as a question ("Where does it go?").
  placeholder: { type: String, required: true },
  // The menu's "nothing picked" option; defaults to `placeholder` when they'd read the same.
  noneLabel: { type: String, default: null },
  label: { type: String, required: true },
  icon: { type: [Object, Function], default: () => Folder },
})
const emit = defineEmits(['update:modelValue'])
const none = computed(() => props.noneLabel ?? props.placeholder)

const picked = computed({
  get: () => (props.modelValue == null ? NONE : String(props.modelValue)),
  set: (value) => emit('update:modelValue', value === NONE ? null : Number(value)),
})

// Each node's path from the top, to name the picked one by its last two steps.
const paths = computed(() => {
  const out = new Map()
  const walk = (items, trail) => {
    for (const item of items) {
      const path = [...trail, item.title]
      out.set(String(item.id), path)
      if (item.children?.length) walk(item.children, path)
    }
  }
  walk(nodes.value, [])
  return out
})
const pickedPath = computed(() => paths.value.get(picked.value)?.slice(-2).join(' / ') ?? '')
</script>

<template>
  <PopoverMorph
    variant="ghost"
    size="sm"
    align="end"
    fluid
    class="min-w-0 text-fg-muted"
    :label="pickedPath ? `${label} ${pickedPath}` : label"
  >
    <template #trigger>
      <component :is="icon" class="size-4 shrink-0" aria-hidden="true" />
      <TruncatedText class="min-w-0">{{ pickedPath || placeholder }}</TruncatedText>
    </template>
    <template #default="{ close }">
      <NavTree v-model="picked" selectable :label="label" @select="close">
        <NavTreeItem :value="NONE">{{ none }}</NavTreeItem>
        <PlaceTree :items="nodes" />
      </NavTree>
    </template>
  </PopoverMorph>
</template>
