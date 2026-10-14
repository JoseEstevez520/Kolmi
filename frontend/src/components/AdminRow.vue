<script setup>
import { Button, TruncatedText } from 'elastic-ui'
import { ChevronRight } from '@lucide/vue'
import NodeMark from './NodeMark.vue'

// One row of the admin tree, as quiet as a file explorer's: a chevron where there is something
// to open, the node's mark and its title. Nothing else: what is done to a node is done in the
// panel. The picked row is lit by tone. It is an item of a WAI-ARIA tree: the tree's keys are
// handled one level up (AdminContentView), and only one row takes Tab (`tabStop`).
const emit = defineEmits(['toggle', 'select'])
defineProps({
  node: { type: Object, required: true },
  open: { type: Boolean, default: false },
  // A section with rows under it folds.
  foldable: { type: Boolean, default: false },
  count: { type: Number, default: 0 },
  level: { type: Number, default: 1 },
  selected: { type: Boolean, default: false },
  tabStop: { type: Boolean, default: false },
  owns: { type: String, default: undefined },
})
</script>

<template>
  <div
    role="treeitem"
    :data-node="node.id"
    :aria-level="level"
    :aria-selected="selected"
    :aria-expanded="foldable ? open : undefined"
    :aria-owns="owns"
    :tabindex="tabStop ? 0 : -1"
    :class="[
      'flex min-h-8 min-w-0 items-center gap-1.5 rounded-md py-1 pr-2 pl-1 text-ui outline-none focus-ring-inset [@media(pointer:coarse)]:min-h-11',
      'scroll-mt-[calc(var(--page-header-height)+1rem)] cursor-pointer transition-colors duration-150',
      selected ? 'bg-bg-inset text-fg' : 'text-fg-secondary hover:bg-bg-muted hover:text-fg',
    ]"
    @click="emit('select')"
  >
    <!-- The pointer's way to fold it; the keyboard has the arrow keys. -->
    <Button
      v-if="foldable"
      variant="ghost"
      size="icon"
      class="size-6 shrink-0"
      tabindex="-1"
      aria-hidden="true"
      @click.stop="emit('toggle')"
    >
      <ChevronRight :class="['size-4 transition-transform duration-150', open && 'rotate-90']" :stroke-width="1.5" />
    </Button>
    <span v-else class="size-6 shrink-0" aria-hidden="true" />

    <NodeMark :node="node" :open="open" class="shrink-0" />
    <TruncatedText class="min-w-0 flex-1">{{ node.title }}</TruncatedText>
    <span v-if="foldable && !open" class="text-meta tabular-nums text-fg-faint">{{ count }}</span>
  </div>
</template>
