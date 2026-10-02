<script setup>
import { onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { FloatingMenu } from '@tiptap/vue-3/menus'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'
import { TaskItem, TaskList } from '@tiptap/extension-list'
import { TableKit } from '@tiptap/extension-table'
import { Button, SuggestionMenu, SuggestionMenuEmpty, SuggestionMenuItem } from 'elastic-ui'
import { Plus } from '@lucide/vue'
import { findBlocks } from '../lib/editor/blocks.js'
import { BlockHint } from '../lib/editor/hint.js'
import { SlashMenu } from '../lib/editor/slash.js'

// The note's body, written like a page: nothing on screen but the text. Blocks come from one
// menu with two ways in, as in Notion: typing "/" anywhere, or the "+" that shows beside an
// empty line. Bold and italic are the usual Ctrl+B and Ctrl+I, and Markdown typed by hand
// (`## `, `- `, ``` ``` ```) still turns into its block for whoever knows it. The text is
// Markdown in and out (v-model), so the daily pass reads it as it reads any note.
const model = defineModel({ type: String, default: '' })

const props = defineProps({
  placeholder: { type: String, default: '' },
  label: { type: String, default: '' },
})

const { t } = useI18n()

const blockLabel = (block) => t(`notes.blocks.${block.id}`)

// Each empty block says what it is, as in Notion: a heading waits as "Heading", code as
// "Code", and a plain line offers the "/" menu.
const INSIDE = {
  listItem: 'notes.blocks.bulletList',
  taskItem: 'notes.blocks.taskList',
  blockquote: 'notes.blocks.quote',
}

function hintOf(node, parent) {
  if (node.type.name === 'heading') {
    return t(node.attrs.level === 2 ? 'notes.blocks.heading' : 'notes.blocks.subheading')
  }
  if (node.type.name === 'codeBlock') return t('notes.blocks.codeBlock')
  // A line inside a list or a quote names what holds it; a table's cell stays blank.
  if (INSIDE[parent.type.name]) return t(INSIDE[parent.type.name])
  if (parent.type.name === 'tableCell' || parent.type.name === 'tableHeader') return ''
  return props.placeholder
}

// The "+" beside an empty line of text; a heading or a list item that is empty already says
// what it is.
function showPlus({ view, state }) {
  const { $anchor, empty } = state.selection
  return (
    view.hasFocus() &&
    empty &&
    $anchor.depth === 1 &&
    $anchor.parent.type.name === 'paragraph' &&
    $anchor.parent.childCount === 0
  )
}

// What the "/" menu shows; the SlashMenu extension keeps it up to date, and passes the menu
// keys on to the SuggestionMenu, which holds the highlighted block.
const slash = reactive({ open: false, items: [], rect: null, command: null })
const highlighted = ref()
const menu = ref(null)
const keys = {
  next: () => menu.value?.next(),
  previous: () => menu.value?.previous(),
  pick: () => menu.value?.pick() ?? false,
}

function apply(id) {
  const block = slash.items.find((item) => item.id === id)
  if (block) slash.command?.(block)
}

const editor = useEditor({
  content: model.value,
  contentType: 'markdown',
  extensions: [
    StarterKit.configure({ heading: { levels: [2, 3] }, underline: false }),
    TaskList,
    TaskItem.configure({ nested: true }),
    TableKit.configure({ table: { resizable: false } }),
    Markdown,
    BlockHint.configure({ text: hintOf }),
    SlashMenu.configure({ state: slash, keys, find: (query, inTable) => findBlocks(query, blockLabel, inTable) }),
  ],
  editorProps: {
    attributes: {
      class: 'prose min-h-[50vh] outline-none',
      'aria-multiline': 'true',
      ...(props.label && { 'aria-label': props.label }),
    },
  },
  onUpdate: ({ editor }) => {
    model.value = editor.isEmpty ? '' : editor.getMarkdown()
  },
})

// A value set from outside (a draft or a saved note arriving) replaces what is written.
watch(model, (value) => {
  const current = editor.value
  if (!current) return
  const written = current.isEmpty ? '' : current.getMarkdown()
  if (value !== written) current.commands.setContent(value, { contentType: 'markdown', emitUpdate: false })
})

onBeforeUnmount(() => editor.value?.destroy())

// The "+" opens the same menu as typing does.
function openBlocks() {
  editor.value?.chain().focus().insertContent('/').run()
}

defineExpose({
  focus: () => editor.value?.commands.focus('start'),
})
</script>

<template>
  <div class="note-editor">
    <FloatingMenu v-if="editor" :editor="editor" :options="{ placement: 'left', offset: 12 }" :should-show="showPlus">
      <Button
        variant="ghost"
        size="icon"
        :icon="Plus"
        :aria-label="t('notes.blocks.open')"
        @mousedown.prevent
        @click="openBlocks"
      />
    </FloatingMenu>

    <EditorContent :editor="editor" />

    <SuggestionMenu
      ref="menu"
      v-model:open="slash.open"
      v-model="highlighted"
      :reference="slash.rect"
      :label="t('notes.blocks.title')"
      @select="apply"
    >
      <SuggestionMenuItem v-for="block in slash.items" :key="block.id" :value="block.id" :icon="block.icon">
        {{ blockLabel(block) }}
      </SuggestionMenuItem>
      <SuggestionMenuEmpty v-if="!slash.items.length">{{ t('notes.blocks.none') }}</SuggestionMenuEmpty>
    </SuggestionMenu>
  </div>
</template>

<style scoped>
/* The empty block being written says what it is, in the fields' faint tone. It keeps the
   block's own type, so an empty heading already shows at a heading's size. */
.note-editor :deep(.ProseMirror-focused [data-placeholder])::before,
.note-editor :deep([data-empty-doc])::before {
  content: attr(data-placeholder);
  float: left;
  height: 0;
  pointer-events: none;
  color: var(--color-fg-faint);
}

/* Tiptap's table: cells hold paragraphs, which take no margin there, and the cells picked
   for a row or column action are marked. Prose draws the rest of the table. */
.note-editor :deep(.ProseMirror table) {
  table-layout: fixed;
}
.note-editor :deep(.ProseMirror :is(td, th) > p) {
  margin: 0;
}
.note-editor :deep(.ProseMirror .selectedCell) {
  background: var(--color-bg-muted);
}
</style>
