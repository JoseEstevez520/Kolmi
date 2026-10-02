import { Extension } from '@tiptap/core'
import { PluginKey } from '@tiptap/pm/state'
import Suggestion from '@tiptap/suggestion'

export const slashKey = new PluginKey('slash')

// The "/" menu, Notion's way: typing "/" opens the blocks, what follows filters them, the
// arrows move and Enter picks. The extension only reports what the menu should show (`state`:
// open, the blocks found, where the "/" is, the command that applies one) and hands the menu
// keys to elastic-ui's SuggestionMenu (`keys`), so they never reach the text while it is open.
export const SlashMenu = Extension.create({
  name: 'slashMenu',

  addOptions() {
    return { state: null, find: () => [], keys: null }
  },

  addProseMirrorPlugins() {
    const { state, find, keys } = this.options

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
          }
          return {
            onStart: (props) => {
              sync(props)
              state.open = true
            },
            onUpdate: sync,
            onExit: () => {
              state.open = false
              state.items = []
            },
            // Escape is the plugin's own: it closes the menu and leaves the "/" as text.
            onKeyDown: ({ event }) => {
              if (event.key === 'ArrowDown') return keys.next(), true
              if (event.key === 'ArrowUp') return keys.previous(), true
              if (event.key === 'Enter' || event.key === 'Tab') return keys.pick()
              return false
            },
          }
        },
      }),
    ]
  },
})
