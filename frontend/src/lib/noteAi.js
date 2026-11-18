import { api } from './api.js'

// The AI in a note, against the chat's stream (mode "note"): what it writes arrives as tokens;
// once it ends, a piece that wouldn't draw comes back mended (or dropped) as a `fix`. Resolves
// when the answer is done, rejects with the reason when it couldn't write.
export async function streamNoteAi(text, note, { onToken, onFix, liveId = null, failed = 'failed' }) {
  let error = false
  await api.streamChat(
    text,
    [],
    (name, data) => {
      if (name === 'token') onToken(data.text)
      if (name === 'fix') onFix?.(data.index, data.program)
      if (name === 'error') error = true
    },
    null,
    liveId,
    { mode: 'note', note },
  )
  if (error) throw new Error(failed)
}
