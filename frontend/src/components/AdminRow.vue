<script setup>
import { computed, ref } from 'vue'
import { Button, ConfirmButton, Input } from 'elastic-ui'
import { ArrowDown, ArrowUp, Check, FileText, Folder, FolderOpen, X } from '@lucide/vue'
import { nodeIcon } from '../lib/icons.js'

// One row of the admin tree, read like a file explorer: a section is a folder
// (open or closed), a page is a file. It shows the node's own icon when it has
// one, otherwise the folder/file default, with the title editable in place and
// the row's actions (add inside, edit, move up/down, delete) at the end.
const props = defineProps({
  node: { type: Object, required: true },
  open: { type: Boolean, default: true },
  canMoveUp: { type: Boolean, default: false },
  canMoveDown: { type: Boolean, default: false },
  rename: { type: Function, required: true },
  moveUp: { type: Function, default: null },
  moveDown: { type: Function, default: null },
  remove: { type: Function, required: true },
})

const chosen = computed(() => nodeIcon(props.node))
const fallback = computed(() =>
  props.node.kind === 'section' ? (props.open ? FolderOpen : Folder) : FileText,
)

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
  <div
    class="flex min-w-0 items-center gap-1.5 px-1.5 py-1"
  >
    <slot name="toggle" />

    <component
      :is="chosen || fallback"
      class="size-4 shrink-0"
      :class="!chosen && 'text-fg-muted'"
      :stroke-width="1.5"
    />

    <form v-if="editing" class="flex min-w-0 flex-1 items-center gap-1" @submit.prevent="save">
      <Input v-model="draft" aria-label="Rename" autofocus />
      <Button type="submit" variant="ghost" size="icon" :icon="Check" aria-label="Save" />
      <Button variant="ghost" size="icon" :icon="X" aria-label="Cancel" @click="cancel" />
    </form>

    <template v-else>
      <button
        type="button"
        class="focus-ring min-w-0 flex-1 truncate rounded-[var(--radius-sm)] text-left text-label font-medium text-fg hover:text-fg-secondary"
        @click="start"
      >
        {{ node.title }}
      </button>

      <div class="flex shrink-0 items-center gap-1">
        <slot name="actions" />

        <Button
          variant="ghost"
          size="icon"
          :icon="ArrowUp"
          aria-label="Move up"
          :disabled="!canMoveUp"
          @click="call(moveUp)"
        />
        <Button
          variant="ghost"
          size="icon"
          :icon="ArrowDown"
          aria-label="Move down"
          :disabled="!canMoveDown"
          @click="call(moveDown)"
        />
        <ConfirmButton variant="ghost" tone="danger" :label="`Delete ${node.title}`" :action="remove" />
      </div>
    </template>
  </div>
</template>
