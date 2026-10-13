import {
  CalendarPlus,
  CalendarX,
  FilePlus,
  FileText,
  FileX,
  FolderInput,
  History,
  Bug,
  Pencil,
  Play,
  RefreshCw,
  Trash2,
  Wrench,
} from '@lucide/vue'
import { t, te } from './i18n.js'
import { flatten } from './content.js'

// How a proposed tool call reads in the chat: an icon per tool the model can propose, and the
// label from `chat.tools.<name>` (a verb phrase). A tool with no entry still shows, under its
// raw name with a wrench.
const ICONS = {
  create_note: FilePlus,
  update_note: Pencil,
  delete_note: Trash2,
  create_node: FilePlus,
  update_node: Pencil,
  move_node: FolderInput,
  delete_node: Trash2,
  create_schedule_event: CalendarPlus,
  update_schedule_event: Pencil,
  delete_schedule_event: CalendarX,
  delete_file: FileX,
  rebuild_page: RefreshCw,
  run_pass: Play,
  restore_version: History,
  set_status: FileText,
  write_page_web: Pencil,
  report_bug: Bug,
  file_bug_report: Bug,
  discard_bug_report: Trash2,
}

export const toolIcon = (tool) => ICONS[tool] ?? Wrench
const generic = (tool) => (te(`chat.tools.${tool}`) ? t(`chat.tools.${tool}`) : tool)

// What each tool needs read before its title can use names: the tree or the class's people.
const NEEDS = {
  move_node: 'nodes',
  write_page: 'nodes',
  write_page_web: 'nodes',
  restore_version: 'nodes',
  update_node: 'nodes',
  delete_node: 'nodes',
  create_node: 'nodes',
  set_status: 'users',
  set_role: 'users',
  delete_user: 'users',
}
// Ask the data source (usePreviewData) for what the tool's title names. A no-op for the rest.
export const prepareLabel = (tool, data) => {
  const need = NEEDS[tool]
  if (need) data.ensure[need]()
}

const nodeOf = (data, id) => (id == null ? null : flatten(data.nodes.value ?? []).find((n) => n.id === id))
const userOf = (data, id) => data.users.value?.find((u) => String(u.id) === String(id))
const nameOf = (value) => (typeof value === 'string' ? value.trim() : '')
const kindKey = (kind) => (kind === 'page' ? 'page' : 'section')

// The title of a proposal's card. Names come from the data (tree titles, people) so it reads
// "Move Thymeleaf into Extra"; when a name is not known it falls back to the generic label.
// `data` is what usePreviewData() gives; without it, always the generic label.
export function toolLabel(tool, args = {}, data = null) {
  if (!data) return generic(tool)
  const title = (key, values) => (te(`chat.titles.${key}`) ? t(`chat.titles.${key}`, values) : null)
  const a = args ?? {}
  let out = null
  if (tool === 'move_node') {
    const node = nodeOf(data, a.node_id)
    if (node && 'parent_id' in a) {
      const parent = nodeOf(data, a.parent_id)
      if (a.parent_id == null) out = title('moveTop', { node: node.title })
      else if (parent) out = title('move', { node: node.title, parent: parent.title })
    }
  } else if (tool === 'write_page' || tool === 'update_node') {
    const node = nodeOf(data, a.node_id)
    if (node) out = title(tool === 'write_page' ? 'writePage' : 'updateNode', { node: node.title })
  } else if (tool === 'write_page_web') {
    const node = nodeOf(data, a.node_id)
    if (node) out = title('writePageWeb', { node: node.title })
  } else if (tool === 'delete_node') {
    const node = nodeOf(data, a.node_id)
    if (node) out = title('deleteNode', { node: node.title, kind: t(`chat.titles.${kindKey(node.kind)}`) })
  } else if (tool === 'create_node') {
    const name = nameOf(a.title)
    if (name) {
      const kind = t(`chat.titles.${kindKey(a.kind)}`)
      const pages = Array.isArray(a.children) ? a.children.length : 0
      out = pages
        ? t('chat.titles.createNodeWith', { title: name, kind, n: pages }, pages)
        : title('createNode', { title: name, kind })
    }
  } else if (tool === 'set_status' || tool === 'set_role' || tool === 'delete_user') {
    const ids = Array.isArray(a.user_ids) ? a.user_ids : [a.user_id]
    const people = ids.map((id) => userOf(data, id))
    if (people.length > 1 && tool === 'set_status' && a.status === 'active') {
      out = t('chat.titles.approveMany', { n: people.length }, people.length)
    } else if (people.length === 1 && people[0]) {
      const name = people[0].name
      if (tool === 'set_role') out = title(a.role === 'admin' ? 'makeAdmin' : 'makeStudent', { name })
      else if (tool === 'delete_user') out = title('removeUser', { name })
      else if (a.status === 'active') out = title('approve', { name })
      else if (a.status === 'blocked') out = title('block', { name })
      else if (a.status === 'pending') out = title('hold', { name })
    }
  }
  return out ?? generic(tool)
}
