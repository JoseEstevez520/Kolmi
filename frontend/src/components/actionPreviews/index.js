import CreateNotePreview from './CreateNotePreview.vue'
import CreateNodePreview from './CreateNodePreview.vue'
import DeletePreview from './DeletePreview.vue'
import MoveNodePreview from './MoveNodePreview.vue'
import ScheduleEventPreview from './ScheduleEventPreview.vue'
import UserChangePreview from './UserChangePreview.vue'
import WritePagePreview from './WritePagePreview.vue'

// A proposal's tool → the picture of what it would do, drawn under its card. Each component
// gets `tool` and `args` and builds the picture from data the app already has (lib/previewData.js);
// it draws nothing when that data is missing, so the plain card stays. A tool with no entry
// has no picture. Add one here when a new action has something worth showing.
const PREVIEWS = {
  create_note: CreateNotePreview,
  update_note: CreateNotePreview,
  move_node: MoveNodePreview,
  write_page: WritePagePreview,
  create_node: CreateNodePreview,
  create_schedule_event: ScheduleEventPreview,
  update_schedule_event: ScheduleEventPreview,
  delete_schedule_event: ScheduleEventPreview,
  set_status: UserChangePreview,
  set_role: UserChangePreview,
  delete_node: DeletePreview,
  delete_user: DeletePreview,
}

export const previewFor = (tool) => PREVIEWS[tool] ?? null
