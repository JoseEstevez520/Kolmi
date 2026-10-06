// The clients Kolmi's MCP can be connected to, and the exact text that connects each one. Adding a
// client is one entry in CLI_CLIENTS. Every format comes from the client's own documentation
// (the source is on each entry); none is guessed. Editors with their own config or install link
// are left out until their docs are checked.
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
