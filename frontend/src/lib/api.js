import { accessToken } from './auth.js'
import { t } from './i18n.js'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

// `keepalive` lets a request outlive the page, for a save as the tab closes.
async function request(path, { method = 'GET', body, keepalive = false } = {}) {
  const token = accessToken()
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'
  if (token) headers.Authorization = `Bearer ${token}`

  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body !== undefined ? JSON.stringify(body) : undefined,
      keepalive,
    })
  } catch {
    throw new ApiError(0, t('api.unreachable'))
  }

  const text = await response.text()
  let data = null
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      data = text
    }
  }

  if (!response.ok) {
    const message =
      (data && typeof data === 'object' && data.detail) || response.statusText || t('api.failed')
    throw new ApiError(response.status, message)
  }

  return data
}

export const api = {
  getProfile: () => request('/profile'),

  register: ({ code, name }) => request('/register', { method: 'POST', body: { code, name } }),

  createNote: ({ content, format = 'text', nodeId = null, keepalive }) =>
    request('/notes', { method: 'POST', body: { content, format, node_id: nodeId }, keepalive }),

  updateNote: ({ noteId, content, format = 'markdown', nodeId = null, keepalive }) =>
    request('/notes/update', {
      method: 'POST',
      body: { note_id: noteId, content, format, node_id: nodeId },
      keepalive,
    }),

  myNotes: () => request('/notes/mine'),

  // Browsing: the whole tree, and one node with its children (and, for a page,
  // its text).
  nodes: () => request('/nodes'),

  node: (nodeId) => request(`/node?node_id=${encodeURIComponent(nodeId)}`),

  // Admin, the AI log: the passes, what the AI did with each note or page, and
  // the notes students have left.
  adminPasses: ({ limit = 20 } = {}) => request(`/passes?limit=${encodeURIComponent(limit)}`),

  adminAiLog: ({ passId = null, since = null, limit = 100 } = {}) => {
    const query = new URLSearchParams()
    if (passId != null) query.set('pass_id', passId)
    if (since) query.set('since', since)
    query.set('limit', limit)
    return request(`/ai-log?${query}`)
  },

  adminNotes: ({ status = null, nodeId = null } = {}) => {
    const query = new URLSearchParams()
    if (status) query.set('status', status)
    if (nodeId != null) query.set('node_id', nodeId)
    const suffix = query.toString()
    return request(`/notes${suffix ? `?${suffix}` : ''}`)
  },

  // The class settings: the class language, the one the AI writes the shared notes and pages
  // in. Anyone signed in reads them; only an admin changes them.
  settings: () => request('/settings'),

  updateSettings: ({ classLanguage }) =>
    request('/settings', { method: 'POST', body: { class_language: classLanguage } }),

  // Admin, the tree. The backend stores whatever fields it is given, so a node
  // is created with its icon, colour and home flag from the start.
  createNode: ({ parentId = null, kind, title, description, icon, color, onHome }) => {
    const body = { parent_id: parentId, kind, title }
    if (description !== undefined) body.description = description
    if (icon !== undefined) body.icon = icon
    if (color !== undefined) body.color = color
    if (onHome !== undefined) body.on_home = onHome
    return request('/node', { method: 'POST', body })
  },

  updateNode: ({ nodeId, ...patch }) =>
    request('/node/update', { method: 'POST', body: { node_id: nodeId, ...patch } }),

  moveNode: ({ nodeId, parentId = null }) =>
    request('/node/move', { method: 'POST', body: { node_id: nodeId, parent_id: parentId } }),

  reorderNodes: ({ ids }) => request('/node/reorder', { method: 'POST', body: { ids } }),

  deleteNode: ({ nodeId }) =>
    request('/node/delete', { method: 'POST', body: { node_id: nodeId } }),
}
