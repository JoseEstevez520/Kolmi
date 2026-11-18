<script setup>
import { onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { BubbleMenu, FloatingMenu } from '@tiptap/vue-3/menus'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'
import { TaskItem, TaskList } from '@tiptap/extension-list'
import { TableKit } from '@tiptap/extension-table'
import { Button, SuggestionMenu, SuggestionMenuEmpty, SuggestionMenuItem } from 'elastic-ui'
import { Plus, Sparkles } from '@lucide/vue'
import { findBlocks } from '../lib/editor/blocks.js'
import { BlockHint } from '../lib/editor/hint.js'
import { SlashMenu } from '../lib/editor/slash.js'
import { Arrows } from '../lib/editor/arrows.js'
import { AI_LANGUAGE, AiCodeBlock, aiWriting, withoutAi } from '../lib/editor/aiBlock.js'

// The note's body, written like a page: nothing on screen but the text. Blocks come from one
// menu with two ways in, as in Notion: typing "/" anywhere, or the "+" that shows beside an
// empty line. Bold and italic are the usual Ctrl+B and Ctrl+I, and Markdown typed by hand
// (`## `, `- `, ``` ``` ```) still turns into its block for whoever knows it. The text is
// Markdown in and out (v-model), so the daily pass reads it as it reads any note.
const model = defineModel({ type: String, default: '' })
// When the AI couldn't write (no session, the day's limit, a failed answer): its message.
const emit = defineEmits(['ai-error'])

const props = defineProps({
  placeholder: { type: String, default: '' },
  label: { type: String, default: '' },
  // The AI in the note, when it is on: `assist(text, note, onToken, onFix)` streams what the AI
  // writes about a line or a selection, hands back a mended piece (by its index among the
  // answer's pieces, or null to drop it), and resolves when it ends. Null: no AI.
  assist: { type: Function, default: null },
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
    StarterKit.configure({ heading: { levels: [2, 3] }, underline: false, codeBlock: false }),
    AiCodeBlock,
    Arrows,
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
    // Ctrl/Cmd+Enter: the AI on the selection, or on the line the cursor is on.
    handleKeyDown: (view, event) => {
      if (!props.assist || event.key !== 'Enter' || !(event.ctrlKey || event.metaKey)) return false
      return run()
    },
  },
  onUpdate: ({ editor }) => {
    model.value = editor.isEmpty ? '' : editor.getMarkdown()
  },
})

// A value set from outside (a saved note arriving) replaces what is written.
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

// ---- The AI in the note ----
// The text of the block the cursor is in.
function currentLine() {
  const { $from } = editor.value.state.selection
  return $from.parent.textContent
}

const busy = ref(false)

// The AI on a line or a selection: one gesture, and the AI tells what it is. A question becomes
// notes on it, in its place; the student's own notes get the piece that shows them, under them.
// Its first line says which (%%ask or %%complete). What it writes is Markdown (with pieces as
// ```kolmi-ai fences), part of the note from the start: the class following it live sees it
// arrive, and it reads as the note's own, not as a chat.
function run() {
  const ed = editor.value
  if (!ed || !props.assist || busy.value) return false
  const { from, to, empty, $from, $to } = ed.state.selection
  const text = (empty ? currentLine() : ed.state.doc.textBetween(from, to, '\n')).trim()
  if (!text) return false
  const note = withoutAi(ed.getMarkdown())

  // The blocks the text is in, and the place under them.
  const blockStart = $from.before(1)
  const blockEnd = $to.after(1)
  let range = null
  const track = ({ transaction }) => {
    if (range) range = { from: transaction.mapping.map(range.from, -1), to: transaction.mapping.map(range.to, 1) }
  }
  ed.on('transaction', track)

  let received = ''
  let queued = false
  const render = () => {
    queued = false
    const newline = received.indexOf('\n')
    if (newline < 0) return
    if (!range) {
      // The first line says what it did; a model that forgets is read by the text itself.
      const tag = received.slice(0, newline).trim()
      const ask = tag === '%%ask' || (tag !== '%%complete' && text.endsWith('?'))
      range = ask ? { from: blockStart, to: blockEnd } : { from: blockEnd, to: blockEnd }
    }
    let markdown = received.slice(newline + 1).replace(/^%%(ask|complete)\s*$/m, '').trimStart()
    if (!markdown) return
    // A fence still being written is closed, so what follows it doesn't fall inside.
    if ((markdown.match(/^```/gm) || []).length % 2) markdown += '\n```'
    ed.chain()
      .command(({ tr }) => {
        tr.setMeta('addToHistory', false)
        return true
      })
      .insertContentAt(range, markdown, { contentType: 'markdown', updateSelection: false })
      .run()
  }

  busy.value = true
  aiWriting.value = true
  props
    .assist(
      text,
      note,
      (token) => {
        received += token
        if (!queued) {
          queued = true
          requestAnimationFrame(render)
        }
      },
      // A piece that wouldn't draw, mended once it ended (or dropped): put in its place.
      (index, program) => {
        let at = -1
        received = received.replace(/```kolmi-ai[^\n]*\n[\s\S]*?```\n?/g, (fence) => {
          at++
          if (at !== index) return fence
          return program ? '```kolmi-ai\n' + program + '\n```\n' : ''
        })
      },
    )
    // Nothing came, or it failed: the note stays as it was, and the writer is told why.
    .catch((e) => emit('ai-error', e?.message || ''))
    .finally(() => {
      if (!received.includes('\n')) received += '\n'
      render()
      ed.off('transaction', track)
      aiWriting.value = false
      busy.value = false
    })
  return true
}

// The selection's own menu, only with the AI on: ask about it, or complete it.
function showAiMenu({ state, from, to }) {
  return Boolean(props.assist) && from !== to && !busy.value && state.selection.$from.parent.type.name !== 'codeBlock'
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

    <BubbleMenu v-if="editor && assist" :editor="editor" :should-show="showAiMenu" :options="{ placement: 'top' }">
      <div class="flex rounded-lg bg-surface-raised p-1">
        <Button
          variant="ghost"
          size="icon"
          :icon="Sparkles"
          :aria-label="t('notes.ai.help')"
          :title="t('notes.ai.help')"
          @mousedown.prevent
          @click="run"
        />
      </div>
    </BubbleMenu>

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
