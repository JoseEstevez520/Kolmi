import { api } from './api.js'

// What may be attached. The same limits as backend/app/files.py, which is the one that decides:
// this only lets the picker refuse a file before it goes up.
export const MAX_FILE_BYTES = 20 * 1024 * 1024
export const MAX_FILES_PER_NOTE = 5

const EXTENSIONS = [
  'zip',
  'pdf',
  'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'avif',
  'txt', 'md', 'markdown', 'rst', 'log',
  'json', 'csv', 'tsv', 'xml',
  'yml', 'yaml', 'toml', 'ini', 'cfg', 'conf', 'properties', 'gradle', 'lock', 'gitignore',
  'py', 'js', 'mjs', 'ts', 'jsx', 'tsx', 'vue', 'svelte', 'html', 'css', 'scss', 'java', 'kt',
  'c', 'h', 'cpp', 'hpp', 'cs', 'go', 'rs', 'rb', 'php', 'swift', 'sql', 'r', 'lua', 'dart', 'ipynb',
]
export const ACCEPT = EXTENSIONS.map((ext) => `.${ext}`).join(',')

// A file's size as people say it: 1.4 MB, 820 KB.
export function formatSize(bytes) {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  const i = Math.min(units.length - 1, Math.floor(Math.log(bytes) / Math.log(1024)) - 1)
  const value = bytes / 1024 ** (i + 1)
  return `${value < 10 ? value.toFixed(1) : Math.round(value)} ${units[i]}`
}

// The download link is short-lived and the request carries the session, so the link is asked
// for at the click and followed at once.
export async function downloadFile(fileId) {
  const { url } = await api.fileLink(fileId)
  const link = document.createElement('a')
  link.href = url
  link.rel = 'noopener'
  document.body.append(link)
  link.click()
  link.remove()
}
