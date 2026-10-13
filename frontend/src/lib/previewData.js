import { inject, ref } from 'vue'
import { api } from './api.js'
import { loadNode, loadNodes, nodes, pages } from './content.js'

// What an action preview draws from: data the app already has (the cached tree, a page's
// Markdown, the timetable, the class's people). Nothing is read until a preview asks for it, and
// each source is read once per session. A preview takes it with `usePreviewData()`; the
// gallery (/dev/actions) provides its own static copy under the same key, so the same
// components are drawn without the API.
export const PREVIEW_DATA = Symbol('actionPreviewData')

const schedule = ref(null) // { events, settings }
const users = ref(null)
let scheduleRequest = null
let usersRequest = null

const quiet = () => {}

const real = {
  nodes,
  pages,
  schedule,
  users,
  ensure: {
    nodes: () => loadNodes().catch(quiet),
    page: (id) => loadNode(id).catch(quiet),
    schedule: () => {
      scheduleRequest ??= Promise.all([api.scheduleEvents(), api.settings()])
        .then(([events, settings]) => {
          schedule.value = { events, settings }
        })
        .catch(() => {
          scheduleRequest = null
        })
      return scheduleRequest
    },
    users: () => {
      usersRequest ??= api
        .users()
        .then((list) => {
          users.value = list
        })
        .catch(() => {
          usersRequest = null
        })
      return usersRequest
    },
  },
}

export const usePreviewData = () => inject(PREVIEW_DATA, real)
