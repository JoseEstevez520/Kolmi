import { inject, ref } from 'vue'
import { api } from './api.js'
import { flatten, loadNode, loadNodes, nodes, pages } from './content.js'

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

// restore_version carries only a version id, and the versions endpoint is per page: look through
// the pages' lists until the id turns up, once per id (a page's list is read once too).
const versionLists = new Map()
const versionFound = new Map()
async function findVersion(versionId) {
  const key = String(versionId)
  if (!versionFound.has(key)) {
    versionFound.set(
      key,
      (async () => {
        await loadNodes()
        const leaves = flatten(nodes.value ?? []).filter((n) => n.kind === 'page')
        for (const leaf of leaves) {
          if (!versionLists.has(leaf.id)) versionLists.set(leaf.id, api.pageVersions(leaf.id).catch(() => []))
          const hit = (await versionLists.get(leaf.id)).find((v) => String(v.id) === key)
          if (hit) return { ...hit, node_id: leaf.id }
        }
        return null
      })().catch(() => {
        versionFound.delete(key)
        return null
      }),
    )
  }
  return versionFound.get(key)
}

const real = {
  nodes,
  pages,
  schedule,
  users,
  // The notes students have left (admin's list_notes, through GET /notes), read fresh each
  // time: it is asked for only when a delete preview shows, to count what points at a node.
  loadNotes: () => api.adminNotes(),
  // The version a restore names ({ id, created_at, preview, node_id }), or null when not found.
  loadVersion: findVersion,
  // Whether a pass is running now and whether the scheduled ones are on, read fresh each time.
  loadPassState: async () => {
    const [latest, settings] = await Promise.all([api.adminPasses({ limit: 1 }), api.settings()])
    const last = latest[0]
    // The server counts a "running" pass as stale after two hours (passes/daily.py).
    const fresh = last?.status === 'running' && Date.now() - new Date(last.started_at).getTime() < 120 * 60_000
    return { running: Boolean(fresh), enabled: settings.pass_enabled !== false }
  },
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
