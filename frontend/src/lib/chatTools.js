import {
  CalendarPlus,
  CalendarX,
  FilePlus,
  FileText,
  FileX,
  FolderInput,
  History,
  Pencil,
  Play,
  RefreshCw,
  Trash2,
  Wrench,
} from '@lucide/vue'
import { t, te } from './i18n.js'

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
}

export const toolIcon = (tool) => ICONS[tool] ?? Wrench
export const toolLabel = (tool) => (te(`chat.tools.${tool}`) ? t(`chat.tools.${tool}`) : tool)
