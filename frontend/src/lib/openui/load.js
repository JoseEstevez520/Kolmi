// The OpenUI page renderer, loaded on demand: the renderer, its parser and the page catalogue
// are heavy and only a page with an OpenUI source needs them, so they stay out of the main
// bundle. Loaded once and shared by every page.
let loading = null

export function loadPageRenderer() {
  loading ??= Promise.all([import('@openuidev/vue-lang'), import('./library.js')])
    .then(([lang, library]) => ({
      Renderer: lang.Renderer,
      pageLibrary: library.pageLibrary,
      canRender: library.canRender,
    }))
    .catch((error) => {
      // A failed chunk can be retried on the next page.
      loading = null
      throw error
    })
  return loading
}
