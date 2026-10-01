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

  // Browsing: the module tree, one section with its pages, one page with its text.
  modules: () => request('/modules'),

  section: (sectionId) => request(`/section?section_id=${encodeURIComponent(sectionId)}`),

  page: (pageId) => request(`/page?page_id=${encodeURIComponent(pageId)}`),

  // Admin, modules.
  createModule: ({ name }) => request('/module', { method: 'POST', body: { name } }),

  renameModule: ({ moduleId, name }) =>
    request('/module/rename', { method: 'POST', body: { module_id: moduleId, name } }),

  reorderModules: ({ ids }) => request('/module/reorder', { method: 'POST', body: { ids } }),

  deleteModule: ({ moduleId }) =>
    request('/module/delete', { method: 'POST', body: { module_id: moduleId } }),

  // Admin, sections.
  createSection: ({ moduleId, name }) =>
    request('/section', { method: 'POST', body: { module_id: moduleId, name } }),

  renameSection: ({ sectionId, name }) =>
    request('/section/rename', { method: 'POST', body: { section_id: sectionId, name } }),

  reorderSections: ({ ids }) => request('/section/reorder', { method: 'POST', body: { ids } }),

  deleteSection: ({ sectionId }) =>
    request('/section/delete', { method: 'POST', body: { section_id: sectionId } }),

  // Admin, pages.
  createPage: ({ sectionId, title }) =>
    request('/page', { method: 'POST', body: { section_id: sectionId, title } }),

  renamePage: ({ pageId, title }) =>
    request('/page/rename', { method: 'POST', body: { page_id: pageId, title } }),

  reorderPages: ({ ids }) => request('/page/reorder', { method: 'POST', body: { ids } }),

  deletePage: ({ pageId }) =>
    request('/page/delete', { method: 'POST', body: { page_id: pageId } }),
}
