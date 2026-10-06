// The clients Kolmi's MCP can be connected to, and the exact text that connects each one. Adding a
// client is one entry in CLI_CLIENTS, or a builder below for the editors with their own config.
// Every format comes from the client's own documentation (the source is on each entry); none is
// guessed.
import { BASE_URL } from './api.js'

// The instance's MCP address: the API's base plus /mcp, made absolute when the base is relative.
export function mcpUrl() {
  return new URL(`${BASE_URL.replace(/\/+$/, '')}/mcp`, window.location.origin).href
}

export const authHeader = (token) => `Authorization: Bearer ${token}`

// A command line, with `lines` the text to copy. `note` and `name` are i18n keys under
// settings.connect.clients.<id>.
export const CLI_CLIENTS = [
  {
    id: 'claude',
    // https://code.claude.com/docs/en/mcp
    lines: ({ url, token }) => [
      `claude mcp add --transport http kolmi ${url} --header "${authHeader(token)}"`,
    ],
  },
  {
    id: 'gemini',
    // https://github.com/google-gemini/gemini-cli/blob/main/docs/tools/mcp-server.md
    lines: ({ url, token }) => [
      `gemini mcp add --transport http --header "${authHeader(token)}" kolmi ${url}`,
    ],
  },
  {
    id: 'codex',
    // https://github.com/openai/codex/blob/main/codex-rs/cli/src/mcp_cmd.rs: it only takes the
    // token from an environment variable.
    lines: ({ url, token }) => [
      `export KOLMI_TOKEN=${token}`,
      `codex mcp add kolmi --url ${url} --bearer-token-env-var KOLMI_TOKEN`,
    ],
  },
]

// The shape of Claude Code's .mcp.json (https://code.claude.com/docs/en/mcp), which other
// clients read too.
export function mcpServersJson({ url, token }) {
  return JSON.stringify(
    { mcpServers: { kolmi: { type: 'http', url, headers: { Authorization: `Bearer ${token}` } } } },
    null,
    2,
  )
}

// Cursor's install link takes the server's config, base64-encoded:
// https://cursor.com/docs/plugins/mcp/install-links. Its mcp.json takes `url` and `headers` for a
// remote server.
export function cursorConfig({ url, token }) {
  return JSON.stringify({ url, headers: { Authorization: `Bearer ${token}` } }, null, 2)
}

export function cursorLink({ url, token }) {
  const compact = JSON.stringify({ url, headers: { Authorization: `Bearer ${token}` } })
  // btoa only takes Latin-1, so go through UTF-8 bytes.
  const bytes = new TextEncoder().encode(compact)
  const config = btoa(Array.from(bytes, (b) => String.fromCharCode(b)).join(''))
  return `cursor://anysphere.cursor-deeplink/mcp/install?name=kolmi&config=${config}`
}

// VS Code's .vscode/mcp.json for a remote server (https://code.visualstudio.com/docs/agents/reference/mcp-configuration).
// The token is not in the file: VS Code asks for it through an input when it starts the server.
export function vscodeJson({ url }) {
  return JSON.stringify(
    {
      inputs: [{ type: 'promptString', id: 'kolmi-token', description: 'Kolmi token', password: true }],
      servers: { kolmi: { type: 'http', url, headers: { Authorization: 'Bearer ${input:kolmi-token}' } } },
    },
    null,
    2,
  )
}

// Windsurf's mcp_config.json for a remote server, `serverUrl` and `headers`
// (https://docs.windsurf.com/windsurf/cascade/mcp, which now redirects to
// https://docs.devin.ai/desktop/cascade/mcp).
export function windsurfJson({ url, token }) {
  return JSON.stringify(
    { mcpServers: { kolmi: { serverUrl: url, headers: { Authorization: `Bearer ${token}` } } } },
    null,
    2,
  )
}
