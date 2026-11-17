import { Extension, textInputRule } from '@tiptap/core'
import { Plugin } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

// Arrows in the note's text: "->" typed turns into →, and every → is drawn as the library's
// arrow icon (elastic-ui's inline-arrow), as Markdown draws it on a page. The character stays in
// the note; only how it looks changes.
function decorate(doc) {
  const found = []
  doc.descendants((node, pos) => {
    if (!node.isText) return
    for (let i = node.text.indexOf('→'); i >= 0; i = node.text.indexOf('→', i + 1)) {
      found.push(Decoration.inline(pos + i, pos + i + 1, { class: 'inline-arrow' }))
    }
  })
  return DecorationSet.create(doc, found)
}

export const Arrows = Extension.create({
  name: 'arrows',

  addInputRules() {
    return [textInputRule({ find: /->$/, replace: '→' })]
  },

  addProseMirrorPlugins() {
    return [
      new Plugin({
        state: {
          init: (_, { doc }) => decorate(doc),
          apply: (tr, set) => (tr.docChanged ? decorate(tr.doc) : set),
        },
        props: {
          decorations(state) {
            return this.getState(state)
          },
        },
      }),
    ]
  },
})
