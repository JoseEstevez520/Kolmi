import {
  BetweenHorizontalEnd,
  BetweenVerticalEnd,
  Heading2,
  Heading3,
  List,
  ListChecks,
  ListOrdered,
  Minus,
  Pilcrow,
  SquareCode,
  Table,
  TextQuote,
  Trash2,
} from '@lucide/vue'

// The blocks a note can hold, as the "/" menu offers them. Each turns the current line into
// itself. `words` are what a search matches besides the label, in both languages, so `/code`
// and `/cod` find the same block whatever the app's language. Inside a table, the menu
// offers the table's own actions instead (TABLE_ACTIONS).
export const BLOCKS = [
  { id: 'text', icon: Pilcrow, words: ['text', 'texto', 'paragraph', 'parrafo', 'p'], run: (c) => c.setParagraph() },
  { id: 'heading', icon: Heading2, words: ['heading', 'titulo', 'h2'], run: (c) => c.setHeading({ level: 2 }) },
  { id: 'subheading', icon: Heading3, words: ['subheading', 'subtitulo', 'h3'], run: (c) => c.setHeading({ level: 3 }) },
  { id: 'bulletList', icon: List, words: ['list', 'lista', 'bullet', 'ul'], run: (c) => c.toggleBulletList() },
  { id: 'orderedList', icon: ListOrdered, words: ['numbered', 'numerada', 'ordered', 'ol'], run: (c) => c.toggleOrderedList() },
  { id: 'taskList', icon: ListChecks, words: ['checklist', 'todo', 'tareas', 'task', 'check'], run: (c) => c.toggleTaskList() },
  { id: 'quote', icon: TextQuote, words: ['quote', 'cita', 'blockquote'], run: (c) => c.toggleBlockquote() },
  { id: 'codeBlock', icon: SquareCode, words: ['code', 'codigo', 'snippet'], run: (c) => c.setCodeBlock() },
  { id: 'divider', icon: Minus, words: ['divider', 'separador', 'hr', 'line', 'linea'], run: (c) => c.setHorizontalRule() },
  {
    id: 'table',
    icon: Table,
    words: ['table', 'tabla', 'grid'],
    run: (c) => c.insertTable({ rows: 3, cols: 3, withHeaderRow: true }),
  },
]

export const TABLE_ACTIONS = [
  { id: 'addRow', icon: BetweenHorizontalEnd, words: ['row', 'fila', 'add', 'anadir'], run: (c) => c.addRowAfter() },
  { id: 'addColumn', icon: BetweenVerticalEnd, words: ['column', 'columna', 'add', 'anadir'], run: (c) => c.addColumnAfter() },
  { id: 'deleteRow', icon: Trash2, words: ['row', 'fila', 'delete', 'borrar'], run: (c) => c.deleteRow() },
  { id: 'deleteColumn', icon: Trash2, words: ['column', 'columna', 'delete', 'borrar'], run: (c) => c.deleteColumn() },
  { id: 'deleteTable', icon: Trash2, words: ['table', 'tabla', 'delete', 'borrar'], run: (c) => c.deleteTable() },
]

// Lower case and without accents, so "código" and "codigo" are one word.
const plain = (text) => text.normalize('NFD').replace(/\p{Diacritic}/gu, '').toLowerCase()

/** The blocks (or, in a table, its actions) whose label or words start with what was typed. */
export function findBlocks(query, label, inTable = false) {
  const options = inTable ? TABLE_ACTIONS : BLOCKS
  const q = plain(query.trim())
  if (!q) return options
  return options.filter((block) =>
    [label(block), ...block.words].some((word) =>
      plain(word).split(/\s+/).some((part) => part.startsWith(q)),
    ),
  )
}
