import { ref } from 'vue'
import { open } from './chat.js'

// The chat is one box in two sizes (elastic-ui's ChatMorph): the small one at the corner and the
// wide one over the page. `/chat` is only a way to open it wide, so a link or a bookmark works.
export const chatSize = ref('default')

export function openChatWide() {
  chatSize.value = 'wide'
  open.value = true
}
