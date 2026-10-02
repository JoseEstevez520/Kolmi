// A note is one Markdown text. Its title, when it has one, is the first line as a `# ` heading,
// so the daily pass reads it like the rest and the table needs no column for it.
const TITLE = /^# +(.+)\n*/

export function splitNote(content = '') {
  const match = content.match(TITLE)
  return match
    ? { title: match[1].trim(), body: content.slice(match[0].length) }
    : { title: '', body: content }
}

export function joinNote(title, body) {
  const head = title.trim()
  const rest = body.trim()
  if (!head) return rest
  return rest ? `# ${head}\n\n${rest}` : `# ${head}`
}

// A draft lives in this browser until it is sent, so closing the tab at the end of a class
// loses nothing. One per note: `new` for the one being started, the id for one being edited.
const draftKey = (id) => `kolmi.draft.${id ?? 'new'}`

export function loadDraft(id) {
  try {
    const saved = localStorage.getItem(draftKey(id))
    return saved ? JSON.parse(saved) : null
  } catch {
    return null
  }
}

export function saveDraft(id, draft) {
  try {
    localStorage.setItem(draftKey(id), JSON.stringify(draft))
    return true
  } catch {
    // Private mode or blocked storage: the note is still on screen, just not kept.
    return false
  }
}

export function clearDraft(id) {
  try {
    localStorage.removeItem(draftKey(id))
  } catch {
    // Nothing kept, nothing to clear.
  }
}

// A note's text without its marks, for a card's preview: the card is a link, so it shows
// words, not the note's own links and code blocks.
export function plainText(markdown = '') {
  return markdown
    .replace(/^```.*$/gm, '')
    .replace(/^\s{0,3}(#{1,6}|[-*+]|\d+[.)]|>)\s+/gm, '')
    .replace(/(\*\*|__|\*|_|~~|`)(.+?)\1/g, '$2')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\n{3,}/g, '\n\n')
    .trim()
}
