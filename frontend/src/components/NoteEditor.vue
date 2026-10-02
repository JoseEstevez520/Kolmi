<script setup>
import { computed, nextTick, onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { FloatingMenu } from '@tiptap/vue-3/menus'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'
import { TaskItem, TaskList } from '@tiptap/extension-list'
import { TableKit } from '@tiptap/extension-table'
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

// What the "/" menu shows; the SlashMenu extension keeps it up to date.
const slash = reactive({ open: false, items: [], index: 0, rect: null, command: null })

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
    SlashMenu.configure({ state: slash, find: (query, inTable) => findBlocks(query, blockLabel, inTable) }),
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

// Under the "/", or over it when the line is near the bottom of the screen.
const MENU_HEIGHT = 320
const menuStyle = computed(() => {
  const rect = slash.rect
  if (!rect) return { display: 'none' }
  const below = rect.bottom + 6 + MENU_HEIGHT <= window.innerHeight
  return {
    left: `${Math.max(8, Math.min(rect.left, window.innerWidth - 272))}px`,
    ...(below ? { top: `${rect.bottom + 6}px` } : { bottom: `${window.innerHeight - rect.top + 6}px` }),
  }
})

const list = ref(null)
watch(
  () => slash.index,
  async (index) => {
    await nextTick()
    list.value?.children[index]?.scrollIntoView({ block: 'nearest' })
  },
)

defineExpose({
  focus: () => editor.value?.commands.focus('start'),
})
</script>

<template>
  <div class="note-editor">
    <FloatingMenu v-if="editor" :editor="editor" :options="{ placement: 'left', offset: 12 }" :should-show="showPlus">
      <button
        type="button"
        class="grid size-7 cursor-pointer place-items-center rounded-[var(--radius-sm)] text-fg-faint transition-colors duration-150 hover:bg-bg-muted hover:text-fg focus-ring"
        :aria-label="t('notes.blocks.open')"
        @mousedown.prevent
        @click="openBlocks"
      >
        <Plus class="size-4" />
      </button>
    </FloatingMenu>

    <EditorContent :editor="editor" />

    <Teleport to="body">
      <div
        v-if="slash.open"
        class="fixed z-50 w-64 overflow-hidden rounded-[var(--radius-lg)] border border-border bg-surface-raised shadow-overlay animate-[blur-in_0.2s_var(--ease-soft)_both] motion-reduce:animate-none"
        :style="menuStyle"
      >
        <ul
          v-if="slash.items.length"
          ref="list"
          role="listbox"
          :aria-label="t('notes.blocks.title')"
          class="max-h-80 overflow-y-auto overscroll-contain p-1.5 scrollbar-subtle"
        >
          <li
            v-for="(block, i) in slash.items"
            :key="block.id"
            role="option"
            :aria-selected="i === slash.index"
            :data-highlighted="i === slash.index ? '' : undefined"
            class="flex cursor-pointer items-center gap-2.5 rounded-[var(--radius-sm)] px-2.5 py-2 text-ui text-fg select-none data-[highlighted]:bg-bg-muted"
            @mouseenter="slash.index = i"
            @mousedown.prevent="slash.command?.(block)"
          >
            <component :is="block.icon" class="size-4 shrink-0 text-fg-muted" />
            {{ blockLabel(block) }}
          </li>
        </ul>
        <p v-else class="px-3 py-3 text-ui text-fg-muted">{{ t('notes.blocks.none') }}</p>
      </div>
    </Teleport>
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

/* A table as the pages draw theirs, with the cell being written marked. */
.note-editor :deep(.ProseMirror table) {
  table-layout: fixed;
}
.note-editor :deep(.ProseMirror :is(td, th) > p) {
  margin: 0;
}
.note-editor :deep(.ProseMirror .selectedCell) {
  background: var(--color-bg-muted);
}

/* A checklist: the box beside its line, and a done item in a quieter tone. */
.note-editor :deep(ul[data-type='taskList']) {
  list-style: none;
  padding-left: 0;
}
.note-editor :deep(ul[data-type='taskList'] li) {
  display: flex;
  align-items: baseline;
  gap: 0.6em;
}
.note-editor :deep(ul[data-type='taskList'] li > label input) {
  accent-color: var(--color-accent);
  cursor: pointer;
}
.note-editor :deep(ul[data-type='taskList'] li > div) {
  flex: 1;
}
.note-editor :deep(ul[data-type='taskList'] li[data-checked='true'] > div) {
  color: var(--color-fg-muted);
  text-decoration: line-through;
}
</style>
