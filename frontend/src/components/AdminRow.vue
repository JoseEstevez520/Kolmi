<script setup>
import { ref } from 'vue'
import { Button, ConfirmButton, Input } from 'elastic-ui'
import { ArrowDown, ArrowUp, Check, Pencil, X } from '@lucide/vue'

// One module, section or page in the admin panel: its name, editable in place,
// with move up, move down and a delete that asks first (ConfirmButton).
const props = defineProps({
  value: { type: String, required: true },
  canMoveUp: { type: Boolean, default: false },
  canMoveDown: { type: Boolean, default: false },
  renameLabel: { type: String, default: 'Rename' },
  deleteLabel: { type: String, default: 'Delete' },
  rename: { type: Function, required: true },
  moveUp: { type: Function, default: null },
  moveDown: { type: Function, default: null },
  remove: { type: Function, required: true },
})

const editing = ref(false)
const draft = ref('')

function start() {
  draft.value = props.value
  editing.value = true
}

function cancel() {
  editing.value = false
}

async function save() {
  const name = draft.value.trim()
  editing.value = false
  if (!name || name === props.value) return
  try {
    await props.rename(name)
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
  <div class="flex min-w-0 items-center gap-1">
    <form v-if="editing" class="flex min-w-0 flex-1 items-center gap-2" @submit.prevent="save">
      <Input v-model="draft" :aria-label="renameLabel" autofocus />
      <Button type="submit" variant="ghost" size="icon" aria-label="Save">
        <Check class="size-4" />
      </Button>
      <Button type="button" variant="ghost" size="icon" aria-label="Cancel" @click="cancel">
        <X class="size-4" />
      </Button>
    </form>

    <template v-else>
      <span class="min-w-0 flex-1 truncate text-sm font-medium text-fg">{{ value }}</span>
      <Button variant="ghost" size="icon" :aria-label="renameLabel" @click="start">
        <Pencil class="size-4" />
      </Button>
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
      <ConfirmButton tone="danger" :label="deleteLabel" :action="remove" />
    </template>
  </div>
</template>
