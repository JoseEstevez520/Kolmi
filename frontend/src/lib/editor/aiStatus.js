import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'
import { inkFlow } from 'elastic-ui'

// While the AI writes into a note, one or several answers at once, each has a place: the blocks
// it is filling in (`from`..`to`). That place is marked (a thin line beside it that breathes) and
// kept out of the writer's way: what they type elsewhere goes on, but nothing typed lands inside
// it until the answer ends. Before anything arrives, a quiet line there says what it is doing
// ("Thinking…", "Looking for an image…"): a widget, never saved.
export const aiRegionsKey = new PluginKey('aiRegions')

// The wave of words coming into focus at the end of an answer being written: bands of this many
// characters, newest first.
const WAVE = ['ai-wave-3', 'ai-wave-2', 'ai-wave-1']
const WAVE_BAND = 14

// A transaction of the AI's own, which may change its places.
export const AI_OWN = 'aiOwn'

/** Set (or, with null, end) the place and status of answer `id`. */
export function setAiRegion(editor, id, region) {
  const tr = editor.state.tr.setMeta(aiRegionsKey, { id, region }).setMeta('addToHistory', false)
  editor.view.dispatch(tr)
}

// Every edit, the writer's or any answer's, moves the places after it: the start and the line
// between finished and arriving blocks stay before what is inserted at them, the end after it.
function mapRegion(region, mapping) {
  return {
    ...region,
    from: mapping.map(region.from, -1),
    mid: region.mid == null ? region.mid : mapping.map(region.mid, -1),
    to: mapping.map(region.to, 1),
  }
}

/** Move every place that starts at `pos` to start `by` later: a line put in at its edge (the
 * fresh line for the writer) is not part of it. */
export function shiftAiRegions(editor, pos, by) {
  const regions = aiRegionsKey.getState(editor.state) || {}
  for (const [id, r] of Object.entries(regions)) {
    if (r.from !== pos) continue
    const moved = { from: r.from + by, to: Math.max(r.to, r.from + by) }
    if (r.mid === pos) moved.mid = pos + by
    setAiRegion(editor, id, moved)
  }
}

/** Where answer `id` is now, or undefined. */
export function aiRegion(editor, id) {
  return aiRegionsKey.getState(editor.state)?.[id]
}

export const AiRegions = Extension.create({
  name: 'aiRegions',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: aiRegionsKey,
        state: {
          init: () => ({}),
          apply(tr, regions) {
            let next = regions
            if (tr.docChanged) {
              next = Object.fromEntries(Object.entries(regions).map(([id, r]) => [id, mapRegion(r, tr.mapping)]))
            }
            const meta = tr.getMeta(aiRegionsKey)
            if (meta) {
              next = { ...next }
              if (meta.region) next[meta.id] = { ...next[meta.id], ...meta.region }
              else delete next[meta.id]
            }
            return next
          },
        },
        // Nothing the writer types lands inside a place being filled.
        filterTransaction(tr, state) {
          if (!tr.docChanged || tr.getMeta(AI_OWN) || tr.getMeta('history$')) return true
          const regions = Object.values(aiRegionsKey.getState(state) || {})
          if (!regions.length) return true
          let inside = false
          for (const step of tr.steps) {
            step.getMap().forEach((start, end) => {
              for (const r of regions) {
                if (r.to <= r.from) continue
                if ((start < r.to && end > r.from) || (start === end && start > r.from && start < r.to)) inside = true
              }
            })
          }
          return !inside
        },
        props: {
          decorations(state) {
            const regions = Object.values(aiRegionsKey.getState(state) || {})
            if (!regions.length) return null
            const found = []
            for (const r of regions) {
              if (r.to > r.from) {
                state.doc.nodesBetween(r.from, r.to, (node, pos) => {
                  if (pos >= r.from && pos + node.nodeSize <= r.to) found.push(Decoration.node(pos, pos + node.nodeSize, { class: 'ai-writing' }))
                  return false
                })
              }
              // The words just arrived come into focus: the last characters of an answer still
              // being written fade from faint to full, in bands, a soft front that moves on as the
              // text arrives at its steady pace (as the chat's words do, each one blurring in).
              if (r.writing && r.to > r.from) {
                const texts = []
                state.doc.nodesBetween(r.from, r.to, (node, pos) => {
                  if (node.isText) texts.push([pos, pos + node.text.length])
                })
                let left = WAVE.length * WAVE_BAND
                let band = 0
                let inBand = 0
                for (let i = texts.length - 1; i >= 0 && left > 0; i--) {
                  let [a, b] = texts[i]
                  while (b > a && left > 0) {
                    const take = Math.min(b - a, WAVE_BAND - inBand)
                    // In ink, the band's hue drifts along the answer as the chat's words do.
                    const at = b - take - r.from
                    found.push(Decoration.inline(b - take, b, { class: WAVE[band], style: `--ink-flow: ${inkFlow(Math.floor(at / 6))}` }))
                    b -= take
                    left -= take
                    inBand += take
                    if (inBand >= WAVE_BAND) {
                      band++
                      inBand = 0
                    }
                  }
                }
              }
              if (r.status) {
                const text = r.status
                found.push(
                  Decoration.widget(
                    r.to,
                    () => {
                      const el = document.createElement('p')
                      el.className = 'ai-status text-shimmer'
                      el.textContent = text
                      el.setAttribute('aria-live', 'polite')
                      return el
                    },
                    { side: -1, key: `${text}` },
                  ),
                )
              }
            }
            return DecorationSet.create(state.doc, found)
          },
        },
      }),
    ]
  },
})
