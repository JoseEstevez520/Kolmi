import { Extension } from '@tiptap/core'
import { PluginKey } from '@tiptap/pm/state'
import Suggestion from '@tiptap/suggestion'

export const slashKey = new PluginKey('slash')

// The "/" menu, Notion's way: typing "/" opens the blocks, what follows filters them, the
// arrows move and Enter picks. The extension only reports; the editor draws the menu from
// `state` (open, the blocks found, the one highlighted, where the "/" is) and the menu keys
// are handled here, so they never reach the text while it is open.
export const SlashMenu = Extension.create({
  name: 'slashMenu',

  addOptions() {
    return { state: null, find: () => [] }
  },

  addProseMirrorPlugins() {
    const { state, find } = this.options

    const pick = (index) => {
      const block = state.items[index]
      if (block) state.command?.(block)
    }

    return [
      Suggestion({
        editor: this.editor,
        pluginKey: slashKey,
        char: '/',
        // Not in code: a "/" there is a path or a comment, not a command.
        allow: ({ editor }) => !editor.isActive('codeBlock') && !editor.isActive('code'),
        items: ({ query, editor }) => find(query, editor.isActive('table')),
        command: ({ editor, range, props: block }) => {
          block.run(editor.chain().focus().deleteRange(range)).run()
        },
        render: () => {
          const sync = (props) => {
            state.items = props.items
            state.command = props.command
            state.rect = props.clientRect?.() ?? null
            if (state.index >= props.items.length) state.index = 0
          }
          return {
            onStart: (props) => {
              state.index = 0
              sync(props)
              state.open = true
            },
            onUpdate: sync,
            onExit: () => {
              state.open = false
              state.items = []
            },
            onKeyDown: ({ event }) => {
              // Escape is the plugin's own: it closes the menu and leaves the "/" as text.
              const count = state.items.length
              if (!count) return false
              if (event.key === 'ArrowDown') {
                state.index = (state.index + 1) % count
                return true
              }
              if (event.key === 'ArrowUp') {
                state.index = (state.index - 1 + count) % count
                return true
              }
              if (event.key === 'Enter' || event.key === 'Tab') {
                pick(state.index)
                return true
              }
              return false
            },
          }
        },
      }),
    ]
  },
})
