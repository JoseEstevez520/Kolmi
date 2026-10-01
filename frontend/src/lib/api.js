import { accessToken } from './auth.js'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, { method = 'GET', body } = {}) {
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
    })
  } catch {
    throw new ApiError(0, 'Could not reach the server.')
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
      (data && typeof data === 'object' && data.detail) || response.statusText || 'Request failed'
    throw new ApiError(response.status, message)
  }

  return data
}

export const api = {
  getProfile: () => request('/profile'),

  register: ({ code, name }) => request('/register', { method: 'POST', body: { code, name } }),

  createNote: ({ content, moduleId = null, pageId = null }) =>
    request('/notes', { method: 'POST', body: { content, module_id: moduleId, page_id: pageId } }),

  myNotes: () => request('/notes/mine'),

  // Browsing: the whole tree, and one node with its children (and, for a page,
  // its text).
  nodes: () => request('/nodes'),

  node: (nodeId) => request(`/node?node_id=${encodeURIComponent(nodeId)}`),

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
