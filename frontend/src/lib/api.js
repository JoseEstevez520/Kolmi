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

// A file comes back as the response's body: the same session header, the bytes kept as they are.
async function fetchFile(path) {
  const token = accessToken()
  let response
  try {
    response = await fetch(`${BASE_URL}${path}`, { headers: token ? { Authorization: `Bearer ${token}` } : {} })
  } catch {
    throw new ApiError(0, t('api.unreachable'))
  }
  if (!response.ok) {
    let detail = ''
    try {
      detail = (await response.json()).detail
    } catch {
      /* not JSON: the status text will do */
    }
    throw new ApiError(response.status, detail || response.statusText || t('api.failed'))
  }
  const named = /filename="([^"]+)"/.exec(response.headers.get('Content-Disposition') || '')
  return { blob: await response.blob(), name: named ? named[1] : 'kolmi.zip' }
}

// A file goes up as the request's body, with its progress reported as it goes (fetch has none).
function upload({ file, noteId = null, nodeId = null, onProgress }) {
  const query = new URLSearchParams({ name: file.name })
  if (noteId != null) query.set('note_id', noteId)
  if (nodeId != null) query.set('node_id', nodeId)
  const token = accessToken()

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', `${BASE_URL}/files/upload?${query}`)
    xhr.setRequestHeader('Content-Type', file.type || 'application/octet-stream')
    if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`)
    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable) onProgress?.(event.loaded / event.total)
    }
    xhr.onerror = () => reject(new ApiError(0, t('api.unreachable')))
    xhr.onload = () => {
      let data = null
      try {
        data = JSON.parse(xhr.responseText)
      } catch {
        // Not JSON: the status says enough.
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(data)
      else reject(new ApiError(xhr.status, (data && data.detail) || t('api.failed')))
    }
    xhr.send(file)
  })
}

export const api = {
  getProfile: () => request('/profile'),

  register: ({ code, name }) => request('/register', { method: 'POST', body: { code, name } }),

  // The class's people (admin): who they are, their role and whether they were let in. A change
  // answers with the updated row; one that would leave the class with no active admin is a 409.
  users: () => request('/users'),

  setUserRole: ({ userId, role }) =>
    request('/users/role', { method: 'POST', body: { user_id: userId, role } }),

  setUserStatus: ({ userId, status }) =>
    request('/users/status', { method: 'POST', body: { user_id: userId, status } }),

  deleteUser: ({ userId }) => request('/users/delete', { method: 'POST', body: { user_id: userId } }),

  // Your own account: it answers for anyone, whether let in or not, so a person who is waiting
  // (or blocked) can still leave. An admin who is the last one of the class gets a 409.
  deleteMyAccount: () => request('/profile/delete', { method: 'POST' }),

  createNote: ({ content, format = 'text', nodeId = null, forFiles = false, keepalive }) =>
    request('/notes', {
      method: 'POST',
      body: { content, format, node_id: nodeId, for_files: forFiles },
      keepalive,
    }),

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
  // in, the pass's schedule and the timetable's shape (days, hours, breaks). Anyone signed in
  // reads them; only an admin changes them.
  settings: () => request('/settings'),

  // Sends only what is given (JSON drops `undefined` keys), so one setting can change
  // without the rest.
  updateSettings: ({
    classLanguage,
    passEnabled,
    passTimes,
    passDays,
    scheduleEnabled,
    scheduleDays,
    scheduleStart,
    scheduleEnd,
    scheduleBreaks,
    scheduleSessionMinutes,
    chatEnabled,
    chatDailyLimit,
    signupsNeedApproval,
  }) =>
    request('/settings', {
      method: 'POST',
      body: {
        class_language: classLanguage,
        pass_enabled: passEnabled,
        pass_times: passTimes,
        pass_days: passDays,
        schedule_enabled: scheduleEnabled,
        schedule_days: scheduleDays,
        schedule_start: scheduleStart,
        schedule_end: scheduleEnd,
        schedule_breaks: scheduleBreaks,
        schedule_session_minutes: scheduleSessionMinutes,
        chat_enabled: chatEnabled,
        chat_daily_limit: chatDailyLimit,
        signups_need_approval: signupsNeedApproval,
      },
    }),

  // Admin: start the pass now. It answers at once, `started` or `already_running`.
  runPass: () => request('/pass/run', { method: 'POST' }),

  // Ask the hive a question; it answers from the class's own content, with the pages it used.
  askChat: (question) => request('/chat', { method: 'POST', body: { question } }),

  // The timetable's slots. Anyone signed in reads them; only an admin writes them.
  scheduleEvents: () => request('/schedule/events'),

  createScheduleEvent: ({ nodeId, day, startTime, endTime, title, detail, color }) => {
    const body = { node_id: nodeId, day, start_time: startTime, end_time: endTime }
    if (title !== undefined) body.title = title
    if (detail !== undefined) body.detail = detail
    if (color !== undefined) body.color = color
    return request('/schedule/events', { method: 'POST', body })
  },

  updateScheduleEvent: ({ eventId, ...patch }) =>
    request('/schedule/events/update', {
      method: 'POST',
      body: {
        event_id: eventId,
        node_id: patch.nodeId,
        day: patch.day,
        start_time: patch.startTime,
        end_time: patch.endTime,
        title: patch.title,
        detail: patch.detail,
        color: patch.color,
      },
    }),

  deleteScheduleEvent: ({ eventId }) =>
    request('/schedule/events/delete', { method: 'POST', body: { event_id: eventId } }),

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

  // A page's earlier versions (admin): a preview of each, newest first, and putting one back.
  pageVersions: (nodeId) => request(`/page/versions?node_id=${encodeURIComponent(nodeId)}`),

  restoreVersion: (versionId) =>
    request('/page/versions/restore', { method: 'POST', body: { version_id: versionId } }),

  // Files: on a page (admin) or on a note (its author). Upload and delete change them; a
  // download is a short-lived link, asked for at the click.
  uploadFile: upload,

  noteFiles: (noteId) => request(`/files?note_id=${encodeURIComponent(noteId)}`),

  deleteFile: (fileId) => request('/files/delete', { method: 'POST', body: { file_id: fileId } }),

  fileLink: (fileId) => request(`/files/download?file_id=${encodeURIComponent(fileId)}`),

  // The shared pages as a zip of Markdown files: all of them, or the ones under a section.
  exportPages: (nodeId = null) => fetchFile(nodeId == null ? '/export' : `/export?node_id=${encodeURIComponent(nodeId)}`),
}
