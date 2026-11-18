import { ref } from 'vue'
import { CodeBlock } from '@tiptap/extension-code-block'
import { VueNodeViewRenderer } from '@tiptap/vue-3'
import NoteCodeBlock from '../../components/NoteCodeBlock.vue'

// What the AI writes into a note lives in a code fence of its own language: in the Markdown the
// note is saved as, it is ```kolmi-ai and the OpenUI Lang program the chat writes. So the note
// stays plain Markdown (the pass, an export and an old client read it as a fence), and wherever
// the note is drawn the fence becomes the answer: here in the editor, and in Markdown through
// `components` (NoteAiFence).
export const AI_LANGUAGE = 'kolmi-ai'

// How many answers the AI is writing into the editor right now (their pieces arrive half
// written), so a piece isn't judged unreadable before its program ends.
export const aiWriting = ref(0)

export const AiCodeBlock = CodeBlock.extend({
  addAttributes() {
    return {
      ...this.parent?.(),
      // While the answer streams into it; never saved (the fence carries only the language).
      streaming: { default: false, rendered: false, keepOnSplit: false },
    }
  },

  addNodeView() {
    return VueNodeViewRenderer(NoteCodeBlock)
  },
})

/** The note's Markdown without what the AI wrote, as context for the next question. */
export function withoutAi(markdown) {
  return (markdown ?? '').replace(new RegExp('```' + AI_LANGUAGE + '[^\\n]*\\n[\\s\\S]*?```\\n?', 'g'), '').trim()
}
