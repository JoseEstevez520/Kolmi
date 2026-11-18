<script setup>
import { onBeforeUnmount, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { EditorContent, useEditor } from '@tiptap/vue-3'
import { BubbleMenu, FloatingMenu } from '@tiptap/vue-3/menus'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'
import { TaskItem, TaskList } from '@tiptap/extension-list'
import { TableKit } from '@tiptap/extension-table'
import { Image } from '@tiptap/extension-image'
import { Button, SuggestionMenu, SuggestionMenuEmpty, SuggestionMenuItem, createStreamPace, wholeWords } from 'elastic-ui'
import { Plus, Sparkles } from '@lucide/vue'
import { findBlocks } from '../lib/editor/blocks.js'
import { BlockHint } from '../lib/editor/hint.js'
import { SlashMenu } from '../lib/editor/slash.js'
import { Arrows } from '../lib/editor/arrows.js'
import { AI_OWN, AiRegions, aiRegion, setAiRegion, shiftAiRegions } from '../lib/editor/aiStatus.js'
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
  // The AI in the note, when it is on: `assist(text, note, onToken, onFix, onStatus, signal)`
  // streams what the AI writes about a line or a selection, hands back a mended piece (by its
  // index among the answer's pieces, or null to drop it), says what it is doing, stops when
  // `signal` aborts, and resolves when it ends. Null: no AI.
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
    AiRegions,
    // A photo in the note (the AI's, from Wikimedia Commons, with its credit under it).
    Image.configure({ inline: true, HTMLAttributes: { loading: 'lazy', decoding: 'async' } }),
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
      if (event.key === 'Escape') return stopAll()
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


// The AI on a line or a selection: one gesture, and the AI tells what it is. A question becomes
// notes on it, in its place; the student's own notes get the piece that shows them, under them.
// Its first line says which (%%ask or %%complete). What it writes is Markdown (with pieces as
// ```kolmi-ai fences), part of the note from the start: the class following it live sees it
// arrive, and it reads as the note's own, not as a chat.
let nextRun = 0
// The answers on their way, to stop them (Esc).
const running = new Set()

function run() {
  const ed = editor.value
  if (!ed || !props.assist) return false
  const { from, to, empty, $from, $to } = ed.state.selection
  const text = (empty ? currentLine() : ed.state.doc.textBetween(from, to, '\n')).trim()
  if (!text) return false
  const note = withoutAi(ed.getMarkdown())
  const id = `ai-${++nextRun}`

  // Its place lives in the editor (AiRegions), which moves it with every edit, the writer's or
  // another answer's: `from` where it starts, `to` where it ends, `mid` between the blocks
  // already finished (written once, never touched again) and the block still arriving (redrawn
  // as tokens come). Several answers can fill their places at once.
  const blockStart = $from.before(1)
  const blockEnd = $to.after(1)
  const own = (run) =>
    run(
      ed.chain().command(({ tr }) => {
        tr.setMeta(AI_OWN, true).setMeta('addToHistory', false)
        return true
      }),
    ).run()

  // The writer goes on at once, on a fresh line under the place the answer will fill.
  const after = ed.state.doc.nodeAt(blockEnd)
  if (!(after && after.type.name === 'paragraph' && after.content.size === 0)) {
    own((c) => c.insertContentAt(blockEnd, { type: 'paragraph' }))
    // Another answer filling the block right under keeps its place, without this line.
    shiftAiRegions(ed, blockEnd, 2)
  }
  ed.commands.setTextSelection(blockEnd + 1)
  setAiRegion(ed, id, { from: blockStart, to: blockEnd, mid: null, status: t('notes.ai.thinking') })

  // Replace the arriving part (mid..to) with `markdown`, keeping the line being written where it
  // is on screen when the answer grows above it.
  const put = (markdown) => {
    const r = aiRegion(ed, id)
    const head = ed.state.selection.head
    const above = head >= r.to
    const top = above ? ed.view.coordsAtPos(head).top : 0
    // Delete, then insert between blocks: replacing a whole paragraph in one go would pour the
    // new blocks into it (a heading would arrive as a paragraph).
    own((c) => {
      const chain = r.to > r.mid ? c.deleteRange({ from: r.mid, to: r.to }) : c
      return markdown ? chain.insertContentAt(r.mid, markdown, { contentType: 'markdown', updateSelection: false }) : chain
    })
    if (above) {
      const moved = ed.view.coordsAtPos(ed.state.selection.head).top - top
      if (moved) window.scrollBy(0, moved)
    }
  }

  // Where the finished blocks of `markdown` end: the last blank line outside a fence.
  const stableLength = (markdown) => {
    let inFence = false
    let at = 0
    let stable = 0
    for (const line of markdown.split('\n')) {
      if (line.startsWith('```')) inFence = !inFence
      at += line.length + 1
      if (!inFence && line.trim() === '' && at <= markdown.length) stable = at
    }
    return stable
  }

  // What arrived (`received`), and what is on show (`revealed`): the library's steady pace, a
  // whole word at a time, instead of the model's bursts (createStreamPace, as the chat does).
  let received = ''
  let revealed = ''
  let committed = 0
  let queued = false
  let done = false
  const render = (final = false) => {
    queued = false
    const newline = revealed.indexOf('\n')
    if (newline < 0) return
    let r = aiRegion(ed, id)
    if (!r) return
    if (r.mid == null) {
      // The first line says what it did; a model that forgets is read by the text itself. A
      // question is replaced (the place is its block); notes stay and the answer goes under.
      const tag = revealed.slice(0, newline).trim()
      const ask = tag === '%%ask' || (tag !== '%%complete' && text.endsWith('?'))
      setAiRegion(ed, id, ask ? { mid: r.from } : { from: r.to, mid: r.to })
      r = aiRegion(ed, id)
    }
    const markdown = revealed.slice(newline + 1).replace(/^%%(ask|complete)\s*$/m, '').trimStart()
    if (!markdown && !final) return
    const stable = final ? markdown.length : stableLength(markdown)
    if (stable > committed) {
      // Trimmed: a finished block's blank line would become an empty paragraph.
      put(markdown.slice(committed, stable).trim())
      setAiRegion(ed, id, { mid: aiRegion(ed, id).to })
      committed = stable
    }
    // A photo waits for its block to finish, so it is put in (and loads) once.
    let tail = final ? '' : markdown.slice(committed).replace(/^!\[.*$/gm, '').trim()
    // A fence still being written is closed, so what follows it doesn't fall inside.
    if ((tail.match(/^```/gm) || []).length % 2) tail += '\n```'
    r = aiRegion(ed, id)
    if (tail || r.to > r.mid) put(tail)
    setAiRegion(ed, id, { status: null })
  }

  let quiet = false
  // A photo's line (a long link nobody reads) is shown whole as soon as it has arrived, so the
  // pace doesn't spend seconds on it while nothing seems to happen.
  let jumpTo = 0
  const show = (n) => {
    revealed = wholeWords(received, n, !done, quiet)
    const lineStart = revealed.lastIndexOf('\n') + 1
    const lineEnd = received.indexOf('\n', lineStart)
    if (lineEnd > 0 && /^(!\[|\*Imagen:|\*Image:)/.test(received.slice(lineStart, lineEnd))) jumpTo = Math.max(jumpTo, lineEnd + 1)
    if (jumpTo > revealed.length) revealed = received.slice(0, jumpTo)
    if (!queued) {
      queued = true
      requestAnimationFrame(() => render())
    }
  }
  let finished = false
  const finish = () => {
    if (finished) return
    finished = true
    pace.stop()
    try {
      revealed = received.includes('\n') ? received : received + '\n'
      render(true)
    } finally {
      setAiRegion(ed, id, null)
      running.delete(controller)
      aiWriting.value--
    }
  }
  const pace = createStreamPace({
    onFrame: show,
    onQuiet: () => {
      quiet = true
      show(pace.shown)
    },
    // Once the model is done and everything is on show, the answer ends.
    onCaughtUp: () => {
      if (done) finish()
    },
  })

  const controller = new AbortController()
  running.add(controller)
  aiWriting.value++
  setAiRegion(ed, id, { writing: true })
  props
    .assist(
      text,
      note,
      (token) => {
        received += token
        pace.update(received, true)
      },
      // A piece that wouldn't draw, mended once it ended (or dropped): the whole answer is put
      // in again, with the mended piece in its place.
      (index, program) => {
        let at = -1
        received = received.replace(/```kolmi-ai[^\n]*\n[\s\S]*?```\n?/g, (fence) => {
          at++
          if (at !== index) return fence
          return program ? '```kolmi-ai\n' + program + '\n```\n' : ''
        })
        const r = aiRegion(ed, id)
        if (r && r.mid != null) {
          setAiRegion(ed, id, { mid: r.from })
          committed = 0
        }
        pace.update(received, true)
      },
      // What it is doing while nothing arrives: thinking, or looking for an image.
      (status) => {
        const r = aiRegion(ed, id)
        if (r && (r.mid == null || /image/i.test(status))) {
          setAiRegion(ed, id, { status: /image/i.test(status) ? t('notes.ai.searchingImage') : t('notes.ai.thinking') })
        }
      },
      controller.signal,
    )
    // Nothing came, or it failed: the note stays as it was, and the writer is told why. Stopped
    // by the writer (Esc): what arrived stays, nothing to say.
    .catch((e) => {
      if (!controller.signal.aborted) emit('ai-error', e?.message || '')
    })
    .finally(() => {
      done = true
      // Stopped by the writer: what is on show stays, at once. Otherwise the rest comes in at
      // the pace's flush and the answer ends when it has caught up.
      if (controller.signal.aborted) {
        received = revealed
        finish()
      } else {
        pace.update(received, false)
        if (pace.shown >= received.length) finish()
      }
    })
  return true
}

// Esc stops every answer on its way; what arrived stays.
function stopAll() {
  if (!running.size) return false
  for (const controller of running) controller.abort()
  return true
}

// The selection's own menu, only with the AI on: ask about it, or complete it.
function showAiMenu({ state, from, to }) {
  return Boolean(props.assist) && from !== to && state.selection.$from.parent.type.name !== 'codeBlock'
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
/* The words just arrived, in ink (as the chat's, elastic-ui's ink-wave): at the very end faint,
   soft and in an aurora colour, sharper and drying into the text's colour further back. Static per
   band, so redrawing the text never restarts it; the front moves on with the text. */
.note-editor :deep(.ai-wave-3) {
  opacity: 0.35;
  filter: blur(2px);
  color: color-mix(in oklab, var(--ink-flow) 85%, var(--color-fg));
}
.note-editor :deep(.ai-wave-2) {
  opacity: 0.7;
  filter: blur(0.6px);
  color: color-mix(in oklab, var(--ink-flow) 70%, var(--color-fg));
}
.note-editor :deep(.ai-wave-1) {
  color: color-mix(in oklab, var(--ink-flow) 40%, var(--color-fg-secondary));
  transition: color 600ms ease-out;
}
@media (prefers-reduced-motion: reduce) {
  .note-editor :deep(:is(.ai-wave-3, .ai-wave-2, .ai-wave-1)) {
    opacity: 1;
    filter: none;
    color: inherit;
  }
}

/* What the AI is doing while nothing has arrived: a quiet line where its answer will go. */
.note-editor :deep(.ai-status) {
  margin: 0.5em 0;
  color: var(--color-fg-muted);
}

/* A photo the AI put in comes into focus once, as it arrives. */
.note-editor :deep(.ProseMirror img) {
  border-radius: var(--radius-md);
  animation: note-photo-in 0.5s ease-out;
}
@keyframes note-photo-in {
  from {
    opacity: 0;
    filter: blur(6px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .note-editor :deep(.ProseMirror img) {
    animation: none;
  }
}

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
