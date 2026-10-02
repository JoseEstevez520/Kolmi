import { Extension } from '@tiptap/core'
import { Plugin, PluginKey } from '@tiptap/pm/state'
import { Decoration, DecorationSet } from '@tiptap/pm/view'

// What an empty block is, written faintly in it ("Heading", "Code", "Type / for blocks"), on
// the line being written and on the first line of an empty note. Tiptap's own Placeholder
// marks the block with a class, and the library's Prose only styles elements without one, so
// an empty heading would lose its size; this one sets a data attribute and nothing else.
export const BlockHint = Extension.create({
  name: 'blockHint',

  addOptions() {
    // (node, parent) → the hint for that empty block.
    return { text: () => '' }
  },

  addProseMirrorPlugins() {
    const { text } = this.options

    return [
      new Plugin({
        key: new PluginKey('blockHint'),
        props: {
          decorations: ({ doc, selection }) => {
            const first = doc.firstChild
            const emptyDoc = doc.childCount === 1 && first.isTextblock && first.content.size === 0
            const found = []

            doc.descendants((node, pos) => {
              if (!node.isTextblock) return true
              const here = selection.empty && selection.from > pos && selection.from < pos + node.nodeSize
              if (node.content.size === 0 && (here || emptyDoc)) {
                const attrs = { 'data-placeholder': text(node, doc.resolve(pos).parent) }
                if (emptyDoc) attrs['data-empty-doc'] = ''
                found.push(Decoration.node(pos, pos + node.nodeSize, attrs))
              }
              return false
            })

            return DecorationSet.create(doc, found)
          },
        },
      }),
    ]
  },
})
