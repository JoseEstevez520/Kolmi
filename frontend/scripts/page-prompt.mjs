// Generates the web agent's system prompts from the page catalogue (src/lib/openui/catalog.js)
// and writes them into the backend, which cannot read the catalogue itself.
//
//   page.txt        the full prompt, for a model called directly (no Gateway)
//   page.spec.json  the serialized library spec
//   page.gateway.txt the `cloud: true` configuration block for the OpenUI Gateway, which
//                    assembles the prompt from it and validates and repairs the output
//
// Run with `npm run page-prompt` whenever the catalogue changes, and commit the output.
import { execFileSync } from 'node:child_process'
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'
import { generateSystemPrompt } from '@openuidev/lang-core'
import { promptOptions } from '../src/lib/openui/prompt-options.js'

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..')
const outDir = resolve(root, '../backend/app/agents/openui')
mkdirSync(outDir, { recursive: true })

execFileSync(
  'npx',
  [
    'openui',
    'generate',
    'src/lib/openui/prompt.js',
    '--no-interactive',
    '--export',
    'library',
    '--prompt-options',
    'promptOptions',
    '--out',
    resolve(outDir, 'page.txt'),
  ],
  { cwd: root, stdio: 'inherit', env: { ...process.env, OPENUI_TELEMETRY_DISABLED: '1' } },
)

const spec = JSON.parse(readFileSync(resolve(outDir, 'page.spec.json'), 'utf8'))
const gateway = generateSystemPrompt({ cloud: true, library: spec, promptOptions })
writeFileSync(resolve(outDir, 'page.gateway.txt'), gateway + '\n')
console.log(`Written Gateway prompt to ${resolve(outDir, 'page.gateway.txt')}`)
