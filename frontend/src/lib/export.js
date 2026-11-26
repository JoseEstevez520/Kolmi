import { api } from './api.js'

// The class's shared pages as Markdown files in a zip, kept on this device. The request carries
// the session, so the file is fetched here and handed to the browser instead of linked to.
export async function downloadExport(nodeId = null, ownNotes = false) {
  const { blob, name } = await (ownNotes ? api.exportNotes() : api.exportPages(nodeId))
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = name
  document.body.append(link)
  link.click()
  link.remove()
  setTimeout(() => URL.revokeObjectURL(url), 10_000)
}
