// The catalogue without renderers, for `openui generate` (it loads this file in Node, where
// elastic-ui's components cannot run). Only the names, schemas and descriptions reach the
// prompt, so a stub renderer is enough. Run `npm run page-prompt` after changing catalog.js.
import { buildLibrary, promptOptions } from './catalog.js'

const stub = { render: () => null }

export const library = buildLibrary(
  new Proxy({}, { get: () => stub }),
)

export { promptOptions }
