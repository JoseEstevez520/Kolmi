// The chat's OpenUI renderer, loaded on demand like the page's (load.js): only an answer
// written in OpenUI Lang needs the parser and the catalogue.
let loading = null

export function loadChatRenderer() {
  loading ??= Promise.all([import('@openuidev/vue-lang'), import('./chat-library.js')])
    .then(([lang, library]) => ({
      Renderer: lang.Renderer,
      chatLibrary: library.chatLibrary,
      canRender: library.canRenderAnswer,
    }))
    .catch((error) => {
      loading = null
      throw error
    })
  return loading
}
