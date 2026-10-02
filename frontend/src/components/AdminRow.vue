<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, ConfirmButton, Input, useTruncated } from 'elastic-ui'
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

const { t } = useI18n()

const chosen = computed(() => nodeIcon(props.node))
const fallback = computed(() =>
  props.node.kind === 'section' ? (props.open ? FolderOpen : Folder) : FileText,
)

// The title fades at its end only when it runs past its room.
const titleEl = ref(null)
const truncated = useTruncated(titleEl, () => props.node.title)

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
      <Input v-model="draft" :aria-label="t('admin.rename')" autofocus />
      <Button type="submit" variant="ghost" size="icon" :icon="Check" :aria-label="t('common.save')" />
      <Button variant="ghost" size="icon" :icon="X" :aria-label="t('common.cancel')" @click="cancel" />
    </form>

    <template v-else>
      <Button variant="link" class="min-w-0 flex-1 justify-start text-fg" @click="start">
        <span ref="titleEl" class="min-w-0 overflow-hidden whitespace-nowrap" :class="truncated && 'mask-fade-r'">
          {{ node.title }}
        </span>
      </Button>

      <div class="flex shrink-0 items-center gap-1">
        <slot name="actions" />

        <Button
          variant="ghost"
          size="icon"
          :icon="ArrowUp"
          :aria-label="t('admin.moveUp')"
          :disabled="!canMoveUp"
          @click="call(moveUp)"
        />
        <Button
          variant="ghost"
          size="icon"
          :icon="ArrowDown"
          :aria-label="t('admin.moveDown')"
          :disabled="!canMoveDown"
          @click="call(moveDown)"
        />
        <ConfirmButton variant="ghost" tone="danger" :label="t('admin.delete', { title: node.title })" :action="remove" />
      </div>
    </template>
  </div>
</template>
