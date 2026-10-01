<script setup>
import { ref } from 'vue'
import { Badge, Button, ConfirmButton, Input } from 'elastic-ui'
import { ArrowDown, ArrowUp, Check, X } from '@lucide/vue'
import { nodeIcon } from '../lib/icons.js'

// One node in the admin tree: its kind, its icon, its title editable in place,
// the extra actions the tree gives it (edit, add inside), move up and move down,
// and a delete that asks first (ConfirmButton).
const props = defineProps({
  node: { type: Object, required: true },
  canMoveUp: { type: Boolean, default: false },
  canMoveDown: { type: Boolean, default: false },
  rename: { type: Function, required: true },
  moveUp: { type: Function, default: null },
  moveDown: { type: Function, default: null },
  remove: { type: Function, required: true },
})

const editing = ref(false)
const draft = ref('')

function start() {
  draft.value = props.node.title
  editing.value = true
}

function cancel() {
  editing.value = false
}

async function save() {
  const title = draft.value.trim()
  editing.value = false
  if (!title || title === props.node.title) return
  try {
    await props.rename(title)
  } catch {
    // The panel says what went wrong.
  }
}

function call(fn) {
  if (!fn) return
  Promise.resolve(fn()).catch(() => {})
}
</script>

<template>
  <div class="flex min-w-0 items-center gap-1.5">
    <component
      :is="nodeIcon(node)"
      v-if="nodeIcon(node)"
      class="size-4 shrink-0"
      :stroke-width="1.5"
    />
    <Badge size="sm" variant="soft" class="shrink-0">
      {{ node.kind === 'section' ? 'Section' : 'Page' }}
    </Badge>

    <form v-if="editing" class="flex min-w-0 flex-1 items-center gap-2" @submit.prevent="save">
      <Input v-model="draft" aria-label="Rename" autofocus />
      <Button type="submit" variant="ghost" size="icon" aria-label="Save">
        <Check class="size-4" />
      </Button>
      <Button type="button" variant="ghost" size="icon" aria-label="Cancel" @click="cancel">
        <X class="size-4" />
      </Button>
    </form>

    <template v-else>
      <button
        type="button"
        class="min-w-0 flex-1 truncate text-left text-sm font-medium text-fg hover:text-fg-secondary"
        @click="start"
      >
        {{ node.title }}
      </button>

      <slot name="actions" />

      <Button
        variant="ghost"
        size="icon"
        aria-label="Move up"
        :disabled="!canMoveUp"
        @click="call(moveUp)"
      >
        <ArrowUp class="size-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon"
        aria-label="Move down"
        :disabled="!canMoveDown"
        @click="call(moveDown)"
      >
        <ArrowDown class="size-4" />
      </Button>
      <ConfirmButton tone="danger" :label="`Delete ${node.title}`" :action="remove" />
    </template>
  </div>
</template>
