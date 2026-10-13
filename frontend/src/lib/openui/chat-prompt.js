// The chat catalogue without renderers, for the backend's prompt (the same way prompt.js serves
// the pages): `chatLibrary.prompt()` or `openui generate` can list the parts allowed in chat.
import { buildLibrary } from './catalog.js'

const stub = { render: () => null }

export const chatLibrary = buildLibrary(new Proxy({}, { get: () => stub }), { chat: true })
