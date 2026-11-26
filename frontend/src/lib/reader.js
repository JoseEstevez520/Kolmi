import { api } from './api.js'
import { t } from './i18n.js'

// A reading request uses the same authenticated stream and quota as the chat, while acting on
// nothing. `onTextDone` marks the end of the text stream before any Artifact visual is built,
// and `fix` replaces a completed kolmi-ai fence in place once its piece is ready.
export async function streamReader(
  selection,
  context,
  { detail = false, nodeId = null, liveId = null, history = [], signal, onText, onTextDone },
) {
  let text = ''
  let done = false
  let error = ''
  await api.streamChat(
    selection,
    history,
    (event, data) => {
      if (signal?.aborted) return
      if (event === 'token') {
        text += data.text
        onText(text)
      }
      if (event === 'text_done') onTextDone?.()
      if (event === 'fix') {
        let index = -1
        text = text.replace(/```kolmi-ai[^\n]*\n[\s\S]*?```\n?/g, (fence) => {
          index++
          return index === data.index ? (data.program ? `\`\`\`kolmi-ai\n${data.program}\n\`\`\`\n` : '') : fence
        })
        onText(text)
      }
      if (event === 'done') done = true
      if (event === 'error') error = data.message
    },
    nodeId,
    liveId,
    { mode: detail ? 'reader_detail' : 'reader', note: context, signal },
  )
  if (signal?.aborted) return
  if (error || !done) throw new Error(error || t('reader.failed'))
  return text
}

export function readingContext(title, text, selection) {
  const at = text.indexOf(selection)
  const start = at < 0 ? 0 : Math.max(0, at - 2600)
  return `${title}\n\n${text.slice(start, start + 5600)}`.slice(0, 6000)
}
