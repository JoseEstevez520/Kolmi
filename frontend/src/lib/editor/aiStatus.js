import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

// What the AI is doing while nothing has arrived yet ("Thinking…", "Looking for an image…"),
// shown in the note where its answer will go: a widget, not text, so it is never saved.
export const aiStatusKey = new PluginKey('aiStatus')

/** Show `text` at `pos`, or clear it with null. */
export function setAiStatus(editor, status) {
  editor.view.dispatch(editor.state.tr.setMeta(aiStatusKey, status).setMeta('addToHistory', false))
}

export const AiStatus = Extension.create({
  name: 'aiStatus',

  addProseMirrorPlugins() {
    return [
      new Plugin({
        key: aiStatusKey,
        state: {
          init: () => null,
          apply(tr, status) {
            const next = tr.getMeta(aiStatusKey)
            if (next !== undefined) return next
            return status && { ...status, pos: tr.mapping.map(status.pos, 1) }
          },
        },
        props: {
          decorations(state) {
            const status = aiStatusKey.getState(state)
            if (!status) return null
            const widget = () => {
              const el = document.createElement('p')
              el.className = 'ai-status text-shimmer'
              el.textContent = status.text
              el.setAttribute('aria-live', 'polite')
              return el
            }
            return DecorationSet.create(state.doc, [Decoration.widget(status.pos, widget, { side: 1, key: status.text })])
          },
        },
      }),
    ]
  },
})
