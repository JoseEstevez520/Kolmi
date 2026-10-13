import { h } from 'vue'
import { createParser } from '@openuidev/vue-lang'
import AnswerProposal from '../../components/AnswerProposal.vue'
import AnswerSources from '../../components/AnswerSources.vue'
import { buildLibrary, CHAT_ROOT } from './catalog.js'
import { renderers } from './library.js'

// The chat's catalogue drawn with the same renderers as the pages, plus its own root and the
// two parts that point at the app by id (Sources, Proposal). Loaded on demand (load-chat.js).
const declared = ['props', 'renderNode']
const renderer = (render) => ({ props: declared, setup: (p) => () => render(p.props ?? {}, p.renderNode) })

export const chatLibrary = buildLibrary(
  {
    ...renderers,
    // Not inside a Prose: an answer is a chat bubble's content, with the blocks' own spacing.
    Answer: renderer((props, renderNode) => h('div', { class: 'flex flex-col gap-3' }, renderNode(props.blocks ?? []))),
    Sources: renderer(({ ids }) => h(AnswerSources, { ids: Array.isArray(ids) ? ids : [] })),
    Proposal: renderer(({ id }) => (id != null ? h(AnswerProposal, { id }) : null)),
  },
  { chat: true },
)

const parser = createParser(chatLibrary.toJSONSchema(), CHAT_ROOT)

/** Whether `source` parses into an Answer root (the Markdown fallback when it does not). */
export function canRenderAnswer(source) {
  if (!source?.trim()) return false
  try {
    return parser.parse(source)?.root?.typeName === CHAT_ROOT
  } catch {
    return false
  }
}
