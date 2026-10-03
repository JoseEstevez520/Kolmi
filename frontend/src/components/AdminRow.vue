<script setup>
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { Button, ConfirmButton, Input, TruncatedText } from 'elastic-ui'
import { Check, FileText, Folder, FolderOpen, X } from '@lucide/vue'
import { nodeIcon } from '../lib/icons.js'

// One row of the admin tree, read like a file explorer: a section is a folder
// (open or closed), a page is a file. It shows the node's own icon when it has
// one, otherwise the folder/file default, with the title editable in place. At rest
// it is only that; the grip and the row's actions (add inside, edit, delete) come in
// when the row is pointed at or focused, and stay on a screen with no hover.
const props = defineProps({
  node: { type: Object, required: true },
  open: { type: Boolean, default: true },
  rename: { type: Function, required: true },
  remove: { type: Function, required: true },
})

const { t } = useI18n()

// Out of sight at rest, in when the row is pointed at or has focus inside it (TreeDragItem's group).
const reveal =
  'transition-opacity duration-150 opacity-0 group-hover/row:opacity-100 group-focus-within/row:opacity-100 [@media(pointer:coarse)]:opacity-100'

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

</script>

<template>
  <div class="flex min-w-0 items-center gap-1.5 px-1.5 py-1">
    <div :class="[reveal, 'flex items-center']"><slot name="handle" /></div>
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
        <TruncatedText class="min-w-0">{{ node.title }}</TruncatedText>
      </Button>

      <div :class="[reveal, 'flex shrink-0 items-center gap-1']">
        <slot name="actions" />
        <ConfirmButton variant="ghost" tone="danger" :label="t('admin.delete', { title: node.title })" :action="remove" />
      </div>
    </template>
  </div>
</template>
