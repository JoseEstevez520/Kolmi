import { api } from './api.js'

// The AI in a note, against the chat's stream (mode "note"): what it writes arrives as tokens;
// once it ends, a piece that wouldn't draw comes back mended (or dropped) as a `fix`. Resolves
// when the answer is done, rejects with the reason when it couldn't write. `onStatus` hears what
// it is doing while nothing arrives (thinking, looking for an image).
export async function streamNoteAi(text, note, { onToken, onFix, onStatus, signal, nodeId = null, liveId = null, failed = 'failed' }) {
  let error = false
  await api.streamChat(
    text,
    [],
    (name, data) => {
      if (name === 'token') onToken(data.text)
      if (name === 'fix') onFix?.(data.index, data.program)
      if (name === 'text_done') onStatus?.('', 'text_done')
      if (name === 'status') onStatus?.(data.text)
      if (name === 'error') error = true
    },
    nodeId,
    liveId,
    { mode: 'note', note, signal },
  )
  if (error) throw new Error(failed)
}
